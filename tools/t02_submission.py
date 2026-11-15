"""Reproduce T004 evidence offline. Never trains or reads official GT in inference.

python -m tools.t02_submission --output out/reproduce --reports out/reproduce/reports
Saved CVAT observations are imported with their actual operator provenance.
Existing reviewed files are retained; this tool never signs on behalf of a human.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from src.common.io import read_json, resolve_config, sha256_file, write_json
from src.common.manifest import build_manifest, write_manifest
from src.common.review import REVIEW_COLUMNS
from tools.t02_cvat_review import export_review


LABELS = Path("reports/annotations/internal_eval_labels.csv")


def command(*args):
    subprocess.run([sys.executable, "-m", *map(str,args)], check=True)


def checked_labels(labels: pd.DataFrame, inputs: pd.DataFrame) -> None:
    expected = inputs.loc[inputs.split == "eval", "image_id"]
    if labels.image_id.duplicated().any() or set(labels.image_id) != set(expected):
        raise ValueError("internal labels must cover eval exactly once")
    if not set(labels.is_defect).issubset({0,1}):
        raise ValueError("is_defect must be binary")
    if not (labels.is_defect == labels.defect_type.ne("none").astype(int)).all():
        raise ValueError("defect_type/is_defect conflict")
    manifest = pd.read_csv("fixtures/t02_raw_qc/manifest.csv")
    scene_splits = manifest[manifest.path.str.startswith("images/")].groupby("group_id").split.nunique()
    if (scene_splits > 1).any():
        raise ValueError("scene leakage across dev/eval")


def make_ai_review(queue: pd.DataFrame, labels: pd.DataFrame) -> pd.DataFrame:
    q = queue.copy().fillna("")
    observations = labels.set_index("image_id")
    for idx,row in q.iterrows():
        label=observations.loc[row.item_id]
        target = "RECAPTURE" if label.is_defect else "KEEP"
        change = target != row.suggested_action
        q.loc[idx,"reviewer"] = "AI:Codex"
        q.loc[idx,"reviewer_decision"] = "edit" if change else "approve"
        q.loc[idx,"override_value"] = target if change else ""
        q.loc[idx,"review_note"] = "AI visual review, NOT human sign-off: " + label.note
        q.loc[idx,"reviewed_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return q[REVIEW_COLUMNS]


def fixed_ranking_bootstrap(labels: pd.DataFrame, top_sets: dict, repeats=2000, seed=42) -> dict:
    """Paired cluster bootstrap of fixed top-B contributions, not re-ranking."""
    groups=sorted(labels.scene_id.unique())
    positive=labels.is_defect.to_numpy(dtype=float)
    group_rows={g:np.flatnonzero(labels.scene_id.to_numpy()==g) for g in groups}
    contributions={name:labels.image_id.isin(top).to_numpy()*positive for name,top in top_sets.items()}
    rng=np.random.default_rng(seed)
    values={name:[] for name in top_sets}
    for _ in range(repeats):
        indices=np.concatenate([group_rows[g] for g in rng.choice(groups,len(groups),replace=True)])
        den=positive[indices].sum()
        if not den:
            continue
        for name,c in contributions.items():
            values[name].append(float(c[indices].sum()/den))
    result={name:{"ci95":np.quantile(v,[.025,.975]).tolist() if v else None,"valid_draws":len(v)} for name,v in values.items()}
    if "baseline" in values and "poc" in values:
        delta=np.array(values["poc"])-np.array(values["baseline"])
        result["paired_delta"]={"ci95":np.quantile(delta,[.025,.975]).tolist() if len(delta) else None}
    return {"method":"paired scene bootstrap of fixed ranking contributions (does not re-rank)","seed":seed,
            "repeats":repeats,"n_scenes":len(groups),"results":result,
            "limitations":"AI labels, same synthetic family; CI excludes annotation error and external domain shift"}


def derive_summary(labels: pd.DataFrame, predictions: dict, budget=20) -> dict:
    result={"label_source":str(LABELS),"official":False,"human_verified":False,"eval_n":len(labels),
            "positive_n":int(labels.is_defect.sum()),"budget":budget,"runs":{},"slices":[]}
    tops={}
    for name,pred in predictions.items():
        pool=pred[pred.image_id.isin(labels.image_id)].sort_values("score",ascending=False,kind="mergesort")
        top=set(pool.image_id.head(budget));tops[name]=top
        positive=set(labels.loc[labels.is_defect==1,"image_id"])
        result["runs"][name]={"tp":len(top&positive),"fp":len(top-positive),"fn":len(positive-top),
                               "recall":len(top&positive)/len(positive),"precision":len(top&positive)/min(budget,len(pool)),
                               "false_positive_ids":sorted(top-positive),"false_negative_ids":sorted(positive-top)}
        for column in ("light","camera_id","defect_type"):
            for value,sub in labels.groupby(column):
                pos=sub[sub.is_defect==1];neg=sub[sub.is_defect==0]
                result["slices"].append({"run":name,"slice":f"{column}={value}","n":len(sub),
                    "tp":int(pos.image_id.isin(top).sum()),"positive_n":len(pos),"fp":int(neg.image_id.isin(top).sum()),
                    "negative_n":len(neg),"recall":float(pos.image_id.isin(top).mean()) if len(pos) else None,
                    "false_alarm":float(neg.image_id.isin(top).mean()) if len(neg) else None})
    result["uncertainty"]=fixed_ranking_bootstrap(labels,tops)
    return result


def prepare_ood(output: Path) -> Path:
    root=output/"ood_input"; (root/"images").mkdir(parents=True,exist_ok=True)
    observations=pd.read_csv("reports/annotations/ood_visual_labels.csv")
    source=pd.read_csv("fixtures/t13_rare_mining/images.csv").sort_values("image_id").head(10)
    if list(source.image_id)!=list(observations.image_id):
        raise ValueError("OOD protocol selection changed")
    source=source.merge(observations[["image_id","light"]],on="image_id")
    source["camera_id"]="ood_T13";source["split"]="eval"
    for path in source.path:
        shutil.copy2(Path("fixtures/t13_rare_mining")/path,root/path)
    source.to_csv(root/"images.csv",index=False)
    manifest=build_manifest(root,["images.csv",*source.path],"synthetic:T13 cross-fixture OOD proxy","CC0-1.0",split="eval",group_id="T004")
    write_manifest(manifest,root/"manifest.csv")
    return root


def archive_tree(source: Path,dest: Path):
    dest.mkdir(parents=True,exist_ok=True)
    for path in source.iterdir():
        if path.is_file():
            shutil.copy2(path,dest/path.name)


def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output",default="out/reproduce")
    ap.add_argument("--reports",default="out/reproduce/reports")
    a=ap.parse_args(argv);out=Path(a.output);report=Path(a.reports)
    out.mkdir(parents=True,exist_ok=True);report.mkdir(parents=True,exist_ok=True)
    cfg=resolve_config("configs/lab.yaml")
    labels=pd.read_csv(LABELS)
    checked_labels(labels,pd.read_csv("fixtures/t02_raw_qc/images.csv"))
    predictions={}
    for name,module in (("baseline","src.t02_baseline"),("poc","src.pipeline"),("no_roi","src.pipeline"),("global_thresholds","src.pipeline")):
        config=Path("configs/lab.yaml")
        if name in {"no_roi","global_thresholds"}:
            config=out/f"config_{name}.yaml"
            c=json.loads(json.dumps(cfg));c.pop("track_config",None);c["params"]["ablation"]=name
            config.write_text(yaml.safe_dump(c,allow_unicode=True),encoding="utf-8")
        target=out/name
        command("src.main","--config",config,"--pipeline",module,"--output",target,"--run-name",name,"--offline","--seed","42")
        if name=="poc":
            reviewed=target/"review_queue_reviewed.csv"
            if not reviewed.exists():
                export_review(reviewed)
            command("src.main","--output",target,"--run-name",name,"--offline","--seed","42")
        command("src.evaluate","--track","t02","--gt",LABELS,"--pred",target/"ranked_review.csv",
                "--run-name",name,"--out",report/f"metrics_{name}.json","--slices-out",report/f"slices_{name}.csv")
        predictions[name]=pd.read_csv(target/"ranked_review.csv")
        archive_tree(target,report/"evidence"/name)
    command("src.compare",report/"metrics_baseline.json",report/"metrics_poc.json","--out",report/"table1_baseline_vs_poc.md")
    summary=derive_summary(labels,predictions)
    summary["protocol_sha256"]=sha256_file("reports/protocol_freeze.json")
    summary["labels_sha256"]=sha256_file(LABELS)
    write_json(report/"analysis_summary.json",summary)
    pd.DataFrame(summary["slices"]).to_csv(report/"detailed_slices.csv",index=False)
    root=prepare_ood(out)
    command("src.main","--input",root,"--output",out/"ood","--run-name","ood_proxy","--offline","--seed","42")
    ood=pd.read_csv(out/"ood/ranked_review.csv").merge(pd.read_csv("reports/annotations/ood_visual_labels.csv")[["image_id","is_defect","note"]],on="image_id")
    ood.to_csv(report/"ood_check.csv",index=False)
    write_json(report/"ood_summary.json",{"n":len(ood),"positive_n":int(ood.is_defect.sum()),
        "suggested_recapture":int((ood.pred_action=="RECAPTURE").sum()),"unknown_camera_n":int(ood.unknown_domain.sum()),
        "decision":read_json(out/"ood/decision.json")["status"],"recall":None,"official":False,
        "limitation":"10 clean synthetic cross-fixture images; no positives and no real-world coverage"})
    archive_tree(out/"ood",report/"evidence/ood")
    # Conventional evidence paths required by the handout.
    for source,name in (("review_queue_reviewed.csv","review_queue.csv"),("decision_log.csv","decision_log.csv"),("audit_log.jsonl","audit_log.jsonl"),("contact_sheet.html","contact_sheet.html")):
        shutil.copy2(out/"poc"/source,report/name)
    print(f"T004 evidence generated at {report}; saved CVAT review imported, real human sign-off still pending.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
