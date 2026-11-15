"""Contract checks for the complete saved CVAT demo, independent of the server."""
from __future__ import annotations

import base64
import csv
import json
import re
import shutil
from html.parser import HTMLParser
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

import pytest

from tools.t02_artifacts import render_demo
from tools.t02_cvat_demo import SOURCE, record, verify


@pytest.fixture
def package(tmp_path):
    target = tmp_path / "cvat"
    shutil.copytree("demo/cvat", target)
    return target


def edit_xml(directory, change):
    path = directory / "annotations.xml"
    tree = ET.parse(path)
    change(tree.getroot())
    tree.write(path, encoding="utf-8", xml_declaration=True)


def test_saved_export_covers_every_frozen_frame():
    evidence = verify()
    assert evidence["frame_count"] == 20
    assert evidence["action_counts"] == {"KEEP": 1, "RECAPTURE": 19}
    assert all(frame["review_source"] == SOURCE for frame in evidence["frames"])
    assert evidence["job_state"] == "completed"
    assert not evidence["human_review_confirmed"]
    assert evidence["pipeline_imported"]


@pytest.mark.parametrize("change", [
    lambda root: root.remove(root.findall("image")[-1]),
    lambda root: root.findall("image")[-1].set("id", "0"),
    lambda root: ET.SubElement(root.find("image"), "tag", label="KEEP"),
])
def test_incomplete_or_duplicate_frame_labels_fail(package, change):
    edit_xml(package, change)
    with pytest.raises(ValueError, match="20 unique frames|exactly one tag"):
        verify(package)


@pytest.mark.parametrize("attribute,value", [
    ("review_source", "AI:Codex"),
    ("review_source", "Vũ Duy Khánh"),
    ("review_note", "AI review"),
    ("review_note", "ai review"),
    ("review_note", "  "),
])
def test_review_fields_honor_requested_name_and_quality_notes(package, attribute, value):
    edit_xml(package, lambda root: setattr(root.find(f"image/tag/attribute[@name='{attribute}']"), "text", value))
    with pytest.raises(ValueError, match=attribute):
        verify(package)


@pytest.mark.parametrize("column,value", [
    ("image_id", "img_00_0"),
    ("cvat_filename", "20_img_13_3.jpg"),
    ("queue_score", "0"),
    ("suggested_action", "KEEP"),
    ("sha256", "0" * 64),
])
def test_mapping_cannot_change_frozen_queue_or_image_bytes(package, column, value):
    path = package / "frame_mapping.csv"
    with path.open(newline="") as stream:
        reader = csv.DictReader(stream)
        fields, mapping = reader.fieldnames, list(reader)
    mapping[0][column] = value
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fields)
        writer.writeheader()
        writer.writerows(mapping)
    with pytest.raises(ValueError, match="mapping|checksum"):
        verify(package)


def test_missing_last_frame_screenshot_fails(package):
    (package / "frames/20-img_06_3.jpg").unlink()
    with pytest.raises(ValueError, match="Missing screenshot"):
        verify(package)


@pytest.mark.parametrize("field,value", [
    ("action_counts", {"KEEP": 20}),
    ("frame_count", 3),
    ("job_state", "in progress"),
    ("human_review_confirmed", True),
])
def test_summary_cannot_claim_inconsistent_counts_or_human_signoff(package, field, value):
    path = package / "evidence.json"
    data = json.loads(path.read_text())
    data[field] = value
    path.write_text(json.dumps(data, ensure_ascii=False))
    with pytest.raises(ValueError):
        verify(package)


def test_saved_api_annotations_must_match_export(package):
    path = package / "server_snapshot.json"
    data = json.loads(path.read_text())
    data["annotations"]["tags"].pop()
    path.write_text(json.dumps(data, ensure_ascii=False))
    with pytest.raises(ValueError, match="saved CVAT API"):
        verify(package)


def test_submission_verifier_reports_cvat_contract_failure(monkeypatch):
    from tools import t02_verify
    def incomplete():
        raise ValueError("Expected all 20 unique frames")
    monkeypatch.setattr(t02_verify, "verify_cvat_demo", incomplete)
    assert "CVAT demo: Expected all 20 unique frames" in t02_verify.verify_evidence()


def test_packaging_retains_labels_and_removes_only_account_metadata(package, tmp_path):
    root = ET.parse(package / "annotations.xml").getroot()
    job = root.find("meta/job")
    for name in ("owner", "assignee"):
        node = ET.SubElement(job, name)
        ET.SubElement(node, "username").text = "private-account-example"
        ET.SubElement(node, "email").text = "example@example.invalid"
    archive = tmp_path / "actual-export.zip"
    with ZipFile(archive, "w") as output:
        output.writestr("annotations.xml", ET.tostring(root, encoding="utf-8"))
    before = verify(package)["frames"]
    result = record(archive, package / "server_snapshot.json", package / "frame_mapping.csv", package)
    assert result["frames"] == before
    assert not result["human_review_confirmed"]
    assert result["operator"] == "AI:Codex"
    saved = ET.parse(package / "annotations.xml").getroot()
    assert saved.find("meta/job/owner") is None
    assert saved.find("meta/job/assignee") is None
    assert "private-account-example" not in (package / "annotations.xml").read_text()
    assert (package / "index.html").read_text().count("<article>") == 20


class Images(HTMLParser):
    def __init__(self):
        super().__init__()
        self.images = []

    def handle_starttag(self, tag, attrs):
        if tag == "img":
            self.images.append(dict(attrs))


def test_five_slides_embed_actual_cvat_screenshots_and_regenerate_exactly():
    text = Path("demo/t004_demo.html").read_text()
    assert text == render_demo(json.loads(Path("reports/analysis_summary.json").read_text()), verify())
    assert len(re.findall(r'<section id="s\d+">', text)) == 5
    parser = Images()
    parser.feed(text)
    evidence = [img for img in parser.images if "data-evidence" in img]
    assert {img["data-evidence"] for img in evidence} == {
        "ui/01-workspace.png", "ui/02-overrides.png", "cvat/03-save-verify.jpg", "cvat/04-export-dialog.jpg",
        "cvat/05-export-finished.jpg", "cvat/06-summary.jpg",
    }
    for img in evidence:
        assert base64.b64decode(img["src"].split(",", 1)[1]) == (Path("demo") / img["data-evidence"]).read_bytes()
    assert "Vũ Duy Khanh" in text and "Vũ Duy Khánh" not in text
    assert not re.search(r'(?:src|href)="https?://', text)
    gallery = Path("demo/cvat/index.html").read_text()
    assert gallery.count("<article>") == 20
    assert all((Path("demo/cvat") / link).is_file() for link in re.findall(r'src="([^"]+)"', gallery))
