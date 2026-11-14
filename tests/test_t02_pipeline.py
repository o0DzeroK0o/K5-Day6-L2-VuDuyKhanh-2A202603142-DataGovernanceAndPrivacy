"""T004 tests: actual pixel defects, protocol boundaries, overrides and failures."""
import json
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src import main as runner
from src.common.context import RunContext
from src.common.io import resolve_config
from src.common.review import AuditLog
from src.pipeline import decide, image_features, load, rank, review, score_features


@pytest.fixture
def ctx(tmp_path):
    return RunContext("t02", Path("fixtures/t02_raw_qc"), tmp_path, resolve_config("configs/lab.yaml"),
                      42, np.random.default_rng(42), audit=AuditLog(tmp_path / "audit_log.jsonl"))


def test_offline_repeatable_complete_contract(tmp_path):
    for name in ("a", "b"):
        assert runner.main(["--output", str(tmp_path/name), "--offline", "--seed", "42"]) == 0
    a, b = tmp_path/"a", tmp_path/"b"
    assert (a/"ranked_review.csv").read_bytes() == (b/"ranked_review.csv").read_bytes()
    ranked = pd.read_csv(a/"ranked_review.csv")
    queue = pd.read_csv(a/"review_queue.csv")
    assert ranked.image_id.nunique() == len(ranked) == 96
    assert np.isfinite(ranked.score).all() and len(queue) == 20
    assert set(queue.item_id) <= set(ranked.loc[ranked.split == "eval", "image_id"])
    assert (a/"contact_sheet.html").read_text().count('class="card"') == 20
    d = json.loads((a/"decision.json").read_text())
    assert d["status"] == "HOLD" and d["reason_code"] == "HUMAN_REVIEW_REQUIRED"


def test_pixel_features_local_glare_and_blur(ctx):
    clean = np.zeros((64,64,3), dtype=np.uint8) + 70
    glare = clean.copy(); glare[32:56,16:40] = 255
    a, b = image_features(clean), image_features(glare)
    assert b["roi_saturation"] > .1 and a["roi_saturation"] == 0
    assert score_features(a,"cam_A","day",ctx.config["params"])["pred_defect_type"] == "blur"
    assert image_features(np.zeros((32,32,3), dtype=np.uint8))["blockiness"] == 0
    with pytest.raises(ValueError, match="32x32"):
        image_features(np.zeros((10,10,3)))


def test_camera_light_conditioning_and_ablation(ctx):
    features = dict(sharpness=200., mean=32., roi_saturation=0., blockiness=1.)
    params = ctx.config["params"]
    assert score_features(features,"cam_B","night",params)["pred_action"] == "KEEP"
    assert score_features(features,"cam_B","night",params,baseline=True)["pred_action"] == "RECAPTURE"
    assert score_features(features,"cam_B","night",params|{"ablation":"global_thresholds"})["pred_action"] == "RECAPTURE"
    assert score_features(features,"new_camera","night",params)["unknown_domain"]


def test_tampered_input_rejected_before_scoring(ctx, tmp_path):
    dest = tmp_path/"input"
    shutil.copytree(ctx.input_dir,dest)
    (dest/"images/img_00_0.jpg").write_bytes(b"tampered")
    ctx.input_dir=dest
    with pytest.raises(ValueError,match="provenance"):
        load(ctx)


def test_manifest_cannot_escape_input(ctx,tmp_path):
    dest=tmp_path/"input";dest.mkdir()
    pd.DataFrame({"path":["../outside.jpg"]}).to_csv(dest/"manifest.csv",index=False)
    ctx.input_dir=dest
    with pytest.raises(ValueError,match="inside input"):
        load(ctx)


def _scored(ctx):
    return pd.DataFrame({"image_id":["a","b"], "path":["images/img_00_0.jpg","images/img_00_1.jpg"],
                         "split":["eval","eval"],"score":[.8,.7],"reason":["blur","glare"],
                         "pred_action":["RECAPTURE","RECAPTURE"],"raw_action":["RECAPTURE","RECAPTURE"],
                         "light":["day","day"],"unknown_domain":[False,False]})


def _reviewed(ctx,scored):
    queue=rank(ctx,scored)
    reviewed=queue.copy()
    reviewed["reviewer"]="AI:Codex"
    reviewed["reviewer_decision"]="approve"
    reviewed.loc[0,["reviewer_decision","override_value","review_note"]]=["edit","KEEP","Visual check: still useful"]
    return queue,reviewed


def test_override_audited_scores_immutable_ai_does_not_sign(ctx):
    scored=_scored(ctx);queue,reviewed=_reviewed(ctx,scored)
    reviewed.to_csv(ctx.out("review_queue_reviewed.csv"),index=False)
    final=review(ctx,scored,queue)
    assert final.loc[0,"pred_action"]=="KEEP" and scored.loc[0,"pred_action"]=="RECAPTURE"
    assert final.score.equals(scored.score)
    assert len([e for e in ctx.audit.read() if e["action"].startswith("review:")])==2
    review(ctx,scored,queue)
    assert len([e for e in ctx.audit.read() if e["action"].startswith("review:")])==2
    ctx.config["human_review_confirmed"]=True
    final=review(ctx,scored,queue)
    assert decide(ctx,final).status=="HOLD" and ctx.stats["n_human_reviewed"]==0


@pytest.mark.parametrize("case",["unknown","duplicate","stale","bad_override","missing_reviewer","missing_note"])
def test_invalid_review_rejected(ctx,case):
    scored=_scored(ctx);queue,reviewed=_reviewed(ctx,scored)
    if case=="unknown": reviewed.loc[0,"item_id"]="foreign"
    if case=="duplicate": reviewed.loc[1,"item_id"]="a"
    if case=="stale": reviewed.loc[0,"score"]=.1
    if case=="bad_override": reviewed.loc[0,"override_value"]="DELETE"
    if case=="missing_reviewer": reviewed.loc[0,"reviewer"]=""
    if case=="missing_note": reviewed.loc[0,"review_note"]=""
    reviewed.to_csv(ctx.out("review_queue_reviewed.csv"),index=False)
    with pytest.raises(ValueError): review(ctx,scored,queue)


def test_human_review_and_escalation_gate(ctx):
    scored=_scored(ctx);queue,reviewed=_reviewed(ctx,scored)
    reviewed["reviewer"]="Test reviewer"
    ctx.config["human_review_confirmed"]=True
    reviewed.to_csv(ctx.out("review_queue_reviewed.csv"),index=False)
    final=review(ctx,scored,queue)
    assert decide(ctx,final).status=="REWORK"
    reviewed.loc[1,["reviewer_decision","review_note"]]=["escalate","Uncertain glare"]
    reviewed.to_csv(ctx.out("review_queue_reviewed.csv"),index=False)
    final=review(ctx,scored,queue)
    assert final.loc[1,"pred_action"]=="HOLD"
    assert decide(ctx,final).reason_code=="REVIEW_ESCALATED"
