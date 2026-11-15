"""Generate offline failure gallery and five-page demo from measured evidence."""
from __future__ import annotations

import base64
import html
import json
from pathlib import Path

import pandas as pd

from src.common.io import write_json


def uri(path):
    return "data:image/jpeg;base64,"+base64.b64encode(Path(path).read_bytes()).decode()


def main():
    root=Path("reports");summary=json.loads((root/"analysis_summary.json").read_text())
    pred={n:pd.read_csv(root/f"evidence/{n}/ranked_review.csv").set_index("image_id") for n in ("baseline","poc")}
    examples=[
        ("img_03_0","Night hữu ích / cam_B", "Baseline ưu tiên nhầm ảnh sạch vì Laplacian giảm khi camera mềm. PoC dùng ngưỡng cam_B và ngưỡng night, giữ được ảnh. Không mặc định mọi ảnh đêm đều lỗi."),
        ("img_05_3","Glare cục bộ trên biển synthetic", "Độ nét toàn ảnh còn cao nên baseline bỏ sót. Ô ROI có tỷ lệ pixel cháy sáng lớn giúp PoC đưa ảnh vào queue."),
        ("img_03_2","PoC bỏ sót glare nhẹ", "Quầng sáng làm giảm tương phản nhưng chưa tạo đủ pixel >245. Tín hiệu saturation ROI thấp; ảnh nằm ngoài top20. Cần nghiên cứu độ tương phản cục bộ trên dev mới, không sửa ngưỡng sau eval này."),
        ("img_23_1","PoC báo động nhầm trong top20", "Cạnh thật trùng lưới 8 pixel tạo blockiness hơi cao. Score vẫn dưới ngưỡng RECAPTURE nhưng quota top20 bắt buộc chọn đủ 20 nên ảnh sạch vẫn vào queue."),
        ("img_19_2","Review sửa đề nghị KEEP", "Nén nhẹ dưới ngưỡng tự động nhưng nằm trong top20. AI xem ảnh đề nghị RECAPTURE; raw score và ranking giữ nguyên để không làm đẹp metric sau review."),
    ]
    cards=[];records=[]
    for ident,title,reason in examples:
        row=pred["poc"].loc[ident]
        rec={"image_id":ident,"title":title,"root_cause":reason,"path":row.path,"light":row.light,"camera_id":row.camera_id}
        for name in pred:
            p=pred[name];pool=p[p.split=="eval"].sort_values("score",ascending=False,kind="mergesort")
            rec[f"{name}_score"]=float(p.loc[ident,"score"])
            rec[f"{name}_rank"]=int(pool.index.get_loc(ident)+1)
            rec[f"{name}_raw_action"]=p.loc[ident,"raw_action"]
        records.append(rec)
        details=f'Baseline rank {rec["baseline_rank"]}, score {rec["baseline_score"]}; PoC rank {rec["poc_rank"]}, score {rec["poc_score"]}'
        cards.append(f'<article><img alt="{ident}" src="{uri(Path("fixtures/t02_raw_qc")/row.path)}"><div><h2>{html.escape(title)}</h2><p>{ident} · {row.camera_id} · {row.light}</p><p>{html.escape(reason)}</p><small>{details}</small></div></article>')
    write_json(root/"failure_cases.json",records)
    (root/"failure_gallery.html").write_text('''<!doctype html><html lang="vi"><meta charset="utf-8"><title>T004: failure cases</title><style>body{font:18px system-ui;background:#f3f5f6;color:#19232e;max-width:1100px;margin:32px auto}article{display:flex;gap:28px;background:white;padding:24px;margin:20px 0}img{width:400px;object-fit:contain}h1{font-size:34px}h2{font-size:24px}small{font-size:13px} @media(max-width:800px){article{display:block}img{width:100%}}</style><h1>T02 · Các lỗi cần giải thích</h1><p>Nhãn quan sát AI nội bộ, chưa xác nhận bởi người thật. Ngưỡng giữ nguyên sau freeze.</p>'''+''.join(cards)+'</html>',encoding='utf-8')
    from tools.t02_cvat_demo import verify
    cvat = verify()
    Path('demo').mkdir(exist_ok=True)
    Path('demo/t004_demo.html').write_text(render_demo(summary, cvat), encoding='utf-8')
    print('Generated 5 failure cases and 5 offline demo pages with verified CVAT evidence.')


def cvat_image(name, caption, css=""):
    path = f"cvat/{name}"
    return (f'<figure class="{css}"><a href="{path}">'
            f'<img src="{uri(Path("demo") / path)}" alt="{html.escape(caption)}" '
            f'data-evidence="{path}"></a><figcaption>{html.escape(caption)}</figcaption></figure>')


