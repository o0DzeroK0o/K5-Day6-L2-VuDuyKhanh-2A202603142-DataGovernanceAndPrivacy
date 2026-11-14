"""T004 / T02: input-only quality triage; frozen dev thresholds, offline review."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import UnidentifiedImageError

from .common.contact_sheet import render_contact_sheet
from .common.context import RunContext
from .common.decision import Decision, write_decision
from .common.image_ops import brightness_stats, laplacian_variance, load_rgb, to_gray
from .common.manifest import verify_manifest
from .common.review import apply_overrides, load_review_decisions, make_review_queue, write_review_queue


def _inside(root: Path, relative: str) -> Path:
    path = (root / relative).resolve()
    if Path(relative).is_absolute() or not path.is_relative_to(root.resolve()):
        raise ValueError(f"input path must remain inside input directory: {relative}")
    return path


def load(ctx: RunContext) -> dict:
    if ctx.track != "t02":
        raise NotImplementedError("T004 pipeline supports T02 only")
    manifest_path = ctx.input_dir / "manifest.csv"
    manifest = pd.read_csv(manifest_path, dtype=str)
    if "path" not in manifest or manifest.path.isna().any() or manifest.path.duplicated().any():
        raise ValueError("manifest requires unique nonempty paths")
    for path in manifest.path:
        _inside(ctx.input_dir, path)
    problems = verify_manifest(manifest_path)
    if problems:
        raise ValueError(f"provenance check failed: {problems[:3]}")
    images = pd.read_csv(ctx.input_dir / "images.csv", dtype=str)
    columns = ["image_id", "path", "camera_id", "light", "split"]
    if not set(columns).issubset(images):
        raise ValueError(f"images.csv requires columns {columns}")
    if images.empty or images[columns].isna().any().any():
        raise ValueError("images.csv is empty or has missing metadata")
    if images.image_id.duplicated().any() or images.path.duplicated().any():
        raise ValueError("duplicate image_id or path")
    covered = set(manifest.path)
    if "images.csv" not in covered or not set(images.path).issubset(covered):
        raise ValueError("all inputs, including images.csv, must be covered by manifest")
    for path in images.path:
        _inside(ctx.input_dir, path)
    ctx.audit.log("pipeline", "manifest_verified", "t02", after=len(images))
    return {"images": images, "manifest": manifest}


def image_features(rgb: np.ndarray) -> dict:
    """Pixel features only: 8-pixel JPEG boundary ratio + overlapping road tiles."""
    g = to_gray(rgb)
    if min(g.shape) < 32:
        raise ValueError("images must be at least 32x32 for quality features")
    dx, dy = np.abs(np.diff(g, axis=1)), np.abs(np.diff(g, axis=0))
    bx, by = np.arange(1, g.shape[1]) % 8 == 0, np.arange(1, g.shape[0]) % 8 == 0
    boundary = (float(dx[:, bx].mean()) + float(dy[by].mean())) / 2
    interior = (float(dx[:, ~bx].mean()) + float(dy[~by].mean())) / 2
    # Upper sky is excluded; sliding 32x32 road tiles catch local blown highlights.
    starts_y = range(min(g.shape[0] // 3, g.shape[0] - 32), g.shape[0] - 31, 16)
    local_sat = max(float((g[y:y+32, x:x+32] > 245).mean())
                    for y in starts_y for x in range(0, g.shape[1] - 31, 16))
    return {"sharpness": laplacian_variance(rgb), **brightness_stats(rgb),
            "blockiness": boundary / max(interior, 1.0), "roi_saturation": local_sat}


def score_features(features: dict, camera: str, light: str, params: dict, baseline=False) -> dict:
    if baseline:
        cutoff = float(params["baseline_laplacian_threshold"])
        value = cutoff / (cutoff + features["sharpness"])
        return {"score": value, "pred_defect_type": "blur" if value >= .5 else "none",
                "reason": "global_laplacian", "pred_action": "RECAPTURE" if value >= .5 else "KEEP",
                "unknown_domain": False}
    cameras, lights = params["sharpness_thresholds"], params["brightness_thresholds"]
    unknown = camera not in cameras or light not in lights
    sharp = float(cameras.get(camera, params["unknown_camera_threshold"]))
    bright = float(lights.get(light, params["unknown_light_threshold"]))
    glare = float(params["roi_saturation_threshold"])
    block = float(params["blockiness_threshold"])
    components = {
        "blur": sharp / (sharp + features["sharpness"]),
        "dark": bright / (bright + features["mean"]),
        "glare": features["roi_saturation"] / (features["roi_saturation"] + glare),
        "compression": features["blockiness"]**2 / (features["blockiness"]**2 + block**2),
    }
    if params.get("ablation") == "no_roi":
        components["glare"] = 0.0
    elif params.get("ablation") == "global_thresholds":
        components["blur"] = float(params["baseline_laplacian_threshold"]) / (float(params["baseline_laplacian_threshold"]) + features["sharpness"])
        components["dark"] = float(lights["day"]) / (float(lights["day"]) + features["mean"])
    defect = max(components, key=components.get)
    score = components[defect]
    return {"score": score, "pred_defect_type": defect if score >= .5 else "none",
            "reason": f"{defect};camera={camera};light={light}",
            "pred_action": "RECAPTURE" if score >= .5 else "KEEP", "unknown_domain": unknown,
            **{f"score_{k}": v for k, v in components.items()}}


def process(ctx: RunContext, data: dict, baseline=False) -> pd.DataFrame:
    params = ctx.config["params"]
    required = [params["baseline_laplacian_threshold"], params["roi_saturation_threshold"],
                params["blockiness_threshold"], params["unknown_camera_threshold"], params["unknown_light_threshold"],
                *params["sharpness_thresholds"].values(), *params["brightness_thresholds"].values()]
    if not all(np.isfinite(v) and v > 0 for v in required):
        raise ValueError("quality thresholds must be finite and positive")
    rows = []
    for r in data["images"].to_dict("records"):
        try:
            features = image_features(load_rgb(_inside(ctx.input_dir, r["path"])))
        except (UnidentifiedImageError, OSError) as exc:
            raise ValueError(f"unreadable image: {r['image_id']}") from exc
        rows.append(r | features | score_features(features, r["camera_id"], r["light"], params, baseline))
    scored = pd.DataFrame(rows).sort_values(["score", "image_id"], ascending=[False, True], kind="mergesort").reset_index(drop=True)
    scored["raw_action"] = scored.pred_action
    return scored


def rank(ctx: RunContext, scored: pd.DataFrame) -> pd.DataFrame:
    split = str(ctx.param("review_split", "eval"))
    pool = scored if split == "all" else scored[scored.split == split]
    budget = int(ctx.param("budget", 20))
    if budget <= 0 or pool.empty:
        raise ValueError("review budget must be positive and selected pool nonempty")
    q = make_review_queue(pool, "image_id", "score", budget, reason_col="reason", action_col="pred_action",
                          slice_col="light", evidence_col="path")
    write_review_queue(q, ctx.out("review_queue.csv"))
    render_contact_sheet(q, ctx.out("contact_sheet.html"), image_root=ctx.input_dir,
                         title=f"T004 / T02 — {ctx.run_name} — {split} — review")
    ctx.stats.update(review_pool=len(pool), review_budget=budget, review_split=split, queue_size=len(q))
    return q


def review(ctx: RunContext, scored: pd.DataFrame, queue: pd.DataFrame) -> pd.DataFrame:
    final = scored.copy()
    final["review_state"] = "unreviewed"
    final["reviewer"] = ""
    path = ctx.output_dir / "review_queue_reviewed.csv"
    ctx.stats.update(n_reviewed=0, n_human_reviewed=0, n_escalated=0)
    if not path.exists():
        return final
    reviewed = load_review_decisions(path)
    if reviewed.item_id.duplicated().any() or not set(reviewed.item_id).issubset(set(queue.item_id)):
        raise ValueError("review IDs must be unique and belong to current top-B queue")
    current = queue.set_index("item_id")
    for r in reviewed.itertuples():
        if not np.isfinite(float(r.score)) or not np.isclose(float(r.score), current.loc[r.item_id, "score"], atol=1e-6, rtol=0):
            raise ValueError("stale review score; review the current queue")
        if r.suggested_action != current.loc[r.item_id, "suggested_action"]:
            raise ValueError("stale review suggestion")
        if r.reviewer_decision in {"edit", "reject"}:
            if r.override_value not in {"KEEP", "RECAPTURE"} or not r.review_note.strip():
                raise ValueError("edit/reject requires KEEP or RECAPTURE and a review note")
        elif r.override_value:
            raise ValueError("override_value is only allowed for edit/reject")
    # Log complete decisions once below, including before/after for overrides.
    final = apply_overrides(final, reviewed, "image_id", "pred_action")
    seen = {e.get("extra", {}).get("review_fingerprint") for e in ctx.audit.read()}
    for r in reviewed.to_dict("records"):
        mask = final.image_id == r["item_id"]
        closed = r["reviewer_decision"] in {"approve", "edit", "reject"}
        human = bool(ctx.config.get("human_review_confirmed", False)) and not r["reviewer"].upper().startswith("AI:")
        final.loc[mask, "review_state"] = ("human" if human else "ai") if closed else r["reviewer_decision"]
        final.loc[mask, "reviewer"] = r["reviewer"]
        if not closed:
            final.loc[mask, "pred_action"] = "HOLD"
        ctx.stats["n_reviewed"] += int(closed)
        ctx.stats["n_human_reviewed"] += int(closed and human)
        ctx.stats["n_escalated"] += int(r["reviewer_decision"] == "escalate")
        fingerprint = hashlib.sha256(json.dumps(r, sort_keys=True).encode()).hexdigest()
        if fingerprint not in seen:
            ctx.audit.log(r["reviewer"], "review:" + r["reviewer_decision"], r["item_id"],
                          before=final.loc[mask, "raw_action"].item(), after=final.loc[mask, "pred_action"].item(),
                          reason=r["review_note"], review_fingerprint=fingerprint, human_confirmed=human)
    return final


def decide(ctx: RunContext, final: pd.DataFrame) -> Decision:
    if ctx.stats.get("n_escalated", 0):
        status, code, reason = "HOLD", "REVIEW_ESCALATED", "Review có mẫu cần chủ dữ liệu xác nhận."
    elif ctx.stats.get("n_human_reviewed", 0) < ctx.stats["queue_size"]:
        status, code, reason = "HOLD", "HUMAN_REVIEW_REQUIRED", "Cần người thật xác nhận toàn bộ queue; AI review không phải chữ ký người dùng."
    elif final.unknown_domain.any():
        status, code, reason = "HOLD", "UNKNOWN_DOMAIN", "Camera/light ngoài miền dev cần đánh giá riêng."
    elif (final.pred_action == "RECAPTURE").any():
        status, code, reason = "REWORK", "QUALITY_RECAPTURE_REQUIRED", "Có ảnh cần thu lại; không release batch còn lỗi."
    else:
        status, code, reason = "GO", "TRIAGE_REVIEW_COMPLETE", "Hoàn tất triage trong budget; GO không chứng nhận ảnh ngoài queue hay tuân thủ pháp lý."
    return Decision(status=status, reason_code=code, reason=reason, owner=ctx.config["owner"], scope="T004:T02:triage",
                    evidence=["ranked_review.csv", "review_queue.csv", "audit_log.jsonl", "item_decisions.csv"], metrics=ctx.stats.copy())


def run_pipeline(ctx: RunContext, baseline=False) -> None:
    data = load(ctx)
    scored = process(ctx, data, baseline=baseline)
    ctx.stats.update(n_items=len(scored), algorithm="laplacian_baseline" if baseline else "multifeature_v1")
    # Immutable algorithm scores are used for evaluation, even after overrides.
    scored.to_csv(ctx.out("raw_predictions.csv"), index=False)
    queue = rank(ctx, scored)
    final = review(ctx, scored, queue)
    final.to_csv(ctx.out("ranked_review.csv"), index=False)
    final[["image_id", "raw_action", "pred_action", "review_state", "reviewer"]].to_csv(ctx.out("item_decisions.csv"), index=False)
    write_decision(decide(ctx, final), ctx.out("decision.json"), ctx.out("decision_log.csv"))


def run(ctx: RunContext) -> None:
    run_pipeline(ctx)
