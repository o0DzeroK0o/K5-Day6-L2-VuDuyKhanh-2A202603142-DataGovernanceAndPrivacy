"""Verify and present the captured five-stage web execution."""
from __future__ import annotations

import csv
import html
import json
from collections import Counter
from pathlib import Path

from PIL import Image

DIRECTORY = Path('demo/web')
CAPTURES = [
    ('01-load.png', '01 · Load', 'Đọc 96 ảnh, metadata và kiểm manifest SHA-256.'),
    ('02-process.png', '02 · Process', 'Tính nét, sáng, lóa ROI, blockiness và điểm QC từ pixel.'),
    ('03-rank.png', '03 · Rank', 'Chọn 20 ảnh ưu tiên từ 40 ảnh eval theo điểm đã khóa.'),
    ('04-review.png', '04 · Review', 'Mở đủ 20 frame, lưu review và nhập xác nhận CVAT khớp queue.'),
    ('05-decide.png', '05 · Decide', '20 review trực tiếp, 19 RECAPTURE, 1 KEEP. Batch REWORK.'),
]


def verify(directory=DIRECTORY):
    directory = Path(directory)
    report = json.loads((directory/'verification.json').read_text())
    workflow = json.loads((directory/'workflow.json').read_text())
    decision = json.loads((directory/'decision.json').read_text())
    confirmation = json.loads((directory/'review_confirmation.json').read_text())
    original = json.loads(Path('reports/human_review_confirmation.json').read_text())
    with (directory/'review_queue_reviewed.csv').open(newline='') as stream:
        rows = list(csv.DictReader(stream))
    with Path(original['review_csv']).open(newline='') as stream:
        signed_rows = list(csv.DictReader(stream))
    if rows != signed_rows:
        raise ValueError('Web review rows differ from the signed CVAT decisions')
    if not report['passed'] or report['javascript_errors'] or report['visited_frames'] != original['item_ids']:
        raise ValueError('Web browser verification must cover all 20 confirmed frames')
    if report['run_id'] != workflow['run_id'] or report['revision'] != workflow['revision'] or report['steps'] != workflow['history']:
        raise ValueError('Web verification differs from executed workflow')
    if not all(workflow['steps'][s]['done'] for s in ('load','process','rank','review','decide')):
        raise ValueError('Web workflow has incomplete steps')
    if (decision != workflow['decision'] or decision['status'] != 'REWORK'
            or decision['reason_code'] != 'QUALITY_RECAPTURE_REQUIRED' or decision['metrics']['n_human_reviewed'] != 20):
        raise ValueError('Web decision differs from confirmed review')
    if any(confirmation.get(k) != v for k, v in original.items()):
        raise ValueError('Web import must preserve the original reviewer attestation')
    if [r['item_id'] for r in rows] != original['item_ids'] or any(r['reviewer'] != original['reviewer'] for r in rows):
        raise ValueError('Web review does not match confirmed reviewer and queue')
    if dict(Counter(r['override_value'] or r['suggested_action'] for r in rows)) != original['action_counts']:
        raise ValueError('Web review action counts differ')
    if (directory/'raw_predictions.csv').read_bytes() != Path('reports/evidence/poc/raw_predictions.csv').read_bytes():
        raise ValueError('Web processing changed the frozen predictions')
    with (directory/'item_decisions.csv').open(newline='') as stream:
        final = {r['image_id']:r for r in csv.DictReader(stream)}
    events = [json.loads(line) for line in (directory/'audit_log.jsonl').read_text().splitlines()]
    reviewed_events = {e['item_id']:e for e in events if e['action'].startswith('review:') and e['extra'].get('human_confirmed')}
    for row in rows:
        action = row['override_value'] or row['suggested_action']
        result = final[row['item_id']]
        event = reviewed_events.get(row['item_id'])
        if (result['pred_action'] != action or result['review_state'] != 'human' or result['reviewer'] != original['reviewer']
                or not event or event['actor'] != original['reviewer'] or event['after'] != action or event['reason'] != row['review_note']):
            raise ValueError('Web final actions or audit differ from the confirmed review')
    for name in [c[0] for c in CAPTURES] + ['06-mobile.png']:
        with Image.open(directory/name) as picture:
            if picture.format != 'PNG' or picture.width < 390 or picture.height < 800:
                raise ValueError('Web capture dimensions or format invalid')
            picture.verify()
    return report


def main():
    report = verify()
    cards = ''.join(f'<section><h2>{title}</h2><p>{caption}</p><a href="{name}"><img src="{name}" alt="{html.escape(caption)}" loading="lazy"></a></section>'
                    for name, title, caption in CAPTURES)
    content = f'''<!doctype html><html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>T004 · Pipeline web chạy thật</title><style>
    *{{box-sizing:border-box}}body{{margin:40px auto;max-width:1300px;padding:0 24px;background:#f1f5f4;color:#183b41;font:17px/1.6 system-ui}}h1{{font-size:36px;line-height:1.2}}h2{{font-size:24px}}a{{color:#126f60}}code{{background:#e0ebe5;padding:3px 6px}}section{{margin:35px 0;background:white;padding:24px;border:1px solid #d4e2dd;border-radius:9px}}img{{width:100%;height:auto}}.links{{display:flex;flex-wrap:wrap;gap:18px}}small{{color:#587477}}@media(max-width:700px){{body{{padding:0 14px;margin:24px auto}}section{{padding:14px}}h1{{font-size:29px}}}}
    </style></head><body><h1>Năm bước pipeline trên web</h1><p>Vũ Duy Khanh · T004 / T02</p>
    <p>Chạy <code>make web</code>, mở <a href="http://127.0.0.1:8765">http://127.0.0.1:8765</a> để thao tác.
    Đây là gallery ảnh chụp lần chạy qua HTTP. Kết quả và audit bên dưới được tải từ máy chủ.</p>
    <p><small>Lượt {report['run_id']} · phiên bản {report['revision']} · kiểm tra {html.escape(report['tested_at'])} · Chromium {report['browser']}</small></p>
    <div class="links"><a href="verification.json">Kết quả kiểm thử</a><a href="workflow.json">Lịch sử chạy</a><a href="decision.json">Decision</a><a href="review_queue_reviewed.csv">Review CSV</a><a href="audit_log.jsonl">Audit</a><a href="review_confirmation.json">Xác nhận đã nhập</a><a href="../cvat/index.html">20 frame CVAT</a><a href="../t004_demo.html">5 slides</a></div>
    {cards}<p><a href="06-mobile.png">Ảnh giao diện trên màn hình 390px</a> · <a href="../../docs/HUONG_DAN_CHAY_DEMO_T004.md">Hướng dẫn chạy</a></p></body></html>'''
    (DIRECTORY/'index.html').write_text(content, encoding='utf-8')
    print('PASS: five executed web stages, 20 frames, unchanged predictions and verified confirmation.')


if __name__ == '__main__': main()