def render_demo(summary, cvat):
    """Render the existing five-slide format using measured, saved evidence."""
    b, p = summary["runs"]["baseline"], summary["runs"]["poc"]
    ci = summary["uncertainty"]["results"]["paired_delta"]["ci95"]
    count, counts = cvat["frame_count"], cvat["action_counts"]
    source = html.escape(cvat["review_source"])
    import_status = ('Đã nhập 20 quyết định CVAT vào pipeline, kiểm khớp CSV và audit.'
                     if cvat["pipeline_imported"] else 'Annotation CVAT chưa nhập vào pipeline.')
    task = cvat_image("01-task.jpg", f'Task #{cvat["task_id"]}, job #{cvat["job_id"]}: {count} frame, completed')
    saved = cvat_image("03-save-verify.jpg", "Frame 17 mở lại sau Save: img_19_2, RECAPTURE")
    export = cvat_image("04-export-dialog.jpg", "Export job dataset: CVAT for images 1.1, không kèm ảnh", "dialog")
    finished = cvat_image("05-export-finished.jpg", f'Export của job #{cvat["job_id"]}: Finished, 100%', "receipt")
    overview = cvat_image("06-summary.jpg", f'CVAT Info: {counts["KEEP"]} KEEP, {counts["RECAPTURE"]} RECAPTURE, tổng {count} tag')
    deck = [
        ('T02: QC 20 ảnh trên CVAT', f'''<div class="columns intro"><div>
        <p class="lead">{source}</p><p>T004, nhóm 1 thành viên<br>96 ảnh synthetic CC0<br>Seed 42, CPU, offline</p>
        <ol><li>Đọc ảnh, kiểm SHA-256</li><li>Tính tín hiệu chất lượng</li><li>Xếp hạng top20</li><li>Review và ghi lý do</li><li>KEEP / RECAPTURE</li></ol>
        </div>{task}</div><p class="note">56 dev / 14 scene để chọn ngưỡng. 40 eval / 10 scene để tự kiểm. Freeze 6c525dc trước eval.</p>'''),
        ('Review và lưu đủ 20 frame', f'''<div class="columns review">{saved}<div>
        <p class="lead">{count}/20 đã lưu</p><p><code>review_source</code><br>{source}</p>
        <p><code>review_note</code> ghi lỗi quan sát được trên từng ảnh.</p>
        <p>img_19_2 và img_06_3: đổi gợi ý KEEP thành RECAPTURE. Score và ranking giữ nguyên.</p>
        <p class="note"><a href="cvat/02-review.jpg">Xem frame mờ</a><br><a href="cvat/index.html">Xem đủ 20 ảnh chụp</a></p></div></div>'''),
        ('Export đầy đủ 20 nhãn', f'''<div class="columns export"><div>
        <p class="lead">{counts["RECAPTURE"]} RECAPTURE<br>{counts["KEEP"]} KEEP</p>
        <p>Job #{cvat["job_id"]}: {html.escape(cvat["job_state"])}<br>Mỗi frame có đúng một tag.</p>
        <p>XML khớp 20 nhãn đã lưu trên server và thứ tự queue đã freeze.</p>
        <p class="note"><a href="cvat/annotations.xml">Mở XML export</a><br><a href="cvat/frame_mapping.csv">Đối chiếu frame và image_id</a></p>
        </div>{export}</div>{finished}'''),
        ('Kết quả tự kiểm và lỗi còn sót', f'''<div class="columns metrics"><div>
        <table><tr><th>Chỉ số</th><th>Baseline</th><th>PoC</th></tr>
        <tr><td>Defect Recall@20</td><td>{b["recall"]} ({b["tp"]}/20)</td><td>{p["recall"]} ({p["tp"]}/20)</td></tr>
        <tr><td>Precision@20</td><td>{b["precision"]}</td><td>{p["precision"]}</td></tr>
        <tr><td>FP / FN</td><td>{b["fp"]} / {b["fn"]}</td><td>{p["fp"]} / {p["fn"]}</td></tr></table>
        <p>Bỏ ROI: recall {summary["runs"]["no_roi"]["recall"]}.<br>Ngưỡng chung: {summary["runs"]["global_thresholds"]["recall"]}.</p>
        <p class="note">40 nhãn quan sát AI, chưa phải điểm chính thức. CI 95% của chênh lệch recall: [{ci[0]:.2f}, {ci[1]:.2f}]. Khoảng chứa 0.</p>
        </div><div><figure><img src="{uri("fixtures/t02_raw_qc/images/img_03_2.jpg")}" alt="img_03_2 có quầng lóa nhẹ"><figcaption>img_03_2: glare nhẹ ngoài top20</figcaption></figure>
        <p>Quầng sáng giảm tương phản nhưng chưa đủ pixel cháy trắng. PoC còn bỏ sót.</p>
        <p class="note">Giữ ngưỡng sau eval. <a href="../reports/failure_gallery.html">5 failure cases</a>, gồm night và cam_B.</p></div></div>'''),
        ('Bằng chứng CVAT và bàn giao', f'''<div class="columns closing"><div>
        <p class="lead">CVAT: {count}/{count} frame</p><p><a href="cvat/index.html">Gallery từng frame</a><br><a href="cvat/evidence.json">Metadata và checksum</a><br><a href="../docs/HUONG_DAN_DEMO_CVAT_LOCAL.md">Hướng dẫn CVAT local</a></p>
        <p><strong>Pipeline: HOLD</strong><br><code>HUMAN_REVIEW_REQUIRED</code></p>
        </div>{overview}</div><p class="note">Trợ lý AI thực hiện thao tác demo. Tên trong thuộc tính theo yêu cầu của Vũ Duy Khanh. Xác nhận review của người học còn chờ. {import_status}</p>
        <p class="note">Đã kiểm 10 ảnh proxy T13. Chưa có dữ liệu thật hoặc GT giảng viên. <a href="../docs/HUONG_DAN_HOAN_TAT_T004.md">Các bước người học cần xác nhận</a>.</p>'''),
    ]
    pages = ''.join(f'<section id="s{i}"><div class="eyebrow">T004 / AI20K DAY 06</div><h1>{title}</h1>{body}<footer>{i} / {len(deck)} · Ảnh CVAT thật, bấm để mở bản đầy đủ</footer></section>' for i, (title, body) in enumerate(deck, 1))
    return '''<!doctype html><html lang="vi"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>T004 · T02 Demo CVAT local</title><style>
    *{box-sizing:border-box}body{margin:0;background:#15212b;color:#edf4f8;font:24px system-ui}
    section{position:relative;min-height:100vh;padding:4vh 5vw;page-break-after:always;max-width:1600px;margin:auto;border-bottom:1px solid #384751}
    h1{font-size:48px;line-height:1.12;margin:22px 0 32px}.lead{font-size:32px;color:#7ce4cc;margin-top:0}
    .eyebrow{font-size:16px;letter-spacing:3px;color:#7ce4cc}p,li{line-height:1.45}p{margin:0 0 24px}li{margin:6px 0}
    ol{padding-left:28px}.note{font-size:21px;color:#b7c9d5;line-height:1.45;margin:22px 0 0}code{font-size:.88em;overflow-wrap:anywhere}
    .columns{display:grid;grid-template-columns:1fr 1.8fr;gap:36px;align-items:start}.review{grid-template-columns:2.5fr 1fr}.export{grid-template-columns:1fr 1fr;align-items:center}
    .metrics{grid-template-columns:1.8fr 1fr}.closing{grid-template-columns:1fr 1.8fr}.intro{align-items:center}
    figure{margin:0;min-width:0}figure img{display:block;width:100%;height:auto}figcaption{font-size:17px;line-height:1.4;color:#b7c9d5;margin-top:9px}
    .dialog{max-width:520px;justify-self:center}.receipt{margin-top:24px}table{border-collapse:collapse;width:100%;margin:0 0 24px}td,th{text-align:left;padding:16px 12px;border-bottom:1px solid #4c5c67}th{color:#7ce4cc}
    footer{margin-top:28px;font-size:16px;color:#b7c9d5}a{color:#7ce4cc}
    @media(max-width:900px){body{font-size:20px}h1{font-size:36px}.columns{grid-template-columns:1fr}.lead{font-size:28px}section{padding:32px 24px}.note{font-size:18px}.dialog{justify-self:start}.review figure{order:2}th,td{padding:10px 6px}}
    @media print{@page{size:A4 landscape;margin:0}body{background:white;color:black;font-size:13pt}section{width:297mm;height:210mm;min-height:0;padding:10mm;break-inside:avoid;overflow:hidden}h1{font-size:26pt;margin:12px 0 18px}.eyebrow,footer,figcaption{font-size:9pt}.lead{font-size:21pt}.note{color:#333;font-size:12pt;margin-top:12px}p{margin-bottom:14px}.columns{gap:22px}.dialog{max-width:380px}.eyebrow,th,.lead,a{color:#135c53}td,th{padding:10px}footer{margin-top:16px}}
    </style>''' + pages + '''<script>document.addEventListener('keydown',e=>{if(!['ArrowRight','ArrowLeft','PageDown','PageUp'].includes(e.key))return;e.preventDefault();const p=[...document.querySelectorAll('section')];let i=p.findIndex(x=>x.getBoundingClientRect().bottom>innerHeight/2);i=Math.max(0,Math.min(p.length-1,i+(['ArrowRight','PageDown'].includes(e.key)?1:-1)));p[i].scrollIntoView({behavior:'smooth'});});</script></html>'''


if __name__=='__main__':
    main()
