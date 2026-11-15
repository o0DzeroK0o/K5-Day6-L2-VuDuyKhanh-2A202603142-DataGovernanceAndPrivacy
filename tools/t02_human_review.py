"""Record a later human attestation without rewriting the prior CVAT import.

Only record after the named reviewer explicitly confirms all listed decisions.
The record is a self-attestation from the reviewer, not independent identity proof.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml

from src.common.contact_sheet import render_contact_sheet
from tools.t02_cvat_demo import QUEUE, SOURCE, digest, rows, verify
from tools.t02_cvat_review import RECEIPT as CVAT_RECEIPT, check_run, csv_text, review_rows

RECEIPT = Path('reports/human_review_confirmation.json')
EVIDENCE = Path('reports/evidence/human_review')
STATEMENT = 'Đã xem đủ 20 frame và đồng ý kết quả này'
QUESTION = ('Bạn xác nhận đã trực tiếp xem đủ 20 frame và duyệt kết quả 19 RECAPTURE, '
            '1 KEEP (img_23_1), gồm hai override img_19_2 và img_06_3 chứ?')


def signed_rows(evidence, confirmation):
    if (confirmation['reviewer'] != SOURCE or confirmation['statement'] != STATEMENT
            or confirmation['question'] != QUESTION or confirmation['frame_count'] != 20
            or confirmation['action_counts'] != evidence['action_counts']
            or confirmation['annotation_sha256'] != evidence['annotation_sha256']
            or confirmation['queue_sha256'] != evidence['queue_sha256']
            or confirmation['human_review_confirmed'] is not True):
        raise ValueError('Human confirmation does not cover the saved 20-frame review')
    confirmed = datetime.fromisoformat(confirmation['confirmed_at'])
    captured = datetime.fromisoformat(evidence['captured_at'])
    if confirmed.tzinfo is None or confirmed <= captured:
        raise ValueError('Human confirmation must be timestamped after the CVAT capture')
    expected = review_rows(evidence)
    if confirmation['item_ids'] != [r['item_id'] for r in expected]:
        raise ValueError('Human confirmation queue IDs differ')
    if confirmation['override_ids'] != [r['item_id'] for r in expected if r['reviewer_decision'] == 'edit']:
        raise ValueError('Human confirmation overrides differ')
    return [r | {'reviewer': SOURCE, 'reviewed_at': confirmation['confirmed_at']} for r in expected]


def verify_confirmation():
    evidence = verify()
    confirmation = json.loads(RECEIPT.read_text())
    expected = signed_rows(evidence, confirmation)
    if (confirmation['previous_import_sha256'] != digest(CVAT_RECEIPT)
            or confirmation['review_csv'] != str(EVIDENCE / 'review_queue_reviewed.csv')
            or confirmation['review_csv_sha256'] != digest(EVIDENCE / 'review_queue_reviewed.csv')
            or rows(EVIDENCE / 'review_queue_reviewed.csv') != expected):
        raise ValueError('Human confirmation differs from review CSV or previous import')
    decision = check_run(EVIDENCE, evidence, confirmation)
    if confirmation['status'] != decision['status'] or confirmation['reason_code'] != decision['reason_code']:
        raise ValueError('Human confirmation decision differs from pipeline')
    for name in ('audit_log.jsonl', 'decision_log.csv'):
        if not (EVIDENCE / name).read_bytes().startswith((QUEUE.parent / name).read_bytes()):
            raise ValueError('Human review lost prior append-only history')
    for source, target in (('review_queue_reviewed.csv','review_queue.csv'), ('audit_log.jsonl','audit_log.jsonl'), ('decision_log.csv','decision_log.csv')):
        if (Path('reports') / target).read_bytes() != (EVIDENCE / source).read_bytes():
            raise ValueError('Current report paths differ from confirmed human review')
    cfg = yaml.safe_load(Path('configs/lab.yaml').read_text())
    if cfg['human_review_confirmed'] is not True or not cfg['owner'].startswith(SOURCE):
        raise ValueError('Configuration does not match human confirmation')
    return confirmation


def export_current_review(output):
    """Copy the confirmed review; never silently overwrite different existing work."""
    if not RECEIPT.exists():
        from tools.t02_cvat_review import export_review
        return export_review(output)
    confirmation = verify_confirmation()
    entries = signed_rows(verify(), confirmation)
    content = csv_text(entries)
    if output.exists() and output.read_text() != content:
        raise ValueError('Existing review differs; use a new output directory')
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(content, encoding='utf-8')
    return entries


def record_confirmation(statement, output):
    if statement != STATEMENT:
        raise ValueError('Expected the explicit reviewer statement for all 20 frames')
    if RECEIPT.exists():
        return verify_confirmation()
    evidence = verify()
    entries = review_rows(evidence)
    confirmation = {
        'reviewer': SOURCE, 'confirmed_at': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'source': 'Explicit reviewer confirmation in the project conversation',
        'statement': statement, 'question': QUESTION, 'human_review_confirmed': True,
        'frame_count': 20, 'action_counts': evidence['action_counts'],
        'item_ids': [r['item_id'] for r in entries],
        'override_ids': [r['item_id'] for r in entries if r['reviewer_decision']=='edit'],
        'annotation_sha256': evidence['annotation_sha256'], 'queue_sha256': evidence['queue_sha256'],
        'previous_import': str(CVAT_RECEIPT), 'previous_import_sha256': digest(CVAT_RECEIPT),
        'scope': '20 queue frames and their saved CVAT decisions; does not validate all 40 evaluation labels',
    }
    signed = signed_rows(evidence, confirmation)
    if output.exists() or EVIDENCE.exists():
        raise ValueError('Use fresh output and human evidence directories')
    shutil.copytree(QUEUE.parent, output)
    (output / 'review_queue_reviewed.csv').write_text(csv_text(signed), encoding='utf-8')
    config = Path('configs/lab.yaml')
    previous_config = config.read_text()
    updated = previous_config.replace('human_review_confirmed: false','human_review_confirmed: true').replace(
        'Vũ Duy Khanh — T004 / reviewer (chờ xác nhận người thật)', 'Vũ Duy Khanh — T004 / reviewer')
    config.write_text(updated, encoding='utf-8')
    try:
        subprocess.run([sys.executable,'-m','src.main','--output',str(output),'--run-name','human_review',
                        '--config',str(config),'--offline','--seed','42'], check=True)
        decision = check_run(output, evidence, confirmation)
    except Exception:
        config.write_text(previous_config, encoding='utf-8')
        raise
    render_contact_sheet(pd.DataFrame(signed), output/'contact_sheet.html', image_root='fixtures/t02_raw_qc',
                         title='T004 / T02 · Vũ Duy Khanh · 20 frame đã xác nhận')
    shutil.copytree(output, EVIDENCE)
    for source, target in (('review_queue_reviewed.csv','review_queue.csv'), ('audit_log.jsonl','audit_log.jsonl'),
                          ('decision_log.csv','decision_log.csv'), ('contact_sheet.html','contact_sheet.html')):
        shutil.copy2(EVIDENCE/source, Path('reports')/target)
    confirmation.update(review_csv=str(EVIDENCE/'review_queue_reviewed.csv'),
                        review_csv_sha256=digest(EVIDENCE/'review_queue_reviewed.csv'),
                        status=decision['status'],reason_code=decision['reason_code'])
    RECEIPT.write_text(json.dumps(confirmation,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return verify_confirmation()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--statement', help='Exact, already received reviewer confirmation')
    parser.add_argument('--output', type=Path, default=Path('out/confirmed-review'))
    args=parser.parse_args()
    receipt=record_confirmation(args.statement,args.output) if args.statement else verify_confirmation()
    print(f"PASS: {receipt['reviewer']}, 20/20 confirmed; {receipt['status']} / {receipt['reason_code']}")


if __name__=='__main__':
    main()
