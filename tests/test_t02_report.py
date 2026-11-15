from pathlib import Path
import json
import re
import shutil
import subprocess

import pytest

from tools.t02_fill_report import TEMPLATE, build_report, validate_structure
from tools.t02_artifacts import main as build_artifacts


def test_report_only_fills_answers_without_changing_template():
    original=TEMPLATE.read_text();filled=build_report()
    validate_structure(original,filled)
    assert [s for s in original.splitlines() if s.startswith('#')]==[s for s in filled.splitlines() if s.startswith('#')]
    assert '____' not in filled
    assert '- [x] Có baseline/PoC metrics, ≥1 failure case, reviewer evidence, decision log.' in filled
    assert '- [ ] Link repo và tag cuối cùng trong README; input mẫu không chứa PII thật.' in filled
    audit=json.loads(Path('reports/verification.json').read_text())['submission_audit']
    assert all(f'`{commit}`' in filled for commit in audit['tag_commits'].values())
    assert 'xác nhận đã trực tiếp review đủ 20 frame' in filled
    header=filled.split('## 01')[0]
    assert 'bản hiện hành dùng nhánh `main`' in header and 'chưa push' not in header
    decision = next(line for line in filled.splitlines() if line.startswith('- Decision policy'))
    assert 'REWORK / QUALITY_RECAPTURE_REQUIRED' in decision
    assert 'n_human_reviewed=20' in decision and 'human_review_confirmed=true' in decision
    assert filled.count('| Member')==6


def test_saved_report_matches_generator():
    assert Path('reports/group_report.md').read_text()==build_report()


def test_report_reproduction_runs_offline_without_overwriting_saved_metrics(tmp_path):
    """Execute the documented commands in isolation, including venv activation."""
    root=Path.cwd()
    for name in ('.venv', 'src', 'configs', 'fixtures'):
        (tmp_path/name).symlink_to(root/name, target_is_directory=True)
    (tmp_path/'reports').mkdir()
    shutil.copytree(root/'reports/annotations', tmp_path/'reports/annotations')
    saved=(root/'reports/metrics_poc.json').read_bytes()
    (tmp_path/'reports/metrics_poc.json').write_bytes(saved)
    commands=re.search(r'```bash\n(.*?)\n```', build_report(), re.DOTALL).group(1).splitlines()
    # Dependencies are already installed; do not install or nest pytest in a test.
    result=subprocess.run(['bash', '-e', '-c', '\n'.join(commands[1:-1])],
                          cwd=tmp_path, capture_output=True, text=True, timeout=30)
    assert result.returncode==0, result.stdout+result.stderr
    assert (tmp_path/'reports/metrics_poc.json').read_bytes()==saved
    output=tmp_path/'out/report-reproduce'
    metrics=json.loads((output/'metrics_poc_internal.json').read_text())
    assert metrics['metrics']==json.loads(saved)['metrics']
    decision=json.loads((output/'poc/decision.json').read_text())
    assert decision['status']=='HOLD'
    assert decision['reason_code']=='HUMAN_REVIEW_REQUIRED'
    assert (output/'poc/raw_predictions.csv').read_bytes()==(root/'reports/evidence/poc/raw_predictions.csv').read_bytes()


def test_report_structure_rejects_reworded_question_or_removed_member_row():
    filled=build_report()
    for bad in [filled.replace('Điểm nghẽn cụ thể:','Bài toán:',1),
                '\n'.join(s for s in filled.splitlines() if not s.startswith('| Member 2 |'))+'\n']:
        with pytest.raises(ValueError):validate_structure(TEMPLATE.read_text(),bad)


def test_demo_contains_five_offline_pages_and_real_evidence():
    text=Path('demo/t004_demo.html').read_text()
    assert len(re.findall(r'<section id="s\d+">',text))==5
    assert 'data:image/jpeg;base64,' in text
    assert 'QUALITY_RECAPTURE_REQUIRED' in text
    assert 'chưa phải điểm chính thức' in text
    assert re.findall(r'(?:src|href)="(https?://[^\"]+)"',text)==['http://127.0.0.1:8765']
    assert all(f'web/{name}' in text for name in ('02-process.png','04-review.png','05-decide.png'))
    assert 'make web' in text


def test_web_demo_is_actual_complete_execution():
    from tools.t02_web_demo import verify
    report=verify()
    assert len(report['visited_frames'])==20 and report['human_reviewed']==20
    assert report['final_status']=='REWORK'


def test_web_demo_rejects_changed_review_even_with_same_counts(tmp_path):
    import csv
    import shutil
    from tools.t02_web_demo import verify
    shutil.copytree('demo/web',tmp_path/'web')
    path=tmp_path/'web/review_queue_reviewed.csv'
    with path.open(newline='') as stream:
        rows=list(csv.DictReader(stream))
    rows[0]['review_note']='A different, unconfirmed quality observation'
    with path.open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    with pytest.raises(ValueError,match='signed CVAT decisions'):verify(tmp_path/'web')


def test_evidence_matches_shared_evaluator_and_frozen_protocol():
    from tools.t02_verify import verify_evidence
    assert verify_evidence()==[]


def test_evidence_verifier_detects_forged_metric_even_with_unchanged_hashes(monkeypatch):
    from tools import t02_verify
    read=t02_verify.read_json
    def forged(path):
        value=read(path)
        if str(path)=='reports/metrics_poc.json':
            value['metrics'][0]['value']=0.0
        return value
    monkeypatch.setattr(t02_verify,'read_json',forged)
    assert 'poc: metrics differ from shared evaluator' in t02_verify.verify_evidence()
