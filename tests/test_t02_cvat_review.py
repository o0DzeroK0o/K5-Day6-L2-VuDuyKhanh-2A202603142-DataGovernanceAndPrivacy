"""CVAT review must flow through the real pipeline without changing scores."""
import json
import shutil
from pathlib import Path

import pytest

from tools import t02_cvat_review as importer
from tools.t02_cvat_demo import rows, verify
from tools.t02_fill_report import build_report, validate_structure, TEMPLATE


def test_imported_review_matches_all_cvat_notes_actions_and_operator():
    evidence = verify()
    entries = importer.review_rows(evidence)
    assert len(entries) == 20
    assert [r['review_note'] for r in entries] == [f['review_note'] for f in evidence['frames']]
    assert [r['item_id'] for r in entries if r['reviewer_decision'] == 'edit'] == ['img_19_2', 'img_06_3']
    assert {r['reviewer'] for r in entries} == {'AI:Codex'}
    assert all('AI' not in r['review_note'] for r in entries)
    receipt = importer.verify_import()
    assert receipt['status'] == 'HOLD'
    assert receipt['human_review_confirmed'] is False
    assert receipt['review_source'] == 'Vũ Duy Khanh'


def test_export_refuses_existing_human_review_without_touching_it(tmp_path):
    output = tmp_path / 'review.csv'
    entries = importer.review_rows(verify())
    entries[0]['reviewer'] = 'Vũ Duy Khanh'
    output.write_text(importer.csv_text(entries))
    before = output.read_bytes()
    with pytest.raises(ValueError, match='human work'):
        importer.export_review(output)
    assert output.read_bytes() == before


def test_export_backs_up_prior_ai_review_and_is_idempotent(tmp_path):
    output = tmp_path / 'review.csv'
    entries = importer.review_rows(verify())
    entries[0]['review_note'] = 'Previous observation'
    output.write_text(importer.csv_text(entries))
    before = output.read_bytes()
    importer.export_review(output)
    backups = list((tmp_path / 'review_history').glob('*.csv'))
    assert len(backups) == 1 and backups[0].read_bytes() == before
    after = output.read_bytes()
    importer.export_review(output)
    assert output.read_bytes() == after
    assert len(list((tmp_path / 'review_history').glob('*.csv'))) == 1


@pytest.fixture
def run_copy(tmp_path):
    target = tmp_path / 'poc'
    shutil.copytree('reports/evidence/poc', target)
    return target


@pytest.mark.parametrize('filename,column,value', [
    ('review_queue_reviewed.csv', 'review_note', 'Not the saved CVAT observation'),
    ('ranked_review.csv', 'score', '0'),
    ('item_decisions.csv', 'pred_action', 'KEEP'),
])
def test_modified_notes_scores_or_actions_fail(run_copy, filename, column, value):
    import csv
    path = run_copy / filename
    entries = rows(path)
    entries[0][column] = value
    with path.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, entries[0].keys())
        writer.writeheader()
        writer.writerows(entries)
    with pytest.raises(ValueError):
        importer.check_run(run_copy, verify())


def test_missing_current_review_audit_fails(run_copy):
    path = run_copy / 'audit_log.jsonl'
    lines = path.read_text().splitlines()
    path.write_text('\n'.join(lines[:-1]) + '\n')
    with pytest.raises(ValueError, match='audit'):
        importer.check_run(run_copy, verify())


def test_audit_must_record_the_actual_final_action(run_copy):
    path = run_copy / 'audit_log.jsonl'
    events = [json.loads(line) for line in path.read_text().splitlines()]
    events[-1]['after'] = 'KEEP'
    path.write_text(''.join(json.dumps(event) + '\n' for event in events))
    with pytest.raises(ValueError, match='audit'):
        importer.check_run(run_copy, verify())


def test_sync_rejects_truncated_prior_audit_history(run_copy):
    path = run_copy / 'audit_log.jsonl'
    lines = path.read_text().splitlines()
    path.write_text('\n'.join(lines[1:]) + '\n')
    with pytest.raises(ValueError, match='append-only history'):
        importer.sync_report(run_copy)


def test_false_human_signoff_in_pipeline_is_rejected(run_copy):
    path = run_copy / 'decision.json'
    data = json.loads(path.read_text())
    data['status'] = 'GO'
    data['metrics']['n_human_reviewed'] = 20
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match='sign-off'):
        importer.check_run(run_copy, verify())


def test_report_keeps_template_and_reflects_cvat_import():
    generated = build_report()
    validate_structure(TEMPLATE.read_text(), generated)
    assert 'Vũ Duy Khánh' not in generated
    assert 'Vũ Duy Khanh' in generated
    assert '20/20 quyết định từ CVAT' in generated
    assert '19 RECAPTURE / 1 KEEP' in generated
    assert 'cvat_review_import.json' in generated
    assert 'n_human_reviewed=20' in generated and 'human_review_confirmation.json' in generated
