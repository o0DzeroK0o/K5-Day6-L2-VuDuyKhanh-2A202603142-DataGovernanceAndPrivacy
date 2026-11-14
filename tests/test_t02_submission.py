import pandas as pd
import pytest

from tools.t02_submission import checked_labels, derive_summary, fixed_ranking_bootstrap, make_ai_review
from src.common.review import make_review_queue


def labels():
    return pd.DataFrame({"image_id":["a","b","c","d"],"is_defect":[1,0,1,0],
                         "scene_id":["s1","s1","s2","s2"],"light":["day"]*4,
                         "camera_id":["cam_A"]*4,"defect_type":["blur","none","glare","none"],"note":["visual"]*4})


def test_metrics_use_global_top_budget_not_new_budget_per_slice():
    g=labels();p=pd.DataFrame({"image_id":["a","c","b","d"],"score":[4,3,2,1]})
    s=derive_summary(g,{"poc":p},budget=2)
    assert s["runs"]["poc"]==dict(tp=2,fp=0,fn=0,recall=1.,precision=1.,false_positive_ids=[],false_negative_ids=[])
    ci=s["uncertainty"]["results"]["poc"]["ci95"]
    assert ci==[1.,1.]
    assert s["official"] is False


def test_bootstrap_is_paired_reproducible_and_handles_no_positives():
    g=labels();tops={"baseline":{"a","b"},"poc":{"a","c"}}
    a=fixed_ranking_bootstrap(g,tops,100)
    assert a==fixed_ranking_bootstrap(g,tops,100)
    assert a["results"]["paired_delta"]["ci95"][0]>=0
    g["is_defect"]=0
    assert fixed_ranking_bootstrap(g,tops,10)["results"]["poc"]["ci95"] is None


def test_ai_review_explicitly_names_ai_and_applies_visual_observation():
    pred=pd.DataFrame({"id":["a","b"],"score":[.8,.7],"suggestion":["KEEP","RECAPTURE"]})
    q=make_review_queue(pred,"id","score",2,action_col="suggestion")
    reviewed=make_ai_review(q,labels())
    assert set(reviewed.reviewer)=={"AI:Codex"}
    assert list(reviewed.override_value)==["RECAPTURE","KEEP"]
    assert set(reviewed.reviewer_decision)=={"edit"}


def test_labels_must_match_pool_without_duplicates():
    g=labels();inputs=pd.DataFrame({"image_id":["a","b","c","d"],"split":["eval"]*4})
    with pytest.raises(ValueError,match="exactly once"):
        checked_labels(pd.concat([g,g.iloc[[0]]]),inputs)
