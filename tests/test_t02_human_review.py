"""Later human confirmation must preserve the earlier review and frozen predictions."""
import copy
import json
from pathlib import Path

import pytest

from tools import t02_human_review as human
from tools.t02_cvat_demo import verify, rows
from tools.t02_cvat_review import check_run


def test_confirmed_review_is_new_and_previous_cvat_import_is_unchanged():
    signed=human.verify_confirmation()
    assert signed['reviewer']=='Vũ Duy Khanh'
    assert signed['status']=='REWORK' and signed['human_review_confirmed']
    current=rows(human.EVIDENCE/'review_queue_reviewed.csv')
    assert len(current)==20 and {r['reviewer'] for r in current}=={'Vũ Duy Khanh'}
    old=rows('reports/evidence/poc/review_queue_reviewed.csv')
    assert {r['reviewer'] for r in old}=={'AI:Codex'}
    assert [r['review_note'] for r in current]==[r['review_note'] for r in old]
    assert check_run(Path('reports/evidence/poc'),verify())['status']=='HOLD'
    decision=check_run(human.EVIDENCE,verify(),signed)
    assert decision['metrics']['n_human_reviewed']==20


@pytest.mark.parametrize('field,value',[
    ('reviewer','Other'),('statement','Chỉ xem một phần'),('frame_count',19),
    ('item_ids',['img_23_1']),('override_ids',[]),('action_counts',{'KEEP':20}),
    ('human_review_confirmed',False),('confirmed_at','2020-01-01T00:00:00+00:00'),
    ('annotation_sha256','0'*64),
])
def test_incomplete_or_stale_signoff_is_rejected(field,value):
    record=json.loads(human.RECEIPT.read_text());record[field]=value
    with pytest.raises(ValueError):human.signed_rows(verify(),record)


def test_reproduction_uses_signed_review_and_will_not_overwrite_work(tmp_path):
    target=tmp_path/'review.csv';human.export_current_review(target)
    assert target.read_bytes()==(human.EVIDENCE/'review_queue_reviewed.csv').read_bytes()
    target.write_text('existing work\n')
    with pytest.raises(ValueError,match='Existing review differs'):human.export_current_review(target)
    assert target.read_text()=='existing work\n'


def test_forged_human_action_fails_even_when_original_import_is_valid(tmp_path):
    import shutil
    shutil.copytree(human.EVIDENCE,tmp_path/'run')
    record=json.loads(human.RECEIPT.read_text())
    path=tmp_path/'run/decision.json';data=json.loads(path.read_text());data['status']='GO';path.write_text(json.dumps(data))
    with pytest.raises(ValueError,match='sign-off'):check_run(tmp_path/'run',verify(),record)


def test_current_metric_contract_cannot_change_technical_policy(monkeypatch):
    from tools import t02_verify
    original=Path.read_text
    def read(path,*args,**kwargs):
        text=original(path,*args,**kwargs)
        return text.replace('B = 20','B = 21') if str(path)=='reports/metric_contract.md' else text
    monkeypatch.setattr(Path,'read_text',read)
    assert 'current metric contract changed technical declarations' in t02_verify.verify_evidence()
