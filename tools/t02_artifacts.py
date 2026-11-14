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
    b,p=summary["runs"]["baseline"],summary["runs"]["poc"]
    ci=summary["uncertainty"]["results"]["paired_delta"]["ci95"]
    deck=[
        ('T02 · Raw QC Triage','<p class="lead">Ưu tiên 20 ảnh cần kiểm chất lượng</p><p>T004 · Vũ Duy Khánh · nhóm 1 thành viên</p><p>96 ảnh synthetic CC0<br>Seed 42 · CPU · chạy offline</p><p class="note">Nhãn tự kiểm và review do AI hỗ trợ. Người học cần xác nhận trước khi nộp.</p>'),
        ('Pipeline và protocol','<ol><li>Đọc ảnh, metadata và kiểm SHA-256</li><li>Tính độ nét, tối, saturation ROI, blockiness</li><li>Xếp hạng 20 ảnh trong pool eval</li><li>Review, override, ghi audit</li><li>KEEP / RECAPTURE và quyết định batch</li></ol><p class="note">56 dev / 14 scene để chọn ngưỡng. 40 eval / 10 scene để tự kiểm. Freeze 6c525dc trước khi xem eval.</p>'),
        ('Kết quả kiểm tra nội bộ',f'<table><tr><th>Chỉ số</th><th>Baseline</th><th>PoC</th></tr><tr><td>Defect Recall@20</td><td>{b["recall"]} ({b["tp"]}/20)</td><td>{p["recall"]} ({p["tp"]}/20)</td></tr><tr><td>Precision@20</td><td>{b["precision"]}</td><td>{p["precision"]}</td></tr><tr><td>FP / FN</td><td>{b["fp"]} / {b["fn"]}</td><td>{p["fp"]} / {p["fn"]}</td></tr></table><p>Bỏ ROI: recall {summary["runs"]["no_roi"]["recall"]}. Dùng ngưỡng chung: {summary["runs"]["global_thresholds"]["recall"]}.</p><p class="note">40 nhãn quan sát AI, chưa phải điểm chính thức. CI 95% của chênh lệch recall: [{ci[0]:.2f}, {ci[1]:.2f}]. Khoảng chứa 0, chưa chứng minh cải thiện chắc chắn.</p>'),
        ('Glare nhẹ vẫn bị bỏ sót',f'<img class="hero" src="{uri("fixtures/t02_raw_qc/images/img_03_2.jpg")}" alt="img_03_2"><p>img_03_2 có quầng sáng làm giảm tương phản nhưng không cháy trắng đủ mạnh.</p><p class="note">PoC xếp ngoài top20. Không chỉnh ngưỡng sau eval. Các case night, cam_B, glare cục bộ và FP ở <a href="../reports/failure_gallery.html">gallery</a>.</p>'),
        ('Review và bàn giao','<p class="lead">HOLD · HUMAN_REVIEW_REQUIRED</p><p>AI đã xem và điền 20 quyết định. Hai override KEEP thành RECAPTURE có audit. Score chấm điểm giữ nguyên.</p><p>10 ảnh proxy T13 đều được xem bằng mắt. Chưa có dữ liệu thật hoặc GT giảng viên.</p><p class="note"><a href="../reports/contact_sheet.html">Mở contact sheet</a> · <a href="../docs/HUONG_DAN_HOAN_TAT_T004.md">Các bước người học cần xác nhận</a><br>Demo chạy offline. Tag ghi thời gian thực tế, không chứng nhận đã làm ở phút 180.</p>'),
    ]
    pages=''.join(f'<section id="s{i}"><div class="eyebrow">T004 / AI20K DAY 06</div><h1>{title}</h1>{body}<footer>{i} / {len(deck)}</footer></section>' for i,(title,body) in enumerate(deck,1))
    Path('demo').mkdir(exist_ok=True)
    Path('demo/t004_demo.html').write_text('''<!doctype html><html lang="vi"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>T004 · T02 Demo</title><style>*{box-sizing:border-box}body{margin:0;background:#15212b;color:#edf4f8;font:25px system-ui}section{position:relative;min-height:100vh;padding:6vh 8vw;page-break-after:always;max-width:1500px;margin:auto;border-bottom:1px solid #384751}h1{font-size:54px;line-height:1.1;margin:25px 0 40px;max-width:1100px}.lead{font-size:37px;color:#7ce4cc}.eyebrow{font-size:16px;letter-spacing:3px;color:#7ce4cc}p,li{line-height:1.5}li{margin:12px 0}.note{font-size:21px;color:#b7c9d5;max-width:1080px}table{border-collapse:collapse;width:100%;margin:30px 0}td,th{text-align:left;padding:16px;border-bottom:1px solid #4c5c67}th{color:#7ce4cc}footer{margin-top:32px;font-size:16px;color:#849cac}.hero{width:520px;max-width:100%;image-rendering:auto;float:right;margin:0 0 22px 40px}a{color:#7ce4cc}@media(max-width:800px){h1{font-size:36px}body{font-size:20px}.hero{float:none;margin:0;width:100%}section{padding:32px 24px}.lead{font-size:28px}.note{font-size:18px}}@media print{body{background:white;color:black;font-size:18pt}section{height:190mm;min-height:0;padding:10mm;break-inside:avoid}h1{font-size:32pt}.note{color:#333;font-size:14pt}.eyebrow,th,.lead,a{color:#135c53}}</style>'''+pages+'''<script>document.addEventListener('keydown',e=>{if(!['ArrowRight','ArrowLeft','PageDown','PageUp'].includes(e.key))return;const p=[...document.querySelectorAll('section')];let i=p.findIndex(x=>x.getBoundingClientRect().bottom>innerHeight/2);i=Math.max(0,Math.min(p.length-1,i+(['ArrowRight','PageDown'].includes(e.key)?1:-1)));p[i].scrollIntoView({behavior:'smooth'});});</script></html>''',encoding='utf-8')
    print('Generated 5 failure cases and 5 offline demo pages from actual evidence.')


if __name__=='__main__':
    main()
