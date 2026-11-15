"""Package and verify actual CVAT exports against the frozen T02 review queue."""
from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import re
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

QUEUE = Path("reports/evidence/poc/review_queue.csv")
SOURCE = "Vũ Duy Khanh"
SCREENSHOTS = ["01-task.jpg", "02-review.jpg", "03-save-verify.jpg",
               "04-export.jpg", "04-export-dialog.jpg", "05-export-finished.jpg", "06-summary.jpg"]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def rows(path):
    with Path(path).open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def annotations(path):
    root = ET.parse(path).getroot()
    result = []
    for image in root.findall("image"):
        tags = image.findall("tag")
        if len(tags) != 1 or len(image) != 1:
            raise ValueError(f"Expected exactly one tag per frame: {image.get('id')}")
        tag = tags[0]
        if sorted(a.get("name") for a in tag) != ["review_note", "review_source"]:
            raise ValueError("Expected one review_source and one review_note")
        attrs = {a.get("name"): a.text or "" for a in tag.findall("attribute")}
        result.append(dict(frame=int(image.get("id")), filename=image.get("name"),
                           action=tag.get("label"), **attrs))
    return root, result


def saved_annotations(snapshot):
    """Normalize the authenticated server response for comparison with XML."""
    labels = {label["id"]: label for label in snapshot["labels"]}
    result = []
    if snapshot["annotations"]["shapes"] or snapshot["annotations"]["tracks"]:
        raise ValueError("Expected image-level tags only")
    for tag in snapshot["annotations"]["tags"]:
        label = labels[tag["label_id"]]
        attrs = {a["id"]: a["name"] for a in label["attributes"]}
        result.append(dict(frame=tag["frame"], filename=snapshot["frames"][tag["frame"]]["name"],
                           action=label["name"],
                           **{attrs[a["spec_id"]]: a["value"] for a in tag["attributes"]}))
    return sorted(result, key=lambda row: row["frame"])


def check_screenshot(path):
    if not path.is_file() or path.stat().st_size < 10000:
        raise ValueError(f"Missing screenshot: {path.name}")
    from PIL import Image
    with Image.open(path) as picture:
        if picture.format != "JPEG":
            raise ValueError(f"Expected JPEG screenshot: {path.name}")
        picture.verify()


def verify(directory=Path("demo/cvat")):
    directory = Path(directory)
    evidence = json.loads((directory / "evidence.json").read_text())
    queue, mapping = rows(QUEUE), rows(directory / "frame_mapping.csv")
    predictions = {row["image_id"]: row for row in rows(QUEUE.parent / "ranked_review.csv")}
    root, reviewed = annotations(directory / "annotations.xml")
    if len(reviewed) != 20 or {r["frame"] for r in reviewed} != set(range(20)):
        raise ValueError("Expected all 20 unique frames")
    if len(mapping) != 20 or len(queue) != 20:
        raise ValueError("Expected the complete frozen top20 mapping")
    if evidence["queue_sha256"] != digest(QUEUE):
        raise ValueError("Frozen queue changed")
    reviewed.sort(key=lambda r: r["frame"])
    for i, (entry, mapped, item) in enumerate(zip(reviewed, mapping, queue)):
        if (int(mapped["rank"]) != i + 1 or mapped["image_id"] != item["item_id"]
                or entry["filename"] != mapped["cvat_filename"]
                or mapped["cvat_filename"] != f"{i+1:02d}_{item['item_id']}.jpg"
                or mapped["suggested_action"] != item["suggested_action"]
                or float(mapped["raw_score"]) != float(predictions[item["item_id"]]["score"])
                or float(mapped["queue_score"]) != float(item["score"])):
            raise ValueError("Frame mapping differs from frozen ranking")
        source = Path("fixtures/t02_raw_qc/images") / f"{item['item_id']}.jpg"
        if mapped["source"] != str(source) or mapped["sha256"] != digest(source):
            raise ValueError("Source image checksum mismatch")
        if entry["action"] not in {"KEEP", "RECAPTURE"}:
            raise ValueError("Invalid QC action")
        if entry.get("review_source") != SOURCE:
            raise ValueError("Incorrect review_source")
        if not entry.get("review_note", "").strip() or re.search(r"\bAI\b", entry["review_note"], re.I):
            raise ValueError("Missing or incorrect review_note")
        screenshot = directory / "frames" / f"{i+1:02d}-{item['item_id']}.jpg"
        check_screenshot(screenshot)
    if root.findtext("meta/job/id") != str(evidence["job_id"]):
        raise ValueError("Wrong CVAT job")
    if evidence["human_review_confirmed"] is not False or evidence["operator"] != "AI:Codex":
        raise ValueError("Demo must retain accurate operator and sign-off provenance")
    if evidence["job_state"] != "completed":
        raise ValueError("Job was not completed on CVAT")
    if evidence["frame_count"] != 20 or evidence["review_source"] != SOURCE or evidence["pipeline_imported"] is not False:
        raise ValueError("Incorrect demo metadata")
    snapshot = json.loads((directory / "server_snapshot.json").read_text(encoding="utf-8"))
    if saved_annotations(snapshot) != reviewed:
        raise ValueError("Export does not match saved CVAT API annotations")
    if (snapshot["task"]["id"] != evidence["task_id"] or snapshot["task"]["size"] != 20
            or snapshot["task"]["name"] != evidence["task_name"]
            or snapshot["job"]["id"] != evidence["job_id"] or snapshot["job"]["state"] != "completed"
            or snapshot["server_version"] != evidence["server_version"]
            or len(snapshot["frames"]) != 20 or root.findtext("meta/job/size") != "20"):
        raise ValueError("Server metadata differs from evidence")
    if evidence["frames"] != reviewed or evidence["action_counts"] != dict(Counter(r["action"] for r in reviewed)):
        raise ValueError("Summary differs from exported annotations")
    if evidence["annotation_sha256"] != digest(directory / "annotations.xml"):
        raise ValueError("Annotation checksum mismatch")
    for name in SCREENSHOTS:
        check_screenshot(directory / name)
    for attribute in root.findall(".//labels/label/attributes/attribute"):
        if attribute.findtext("name") == "review_source" and attribute.findtext("default_value") != SOURCE:
            raise ValueError("Incorrect label default review_source")
    return evidence


