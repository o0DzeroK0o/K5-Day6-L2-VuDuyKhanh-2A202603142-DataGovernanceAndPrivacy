"""Import verified CVAT tags into the frozen pipeline's review CSV and evidence.

The CVAT display name stays in source metadata. The pipeline reviewer identifies
its actual operator, so importing annotations cannot grant human sign-off.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from src.common.review import REVIEW_COLUMNS
from tools.t02_cvat_demo import QUEUE, digest, rows, verify

RECEIPT = Path("reports/cvat_review_import.json")
SYNC_FILES = ("review_queue_reviewed.csv", "audit_log.jsonl", "decision_log.csv",
              "decision.json", "run_info.json", "item_decisions.csv", "ranked_review.csv")


def review_rows(evidence):
    """Keep frozen queue fields and copy the saved observations verbatim."""
    result = []
    for item, frame in zip(rows(QUEUE), evidence["frames"]):
        changed = frame["action"] != item["suggested_action"]
        result.append(item | {
            "reviewer": evidence["operator"],
            "reviewer_decision": "edit" if changed else "approve",
            "override_value": frame["action"] if changed else "",
            "review_note": frame["review_note"],
            "reviewed_at": evidence["captured_at"],
        })
    return result


def csv_text(entries):
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, REVIEW_COLUMNS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(entries)
    return stream.getvalue()


def export_review(output, directory=Path("demo/cvat")):
    evidence = verify(directory)
    entries = review_rows(evidence)
    text = csv_text(entries)
    if output.exists() and output.read_text(encoding="utf-8") != text:
        previous = rows(output)
        if any(not row.get("reviewer", "").upper().startswith("AI:") for row in previous):
            raise ValueError("Existing review may contain human work; choose a new output file")
        backup = output.parent / "review_history" / f"{digest(output)}.csv"
        backup.parent.mkdir(parents=True, exist_ok=True)
        if not backup.exists():
            shutil.copy2(output, backup)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")
    return entries


def check_run(output, evidence, confirmation=None):
    human = confirmation is not None
    if human:
        from tools.t02_human_review import signed_rows
        expected = signed_rows(evidence, confirmation)
    else:
        expected = review_rows(evidence)
    reviewer = confirmation['reviewer'] if human else evidence['operator']
    if rows(output / "review_queue_reviewed.csv") != expected:
        raise ValueError("Pipeline review differs from saved CVAT observations")
    frozen = pd.read_csv(QUEUE.parent / "raw_predictions.csv", dtype=str).fillna("")
    raw = pd.read_csv(output / "raw_predictions.csv", dtype=str).fillna("")
    ranked = pd.read_csv(output / "ranked_review.csv", dtype=str).fillna("")
    if not raw.equals(frozen) or not ranked[["image_id", "score", "pred_defect_type"]].equals(raw[["image_id", "score", "pred_defect_type"]]):
        raise ValueError("CVAT import changed frozen algorithm predictions")
    items = pd.read_csv(output / "item_decisions.csv", dtype=str).fillna("").set_index("image_id")
    for row, frame in zip(expected, evidence["frames"]):
        item = items.loc[row["item_id"]]
        prediction = ranked.loc[ranked.image_id == row["item_id"]].iloc[0]
        if (item.pred_action != frame["action"] or prediction.pred_action != frame["action"]
                or item.reviewer != reviewer or item.review_state != ("human" if human else "ai")):
            raise ValueError("Final item action/provenance differs from CVAT")
    decision = json.loads((output / "decision.json").read_text())
    run = json.loads((output / "run_info.json").read_text())
    if (decision["metrics"]["n_reviewed"] != 20 or decision["metrics"]["n_human_reviewed"] != (20 if human else 0)
            or decision["status"] != ("REWORK" if human else "HOLD") or decision["reason_code"] != ("QUALITY_RECAPTURE_REQUIRED" if human else "HUMAN_REVIEW_REQUIRED")
            or not decision["owner"].startswith(evidence["review_source"])
            or run["status"] != 0 or not run["offline"] or run["seed"] != 42):
        raise ValueError("Invalid completed pipeline run or human sign-off")
    audit = [json.loads(line) for line in (output / "audit_log.jsonl").read_text().splitlines() if line]
    for row in expected:
        fingerprint = hashlib.sha256(json.dumps(row, sort_keys=True).encode()).hexdigest()
        events = [event for event in audit if event.get("extra", {}).get("review_fingerprint") == fingerprint]
        if (len(events) != 1 or events[0]["actor"] != reviewer
                or events[0]["item_id"] != row["item_id"]
                or events[0]["action"] != "review:" + row["reviewer_decision"]
                or events[0]["before"] != row["suggested_action"]
                or events[0]["after"] != (row["override_value"] or row["suggested_action"])
                or events[0]["reason"] != row["review_note"] or events[0]["extra"]["human_confirmed"] is not human):
            raise ValueError("Missing, duplicate or inconsistent CVAT review audit")
    return decision


def sync_report(output, directory=Path("demo/cvat")):
    from tools.t02_human_review import RECEIPT as HUMAN_RECEIPT
    if HUMAN_RECEIPT.exists():
        # Validate the candidate before refusing to supersede a later sign-off.
        check_run(output, verify(directory))
        for name in ("audit_log.jsonl", "decision_log.csv"):
            if not (output / name).read_text().startswith((QUEUE.parent / name).read_text()):
                raise ValueError(f"Refusing to replace prior append-only history: {name}")
        raise ValueError("A later human confirmation exists; keep this historical import unchanged")
    evidence = verify(directory)
    decision = check_run(output, evidence)
    # The previous review/audit remains in Git. Logs also retain their full prefix.
    for name in ("audit_log.jsonl", "decision_log.csv"):
        if not (output / name).read_text().startswith((QUEUE.parent / name).read_text()):
            raise ValueError(f"Refusing to replace prior append-only history: {name}")
    for name in SYNC_FILES:
        target = QUEUE.parent / name
        target.write_text((output / name).read_text(), encoding="utf-8")
    for source, name in (("review_queue_reviewed.csv", "review_queue.csv"),
                         ("audit_log.jsonl", "audit_log.jsonl"), ("decision_log.csv", "decision_log.csv")):
        shutil.copy2(QUEUE.parent / source, Path("reports") / name)
    entries = review_rows(evidence)
    receipt = dict(
        imported_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        task_id=evidence["task_id"], job_id=evidence["job_id"],
        annotation_sha256=evidence["annotation_sha256"], queue_sha256=evidence["queue_sha256"],
        review_source=evidence["review_source"], operator=evidence["operator"],
        human_review_confirmed=False, frame_count=20, action_counts=evidence["action_counts"],
        override_ids=[r["item_id"] for r in entries if r["reviewer_decision"] == "edit"],
        review_csv="reports/evidence/poc/review_queue_reviewed.csv",
        review_csv_sha256=digest(QUEUE.parent / "review_queue_reviewed.csv"),
        raw_predictions_sha256=digest(QUEUE.parent / "raw_predictions.csv"),
        status=decision["status"], reason_code=decision["reason_code"], owner=decision["owner"],
        note="Imported CVAT observations into review only; scoring and evaluation labels unchanged.",
    )
    RECEIPT.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    evidence["pipeline_imported"] = True
    evidence["pipeline_import_receipt"] = str(RECEIPT)
    (directory / "evidence.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    verify_import(directory)
    return receipt


def verify_import(directory=Path("demo/cvat")):
    evidence = verify(directory)
    if not evidence["pipeline_imported"]:
        raise ValueError("CVAT observations have not been imported")
    receipt = json.loads(RECEIPT.read_text())
    decision = check_run(QUEUE.parent, evidence)
    for key in ("task_id", "job_id", "annotation_sha256", "queue_sha256", "review_source", "operator", "human_review_confirmed", "frame_count", "action_counts"):
        if receipt[key] != evidence[key]:
            raise ValueError(f"Import receipt differs from CVAT: {key}")
    if (receipt["review_csv_sha256"] != digest(QUEUE.parent / "review_queue_reviewed.csv")
            or receipt["review_csv"] != str(QUEUE.parent / "review_queue_reviewed.csv")
            or evidence.get("pipeline_import_receipt") != str(RECEIPT)
            or receipt["override_ids"] != [r["item_id"] for r in review_rows(evidence) if r["reviewer_decision"] == "edit"]
            or receipt["raw_predictions_sha256"] != digest(QUEUE.parent / "raw_predictions.csv")
            or receipt["status"] != decision["status"] or receipt["reason_code"] != decision["reason_code"]
            or receipt["owner"] != decision["owner"]):
        raise ValueError("Import receipt differs from pipeline evidence")
    from tools.t02_human_review import RECEIPT as HUMAN_RECEIPT, verify_confirmation
    if HUMAN_RECEIPT.exists():
        verify_confirmation()
    elif (Path("reports/review_queue.csv").read_bytes() != (QUEUE.parent / "review_queue_reviewed.csv").read_bytes()
            or Path("reports/audit_log.jsonl").read_bytes() != (QUEUE.parent / "audit_log.jsonl").read_bytes()
            or Path("reports/decision_log.csv").read_bytes() != (QUEUE.parent / "decision_log.csv").read_bytes()):
        raise ValueError("Conventional report paths differ from CVAT pipeline evidence")
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--output", type=Path)
    group.add_argument("--sync-output", type=Path)
    args = parser.parse_args()
    if args.output:
        print(f"Exported {len(export_review(args.output))}/20 CVAT decisions to {args.output}")
    elif args.sync_output:
        receipt = sync_report(args.sync_output)
        print(f"Imported {receipt['frame_count']}/20 CVAT decisions; {receipt['status']} / {receipt['reason_code']}")
    else:
        receipt = verify_import()
        print(f"PASS: {receipt['frame_count']}/20 CVAT decisions match pipeline review, actions and audit")


if __name__ == "__main__":
    main()
