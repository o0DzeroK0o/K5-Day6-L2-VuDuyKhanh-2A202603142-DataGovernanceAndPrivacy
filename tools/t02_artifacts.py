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
        ("img_19_2","Review sửa đề nghị KEEP", "Nén nhẹ dưới ngưỡng tự động nhưng nằm trong top20. Kết quả review đề nghị RECAPTURE; raw score và ranking giữ nguyên để không làm đẹp metric sau review."),
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
    (root/"failure_gallery.html").write_text('''<!doctype html><html lang="vi"><meta charset="utf-8"><title>T004: failure cases</title><style>body{font:18px system-ui;background:#f3f5f6;color:#19232e;max-width:1100px;margin:32px auto}article{display:flex;gap:28px;background:white;padding:24px;margin:20px 0}img{width:400px;object-fit:contain}h1{font-size:34px}h2{font-size:24px}small{font-size:13px} @media(max-width:800px){article{display:block}img{width:100%}}</style><h1>T02 · Các lỗi cần giải thích</h1><p>Nhãn quan sát nội bộ, chưa phải GT giảng viên; nguồn tại annotations/README.md. Ngưỡng giữ nguyên sau freeze.</p>'''+''.join(cards)+'</html>',encoding='utf-8')
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
    from tools.t02_demo import render_demo as render
    return render(summary, cvat)


if __name__=='__main__':
    main()
