"""The web app executes the frozen pipeline and persists review transactions."""
import json
import shutil
import threading
from concurrent.futures import ThreadPoolExecutor
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from pathlib import Path

import pandas as pd
import pytest

from src.web_app import Conflict, ROOT, Workspace, handler_for
from src.web_worker import current_revision


@pytest.fixture(scope='module')
def ranked_base(tmp_path_factory):
    workspace = Workspace(tmp_path_factory.mktemp('web-base'))
    state = workspace.create()
    for step in ('load', 'process', 'rank'):
        state = workspace.stage(state['run_id'], step, {'revision': state['revision']})
    return workspace, state


@pytest.fixture
def ranked(ranked_base, tmp_path):
    base, state = ranked_base
    workspace = Workspace(tmp_path / 'web')
    shutil.copytree(base.run_dir(state['run_id']), workspace.output / state['run_id'])
    return workspace, workspace.snapshot(state['run_id'])


def submit(state, confirmed=False):
    return {'revision': state['revision'], 'reviewer': 'Người kiểm thử', 'human_confirmed': confirmed,
            'rows': [{'item_id': row['item_id'], 'reviewer_decision': 'approve',
                      'override_value': '', 'review_note': 'Kiểm thử luồng lưu review.'} for row in state['queue']]}


def stage(workspace, state, name, **payload):
    return workspace.stage(state['run_id'], name, {'revision': state['revision'], **payload})


def test_real_pixel_stages_preserve_frozen_scores_and_imported_confirmation(ranked):
    workspace, state = ranked
    assert len(state['images']) == len(state['features']) == 96
    assert state['stats']['review_pool'] == 40 and len(state['queue']) == 20
    assert not state['human_confirmed'] and not state['reviews']
    raw = workspace.artifact(state['run_id'], 'raw_predictions.csv').read_bytes()
    assert raw == (ROOT / 'reports/evidence/poc/raw_predictions.csv').read_bytes()
    state = stage(workspace, state, 'review', source='confirmed')
    assert state['stats']['n_human_reviewed'] == 20
    actions = [r['override_value'] or r['suggested_action'] for r in state['reviews']]
    assert actions.count('RECAPTURE') == 19 and actions.count('KEEP') == 1
    assert {r['reviewer'] for r in state['reviews']} == {'Vũ Duy Khanh'}
    assert {r['item_id'] for r in state['reviews'] if r['override_value']} == {'img_19_2', 'img_06_3'}
    state = stage(workspace, state, 'decide')
    assert state['decision']['status'] == 'REWORK'
    assert state['decision']['reason_code'] == 'QUALITY_RECAPTURE_REQUIRED'
    assert workspace.artifact(state['run_id'], 'raw_predictions.csv').read_bytes() == raw
    receipt = json.loads(workspace.artifact(state['run_id'], 'review_confirmation.json').read_text())
    assert receipt['confirmed_at'] == json.loads((ROOT/'reports/human_review_confirmation.json').read_text())['confirmed_at']
    state = stage(workspace, state, 'review', source='confirmed')
    assert len([e for e in state['audit'] if e['action'].startswith('review:')]) == 20
    assert not state['steps']['decide']['done'] and state['decision'] is None


def test_real_override_audit_restart_and_decision_invalidation(ranked):
    workspace, state = ranked
    payload = submit(state, confirmed=True)
    payload['rows'][0].update(reviewer_decision='edit', override_value='KEEP', review_note='Mẫu kiểm thử vẫn đủ nét.')
    state = workspace.stage(state['run_id'], 'review', payload)
    state = stage(workspace, state, 'decide')
    _, previous = current_revision(workspace.run_dir(state['run_id']))
    old_decision = (previous / 'decision.json').read_bytes()
    old_audit = (previous / 'audit_log.jsonl').read_bytes()
    final = pd.read_csv(workspace.artifact(state['run_id'], 'ranked_review.csv'))
    assert final.loc[final.image_id == payload['rows'][0]['item_id'], 'pred_action'].item() == 'KEEP'
    payload['revision'] = state['revision']
    state = workspace.stage(state['run_id'], 'review', payload)
    assert state['decision'] is None and 'decision.json' not in state['downloads']
    assert (previous / 'decision.json').read_bytes() == old_decision
    assert workspace.artifact(state['run_id'], 'audit_log.jsonl').read_bytes().startswith(old_audit)
    assert len([e for e in state['audit'] if e['action'].startswith('review:')]) == 20
    restarted = Workspace(workspace.output, input_dir=Path('/nonexistent'))
    assert restarted.snapshot(state['run_id']) == state
    assert restarted.image(state['run_id'], state['queue'][0]['item_id']).is_file()
    assert restarted.listing()[0]['run_id'] == state['run_id']


