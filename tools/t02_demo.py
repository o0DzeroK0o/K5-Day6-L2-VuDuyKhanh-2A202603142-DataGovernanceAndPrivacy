"""Five-slide offline presentation built from real CVAT and review UI evidence."""
import base64
import html
import json
from pathlib import Path


def picture(relative, caption, css=''):
    path=Path('demo')/relative
    mime='image/png' if path.suffix=='.png' else 'image/jpeg'
    data=f'data:{mime};base64,'+base64.b64encode(path.read_bytes()).decode()
    return (f'<figure class="{css}"><a href="{relative}"><img src="{data}" alt="{html.escape(caption)}" '
            f'data-evidence="{relative}"></a><figcaption>{html.escape(caption)}</figcaption></figure>')


def render_demo(summary, cvat):
    from tools.t02_human_review import verify_confirmation
    signed=verify_confirmation()
    b,p=summary['runs']['baseline'],summary['runs']['poc']
    ci=summary['uncertainty']['results']['paired_delta']['ci95']
    ui=picture('ui/01-workspace.png','Công cụ review offline · đã quyết định đủ 20 frame','workspace')
    review=picture('cvat/03-save-verify.jpg','CVAT job #17 · img_19_2 mở lại sau Save','cvat-review')
    export=picture('cvat/04-export-dialog.jpg','CVAT for images 1.1 · export annotation','export-dialog')
    finished=picture('cvat/05-export-finished.jpg','Requests: Finished · 100%','export-finished')
    counts=picture('cvat/06-summary.jpg','CVAT Info: 19 RECAPTURE · 1 KEEP','counts')
    overrides=picture('ui/02-overrides.png','Bộ lọc hiển thị hai quyết định sửa KEEP → RECAPTURE','overrides')
    defect='data:image/jpeg;base64,'+base64.b64encode(Path('fixtures/t02_raw_qc/images/img_03_2.jpg').read_bytes()).decode()
    slides=[
        ('Kiểm duyệt chất lượng ảnh',f'''<div class="hero"><div><p class="large">20 frame.<br>Quyết định có bằng chứng.</p>
        <p class="byline">Vũ Duy Khanh<br><span>T004 · T02 · Data Governance &amp; Privacy</span></p>
        <p>Ưu tiên ảnh nghi lỗi để review trong budget giới hạn. Lưu nhận xét, override và quyết định cuối.</p>
        <a class="open-tool" href="../reports/contact_sheet.html">Mở công cụ review ↗</a>
        <div class="facts"><b>96 <small>ảnh đầu vào</small></b><b>40 <small>ảnh eval</small></b><b>20 <small>ảnh review</small></b></div></div>{ui}</div>
        <div class="pipeline"><span>01 <b>Load</b></span><i>→</i><span>02 <b>Process</b></span><i>→</i><span>03 <b>Rank</b></span><i>→</i><span>04 <b>Review</b></span><i>→</i><span>05 <b>Decide</b></span></div>'''),
        ('20/20 frame đã được xác nhận',f'''<div class="two"><div>{review}<p class="caption-link"><a href="cvat/index.html">Xem ảnh chụp đầy đủ 20 frame ↗</a> · <a href="cvat/01-task.jpg">Thông tin task</a></p></div>
        <div class="review-copy"><span class="label">REVIEWER</span><h2>Vũ Duy Khanh</h2><p>Đã xác nhận trực tiếp xem đủ 20 frame và đồng ý kết quả.</p>
        <div class="outcomes"><div><strong>19</strong><span>RECAPTURE</span></div><div><strong>1</strong><span>KEEP · img_23_1</span></div></div>
        <hr><h3>Hai quyết định thay đổi</h3><p><b>img_19_2</b> · lỗi nén nhẹ<br><b>img_06_3</b> · quầng lóa</p><p class="small">KEEP → RECAPTURE. Điểm và thứ tự xếp hạng giữ nguyên.</p>
        <a href="../reports/human_review_confirmation.json">Mở bản xác nhận ↗</a></div></div>'''),
        ('Từ CVAT đến kết quả pipeline',f'''<div class="export-layout"><div>{export}<p class="small">Task/job #17 · completed<br>20 frame, mỗi frame đúng một tag.</p></div><div>{finished}{counts}
        <div class="flow"><b>XML</b><span>→</span><b>Review CSV</b><span>→</span><b>Audit &amp; decision</b></div>
        <p>XML khớp nhãn đã lưu và thứ tự queue. Lần ký duyệt mới giữ nguyên toàn bộ lịch sử trước đó.</p>
        <p class="links"><a href="cvat/annotations.xml">XML export ↗</a><a href="cvat/frame_mapping.csv">Frame mapping ↗</a><a href="../reports/audit_log.jsonl">Audit log ↗</a></p></div></div>'''),
        ('Recall tăng, vẫn còn lỗi bỏ sót',f'''<div class="two metrics"><div><table><thead><tr><th>Chỉ số · budget 20</th><th>Baseline</th><th>PoC</th></tr></thead><tbody>
        <tr><td>Defect Recall@20</td><td>{b['recall']} <small>({b['tp']}/20)</small></td><td>{p['recall']} <small>({p['tp']}/20)</small></td></tr>
        <tr><td>Precision@20</td><td>{b['precision']}</td><td>{p['precision']}</td></tr><tr><td>FP / FN</td><td>{b['fp']} / {b['fn']}</td><td>{p['fp']} / {p['fn']}</td></tr></tbody></table>
        <p>Cùng 40 ảnh eval, seed 42, budget 20.<br>Ngưỡng khóa trước eval, không điều chỉnh theo kết quả.</p>
        <p class="small">Nhãn quan sát nội bộ, chưa phải điểm chính thức. CI 95% của chênh lệch recall: [{ci[0]:.2f}, {ci[1]:.2f}], chứa 0. Nguồn nhãn: <a href="../reports/annotations/README.md">metadata</a>.</p>
        <p class="small">Bỏ ROI: recall {summary['runs']['no_roi']['recall']}. Ngưỡng chung: {summary['runs']['global_thresholds']['recall']}.</p></div>
        <div class="failure"><img src="{defect}" alt="img_03_2: quầng lóa nhẹ"><h2>img_03_2 · hạng 21</h2><p>Quầng sáng làm giảm tương phản nhưng chưa đủ pixel cháy trắng. Ảnh lỗi nằm ngoài top20.</p><a href="../reports/failure_gallery.html">Xem 5 failure cases ↗</a></div></div>'''),
        ('Hoàn tất review, cần chụp lại ảnh lỗi',f'''<div class="two closing"><div><span class="label">QUYẾT ĐỊNH BATCH</span><p class="decision">{signed['status']}</p>
        <p class="reason">{signed['reason_code']}</p><p>Owner: <b>Vũ Duy Khanh</b><br>Review trực tiếp: <b>20 / 20</b><br>Ảnh trong queue cần thu lại: <b>19</b></p>
        <p>Giữ 1 ảnh. Thu lại 19 ảnh trong queue và chạy QC lại trước khi xem xét release.</p>
        <p class="small">Xác nhận chỉ bao phủ 20 frame review. Chưa có GT giảng viên; 10 ảnh proxy OOD không thay đánh giá trên dữ liệu thực.</p>
        <p class="links"><a href="../reports/group_report.md">Báo cáo ↗</a><a href="../reports/evidence/human_review/decision.json">Decision ↗</a></p></div>{overrides}</div>
        <p class="closing-note">Tái lập: <code>make t02-submission</code> · Công cụ: <code>make review-ui</code> · Kiểm thử: <code>make test</code></p>'''),
    ]
    pages=''.join(f'<section id="s{i}"><div class="slide-top"><span>T004 / T02</span><span>VŨ DUY KHANH</span></div><h1>{title}</h1>{body}<footer><span>CVAT local · Offline review</span><span>{i:02d} / 05</span></footer></section>' for i,(title,body) in enumerate(slides,1))
    css=Path('tools/demo_assets/demo.css').read_text()
    return f'''<!doctype html><html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>T004 · QC Review · Vũ Duy Khanh</title><style>{css}</style></head><body>{pages}<nav aria-label="Chuyển slide"><button id="prev" aria-label="Slide trước">←</button><span id="position">1 / 5</span><button id="next" aria-label="Slide sau">→</button></nav><script>
    const pages=[...document.querySelectorAll('section')];
    function current(){{return Math.max(0,pages.findIndex(s=>s.getBoundingClientRect().bottom>innerHeight/2));}}
    function move(d){{pages[Math.max(0,Math.min(4,current()+d))].scrollIntoView({{behavior:'instant'}});}}
    document.getElementById('prev').onclick=()=>move(-1);document.getElementById('next').onclick=()=>move(1);
    addEventListener('scroll',()=>document.getElementById('position').textContent=(current()+1)+' / 5');
    document.addEventListener('keydown',e=>{{if(!['ArrowRight','ArrowLeft','PageDown','PageUp','Home','End'].includes(e.key))return;e.preventDefault();if(e.key==='Home')pages[0].scrollIntoView();else if(e.key==='End')pages[4].scrollIntoView();else move(['ArrowRight','PageDown'].includes(e.key)?1:-1);}});
    </script></body></html>'''