def record(export, server, mapping, directory):
    directory.mkdir(parents=True, exist_ok=True)
    with ZipFile(export) as archive:
        original = archive.read("annotations.xml")
    root = ET.fromstring(original)
    # Only remove account metadata; image IDs, tag labels and attributes are preserved.
    job = root.find("meta/job")
    for name in ("owner", "assignee"):
        node = job.find(name)
        if node is not None:
            job.remove(node)
    ET.indent(root)
    ET.ElementTree(root).write(directory / "annotations.xml", encoding="utf-8", xml_declaration=True)
    (directory / "frame_mapping.csv").write_bytes(Path(mapping).read_bytes().replace(b"\r\n", b"\n"))
    snapshot = json.loads(Path(server).read_text())
    _, reviewed = annotations(directory / "annotations.xml")
    reviewed.sort(key=lambda r: r["frame"])
    if saved_annotations(snapshot) != reviewed:
        raise ValueError("Export does not match saved CVAT API annotations")
    (directory / "server_snapshot.json").write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    evidence = dict(cvat_url="http://localhost:8080", server_version=snapshot["server_version"],
                    task_id=snapshot["task"]["id"], task_name=snapshot["task"]["name"],
                    job_id=snapshot["job"]["id"], job_state=snapshot["job"]["state"],
                    captured_at=snapshot["captured_at"], frame_count=len(reviewed),
                    review_source=SOURCE, operator="AI:Codex", human_review_confirmed=False,
                    review_source_note="Name entered at the user's explicit request; not human sign-off.",
                    export_format="CVAT for images 1.1", pipeline_imported=False,
                    export_zip_sha256=digest(export), original_xml_sha256=hashlib.sha256(original).hexdigest(),
                    annotation_sha256=digest(directory / "annotations.xml"), queue_sha256=digest(QUEUE),
                    sanitized_metadata=["meta/job/owner", "meta/job/assignee"],
                    action_counts=dict(Counter(r["action"] for r in reviewed)), frames=reviewed)
    (directory / "evidence.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    verify(directory)
    write_gallery(directory, evidence)
    return evidence


def write_gallery(directory, evidence):
    cards = []
    for entry, item in zip(evidence["frames"], rows(QUEUE)):
        image = f"frames/{entry['frame']+1:02d}-{item['item_id']}.jpg"
        cards.append(f'<article><h2>{entry["frame"]+1:02d}. {html.escape(item["item_id"])} · {entry["action"]}</h2>'
                     f'<a href="{image}"><img src="{image}" alt="CVAT frame {entry["frame"]}" loading="lazy"></a>'
                     f'<p>Gợi ý: {item["suggested_action"]}. Kết luận: {entry["action"]}.<br>'
                     f'{html.escape(entry["review_note"])}</p></article>')
    counts = ", ".join(f"{count} {action}" for action, count in sorted(evidence["action_counts"].items()))
    heading = (f'<h1>CVAT local: {evidence["frame_count"]}/20 frame đã lưu</h1>'
               f'<p>Task #{evidence["task_id"]} / Job #{evidence["job_id"]} '
               f'({html.escape(evidence["job_state"])}) · CVAT {html.escape(evidence["server_version"])}<br>'
               f'review_source: {html.escape(evidence["review_source"])}<br>{counts}. Bấm ảnh để xem toàn kích thước.</p>')
    (directory / "index.html").write_text('''<!doctype html><html lang="vi"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>T004 · 20 frame CVAT local</title><style>body{font:18px system-ui;margin:32px auto;max-width:1400px;background:#15212b;color:#edf4f8;padding:0 20px}h1{font-size:38px}h2{font-size:23px}.grid{display:grid;grid-template-columns:1fr 1fr;gap:32px}img{width:100%;height:auto}a{color:#7ce4cc}p{line-height:1.5}@media(max-width:800px){.grid{display:block}article{margin:32px 0}}</style>''' + heading + '''<p>Trợ lý AI thực hiện demo theo yêu cầu. Tên trong thuộc tính không xác nhận người học đã review. <a href="../../docs/HUONG_DAN_DEMO_CVAT_LOCAL.md">Chi tiết và nguồn bằng chứng</a> · <a href="annotations.xml">XML export</a> · <a href="evidence.json">Metadata</a> · <a href="../t004_demo.html">5 slides</a></p><div class="grid">''' + "".join(cards) + "</div></html>", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export", type=Path)
    parser.add_argument("--server", type=Path, default=Path("out/cvat-demo/server-evidence.json"))
    parser.add_argument("--mapping", type=Path, default=Path("out/cvat-demo/frame_mapping.csv"))
    parser.add_argument("--directory", type=Path, default=Path("demo/cvat"))
    args = parser.parse_args()
    result = record(args.export, args.server, args.mapping, args.directory) if args.export else verify(args.directory)
    print(f"PASS: {len(result['frames'])}/20 saved CVAT frames; {result['action_counts']}; review_source={SOURCE}")


if __name__ == "__main__":
    main()