@pytest.mark.parametrize('mode,code,human', [
    ('unconfirmed', 'HUMAN_REVIEW_REQUIRED', 0),
    ('partial', 'HUMAN_REVIEW_REQUIRED', 19),
    ('escalate', 'REVIEW_ESCALATED', 19),
    ('skip', 'HUMAN_REVIEW_REQUIRED', 19),
])
def test_review_gates_never_inherit_global_confirmation(ranked, mode, code, human):
    workspace, state = ranked
    payload = submit(state, confirmed=mode != 'unconfirmed')
    if mode != 'unconfirmed':
        payload['rows'][0]['reviewer_decision'] = '' if mode == 'partial' else mode
    state = workspace.stage(state['run_id'], 'review', payload)
    state = stage(workspace, state, 'decide')
    assert state['stats']['n_human_reviewed'] == human
    assert state['decision']['status'] == 'HOLD' and state['decision']['reason_code'] == code


@pytest.mark.parametrize('bad', ['missing', 'duplicate', 'foreign', 'score', 'unknown', 'override', 'note',
                                  'unneeded_override', 'reviewer', 'type', 'confirmation_type'])
def test_rejected_review_is_transactional(ranked, bad):
    workspace, state = ranked
    payload = submit(state)
    row = payload['rows'][0]
    if bad == 'missing': payload['rows'].pop()
    if bad == 'duplicate': payload['rows'][1]['item_id'] = row['item_id']
    if bad == 'foreign': row['item_id'] = 'foreign'
    if bad == 'score': row['score'] = '0'
    if bad == 'unknown': row['reviewer_decision'] = 'delete'
    if bad == 'override': row.update(reviewer_decision='edit', override_value='DELETE')
    if bad == 'note': row.update(reviewer_decision='edit', override_value='KEEP', review_note=' ')
    if bad == 'unneeded_override': row['override_value'] = 'KEEP'
    if bad == 'reviewer': payload['reviewer'] = ' '
    if bad == 'type': row['review_note'] = 42
    if bad == 'confirmation_type': payload['human_confirmed'] = 'true'
    with pytest.raises(ValueError): workspace.stage(state['run_id'], 'review', payload)
    assert workspace.snapshot(state['run_id']) == state
    assert not list(workspace.run_dir(state['run_id']).glob('.stage-*'))


def test_wrong_step_and_stale_revision_do_not_publish(ranked):
    workspace, state = ranked
    for step_name in ('load', 'process', 'rank', 'decide'):
        with pytest.raises(ValueError): stage(workspace, state, step_name)
    for value in (0, True, '3', None):
        with pytest.raises(Conflict): workspace.stage(state['run_id'], 'review', submit(state) | {'revision': value})
    assert workspace.snapshot(state['run_id']) == state
    empty = workspace.create()
    assert not empty['human_confirmed']
    with pytest.raises(ValueError, match='Load'):
        stage(workspace, empty, 'process')


def test_input_changed_after_load_is_rejected(tmp_path):
    source = tmp_path / 'input'
    shutil.copytree(ROOT/'fixtures/t02_raw_qc', source, ignore=shutil.ignore_patterns('gt'))
    workspace = Workspace(tmp_path/'web', source)
    state = stage(workspace, workspace.create(), 'load')
    (source/'images/img_00_0.jpg').write_bytes(b'changed after load')
    with pytest.raises(ValueError, match='đã đổi'):
        stage(workspace, state, 'process')
    assert workspace.snapshot(state['run_id']) == state


def test_confirmation_for_different_queue_is_rejected(ranked):
    workspace, state = ranked
    path = workspace.artifact(state['run_id'], 'review_queue.csv')
    queue = pd.read_csv(path, keep_default_na=False)
    queue.loc[0, 'score'] = 0.123456
    queue.to_csv(path, index=False)
    with pytest.raises(ValueError, match='không thuộc queue'):
        stage(workspace, state, 'review', source='confirmed')
    assert not workspace.snapshot(state['run_id'])['steps']['review']['done']


