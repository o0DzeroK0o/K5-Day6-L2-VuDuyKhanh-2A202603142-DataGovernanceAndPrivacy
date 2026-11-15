"""Offline HTML contact sheet for human review (no server, no CDN).

Each card shows image(s) + fields + a decision dropdown + note box.
The "Export decisions CSV" button downloads a file with the REVIEW_COLUMNS
schema, which `review.load_review_decisions` can read back.
"""
from __future__ import annotations

import base64
import hashlib
import html
import io
import json
import os
import re
from pathlib import Path
from typing import Iterable

import pandas as pd
from PIL import Image, ImageDraw

DECISIONS = ["", "approve", "reject", "edit", "escalate", "skip"]


def _thumb_data_uri(path: str | Path, width: int, boxes: list[dict] | None = None) -> str:
    """Return base64 JPEG thumbnail (optionally with boxes drawn: dicts x,y,w,h,label,color in source px)."""
    img = Image.open(path).convert("RGB")
    if boxes:
        d = ImageDraw.Draw(img)
        for b in boxes:
            x, y, w, h = float(b["x"]), float(b["y"]), float(b["w"]), float(b["h"])
            color = b.get("color", "red")
            d.rectangle([x, y, x + w, y + h], outline=color, width=max(2, img.width // 300))
            if b.get("label"):
                d.text((x + 2, max(0, y - 12)), str(b["label"]), fill=color)
    scale = width / img.width
    img = img.resize((width, max(1, int(img.height * scale))))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=80)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def render_contact_sheet(
    queue: pd.DataFrame,
    out_html: str | Path,
    image_col: str | None = "evidence_path",
    before_image_col: str | None = None,
    fields: Iterable[str] = ("rank", "item_id", "score", "reason", "suggested_action", "slice"),
    title: str = "Review queue",
    image_root: str | Path | None = None,
    thumb_width: int = 280,
    boxes_by_item: dict[str, list[dict]] | None = None,
    embed: bool = True,
) -> Path:
    """Write a self-contained review page.

    queue          : DataFrame (usually the review_queue.csv rows)
    image_col      : column with image path (after / current)
    before_image_col: optional column with original image path (before/after grid)
    image_root     : base folder for relative image paths
    boxes_by_item  : optional {item_id: [box dicts]} drawn on the 'after' image
    embed          : True = base64 thumbnails (portable single file)
    """
    out_html = Path(out_html)
    out_html.parent.mkdir(parents=True, exist_ok=True)
    root = Path(image_root) if image_root else Path(".")
    fields = list(fields)
    records = queue.fillna("").astype(str).to_dict(orient="records")
    if len({r.get("item_id", "") for r in records}) != len(records):
        raise ValueError("review queue requires unique item_id values")
    cards = []
    for index, row in enumerate(records):
        imgs = []
        for col, label in ((before_image_col, "before"), (image_col, "after" if before_image_col else "")):
            if not col or not row.get(col):
                continue
            p = Path(row[col])
            p = p if p.is_absolute() else root / p
            if not p.exists():
                imgs.append(f'<div class="missing">Không tìm thấy ảnh: {html.escape(str(p))}</div>')
                continue
            boxes = (boxes_by_item or {}).get(row.get("item_id", "")) if label != "before" else None
            src = _thumb_data_uri(p, max(thumb_width, 640), boxes) if embed else os.path.relpath(p, out_html.parent)
            cap = f"<figcaption>{label}</figcaption>" if label else ""
            alt = html.escape(f"{row.get('item_id', '')} {label}".strip(), quote=True)
            imgs.append(f'<figure><button type="button" class="zoom" aria-label="Phóng to {alt}">'
                        f'<img alt="{alt}" src="{html.escape(src, quote=True)}" width="{thumb_width}"></button>{cap}</figure>')
        meta = "".join(
            f"<div><dt>{html.escape(f)}</dt><dd>{html.escape(row[f])}</dd></div>" for f in fields if f in row
        )
        labels = {"": "Chưa chọn", "approve": "Đồng ý đề nghị", "edit": "Sửa hành động",
                  "reject": "Từ chối đề nghị", "escalate": "Cần xác minh", "skip": "Bỏ qua / xem sau"}
        opts = "".join(f'<option value="{d}">{labels[d]}</option>' for d in DECISIONS)
        item_id = html.escape(row.get("item_id", ""))
        rank = html.escape(row.get("rank", str(index + 1)))
        action = html.escape(row.get("suggested_action", ""))
        cards.append(
            f'<article class="card" data-index="{index}" data-item="{item_id}">'
            f'<div class="card-head"><span class="rank">{rank.zfill(2)}</span><h2>{item_id}</h2>'
            f'<span class="action">{action}</span></div><div class="imgs">{"".join(imgs)}</div>'
            f'<div class="card-body"><details><summary>Thông tin và tín hiệu</summary><dl>{meta}</dl></details>'
            f'<label for="dec-{index}">Quyết định</label><select id="dec-{index}" class="dec">{opts}</select>'
            f'<label for="ov-{index}" class="ov-label">Hành động thay thế</label>'
            f'<input id="ov-{index}" class="ov" placeholder="Giá trị override" autocomplete="off">'
            f'<label for="note-{index}">Nhận xét chất lượng</label>'
            f'<textarea id="note-{index}" class="note" rows="2" placeholder="Lỗi quan sát được, lý do giữ hoặc chụp lại…"></textarea>'
            f'<p class="card-state">Chưa review</p></div></article>'
        )
    rows_json = json.dumps(records, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    assets = Path(__file__).with_name("review_ui")
    values = {"TITLE": html.escape(title), "CARDS": "\n".join(cards), "ROWS": rows_json,
              "KEY": hashlib.sha256(rows_json.encode()).hexdigest(), "N": str(len(queue)),
              "CSS": (assets / "review.css").read_text(), "JS": (assets / "review.js").read_text()}
    page = re.sub(r"__(TITLE|CARDS|ROWS|KEY|N|CSS|JS)__", lambda m: values[m[1]],
                  (assets / "index.html").read_text())
    out_html.write_text(page, encoding="utf-8")
    return out_html