def test_clearing_a_saved_review_is_audited_and_returns_to_hold(ranked):
    workspace, state = ranked
    state = workspace.stage(state['run_id'], 'review', submit(state, confirmed=True))
    payload = submit(state, confirmed=True)
    payload['rows'][0]['reviewer_decision'] = ''
    state = workspace.stage(state['run_id'], 'review', payload)
    cleared = [e for e in state['audit'] if e['action'] == 'review:clear']
    assert len(cleared) == 1 and cleared[0]['item_id'] == payload['rows'][0]['item_id']
    assert cleared[0]['after'] == 'unreviewed'
    state = stage(workspace, state, 'decide')
    assert state['decision']['reason_code'] == 'HUMAN_REVIEW_REQUIRED'


def test_numeric_looking_notes_survive_csv_and_server_restart(ranked):
    workspace, state = ranked
    payload=submit(state)
    payload['reviewer']='00123'
    for row in payload['rows']:row['review_note']='000456'
    state=workspace.stage(state['run_id'],'review',payload)
    assert {r['review_note'] for r in state['reviews']}=={'000456'}
    assert {r['reviewer'] for r in state['reviews']}=={'00123'}
    assert Workspace(workspace.output).snapshot(state['run_id'])==state


def test_interrupted_publication_can_continue_without_overwriting_orphan(ranked):
    workspace, state = ranked
    orphan = workspace.run_dir(state['run_id'])/'revisions/000004'
    orphan.mkdir(); (orphan/'marker').write_text('interrupted')
    state = workspace.stage(state['run_id'], 'review', submit(state))
    assert state['revision'] == 5 and (orphan/'marker').read_text() == 'interrupted'


def test_concurrent_writes_one_wins_and_one_conflicts(ranked):
    workspace, state = ranked
    def save():
        try: return workspace.stage(state['run_id'], 'review', submit(state))['revision']
        except Conflict: return 'conflict'
    with ThreadPoolExecutor(2) as pool:
        results = list(pool.map(lambda _: save(), range(2)))
    assert results.count(4) == results.count('conflict') == 1


def test_http_routes_access_boundaries_and_downloads(ranked):
    workspace, state = ranked
    server = ThreadingHTTPServer(('127.0.0.1', 0), handler_for(workspace))
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    port = server.server_port
    def request(path, method='GET', body=None, headers=None):
        client = HTTPConnection('127.0.0.1', port)
        client.request(method, path, json.dumps(body) if body is not None else None, headers=headers or {})
        response = client.getresponse(); data = response.read(); status = response.status
        client.close(); return status, data
    try:
        assert request('/')[0] == request('/app.js')[0] == request('/app.css')[0] == 200
        status, data = request('/api/runs')
        assert status == 200 and json.loads(data)[0]['run_id'] == state['run_id']
        endpoint = '/api/runs/' + state['run_id']
        assert request(endpoint)[0] == 200
        assert request(endpoint+'/images/'+state['queue'][0]['item_id'])[0] == 200
        assert request(endpoint+'/files/raw_predictions.csv')[1] == workspace.artifact(state['run_id'], 'raw_predictions.csv').read_bytes()
        for path in (endpoint+'/files/config.json', endpoint+'/files/%2e%2e/config.json', '/../../configs/lab.yaml', '/api/runs/nope', endpoint+'/images/foreign'):
            assert request(path)[0] == 404
        assert request('/', headers={'Host': 'evil.example'})[0] == 403
        headers = {'Content-Type': 'application/json', 'X-QC-Request': 'workspace'}
        assert request('/api/runs', 'POST', {}, {'Content-Type': 'application/json'})[0] == 403
        assert request('/api/runs', 'POST', {}, headers | {'Origin': 'http://evil.example'})[0] == 403
        assert request('/api/runs', 'POST', [], headers)[0] == 400
        status, body = request('/api/runs', 'POST', {}, headers | {'Origin': f'http://127.0.0.1:{port}'})
        assert status == 201 and not json.loads(body)['human_confirmed']
        assert request(endpoint+'/steps/review', 'POST', submit(state) | {'revision': 1}, headers)[0] == 409
        status, body = request(endpoint+'/steps/review', 'POST', submit(state), headers)
        assert status == 200 and json.loads(body)['stats']['n_reviewed'] == 20
    finally:
        server.shutdown(); server.server_close(); thread.join()
