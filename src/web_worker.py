"""Execute one real pipeline stage in a guarded subprocess and commit a revision."""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from . import pipeline
from .common.context import RunContext
from .common.decision import write_decision
from .common.gt_guard import enable_gt_guard
from .common.io import read_json, set_seed, sha256_file, write_json
from .common.offline import enable_offline_guard
from .common.review import AuditLog, REVIEW_COLUMNS

STEPS = ('load', 'process', 'rank', 'review', 'decide')
EDITABLE = ('reviewer_decision', 'override_value', 'review_note')


def now():
    return datetime.now(timezone.utc).isoformat(timespec='microseconds')


def current_revision(run_dir):
    revision=read_json(run_dir/'current.json')['revision']
    return revision, run_dir/'revisions'/f'{revision:06d}'


def read_table(directory, name):
    return pd.read_csv(directory/name, keep_default_na=False, float_precision='round_trip')


def check_transition(state, stage):
    if stage not in STEPS:
        raise ValueError('Bước pipeline không hợp lệ.')
    index=STEPS.index(stage)
    if index and not state['steps'][STEPS[index-1]]['done']:
        raise ValueError(f'Cần hoàn tất {STEPS[index-1].title()} trước.')
    if index<3 and state['steps'][stage]['done']:
        raise ValueError('Bước này đã chạy. Tạo lượt mới để xử lý lại dữ liệu.')


def review_entries(queue, payload, previous, previous_confirmed):
    reviewer=payload.get('reviewer','')
    confirmed=payload.get('human_confirmed',False)
    entries=payload.get('rows')
    if not isinstance(reviewer,str) or not reviewer.strip() or len(reviewer)>120:
        raise ValueError('Nhập tên người review (tối đa 120 ký tự).')
    if type(confirmed) is not bool:
        raise ValueError('Trạng thái xác nhận không hợp lệ.')
    if confirmed and reviewer.upper().startswith('AI:'):
        raise ValueError('Tên reviewer không phù hợp với xác nhận trực tiếp.')
    if not isinstance(entries,list) or len(entries)!=len(queue):
        raise ValueError('Cần gửi đủ mỗi frame một lần.')
    by_id={}
    for entry in entries:
        if not isinstance(entry,dict) or set(entry)!={'item_id',*EDITABLE}:
            raise ValueError('Chỉ được sửa quyết định, override và nhận xét.')
        if any(not isinstance(v,str) for v in entry.values()) or any(len(v)>4000 for v in entry.values()):
            raise ValueError('Trường review phải là văn bản, tối đa 4000 ký tự.')
        if entry['item_id'] in by_id:
            raise ValueError('ID frame bị trùng.')
        by_id[entry['item_id']]=entry
    if set(by_id)!=set(queue.item_id):
        raise ValueError('ID review phải khớp queue hiện tại.')
    old={row['item_id']:row for row in previous}
    result=[]
    for row in queue.fillna('').astype(str).to_dict('records'):
        incoming=by_id[row['item_id']]
        decision=incoming['reviewer_decision']
        if decision not in ('','approve','edit','reject','escalate','skip'):
            raise ValueError('Quyết định review không hợp lệ.')
        if decision in ('edit','reject'):
            if incoming['override_value'] not in ('KEEP','RECAPTURE') or not incoming['review_note'].strip():
                raise ValueError('Sửa/từ chối cần KEEP hoặc RECAPTURE và nhận xét.')
        elif incoming['override_value']:
            raise ValueError('Chỉ sửa hoặc từ chối mới có override.')
        current=row | incoming | {'reviewer':reviewer.strip() if decision else '', 'reviewed_at':''}
        prior=old.get(row['item_id'])
        same=prior and previous_confirmed==confirmed and all(prior.get(k,'')==current[k] for k in (*EDITABLE,'reviewer'))
        current['reviewed_at']=(prior['reviewed_at'] if same else now()) if decision else ''
        result.append(current)
    return pd.DataFrame(result)[REVIEW_COLUMNS],confirmed


def run_stage(run_dir, stage, payload):
    revision,previous_dir=current_revision(run_dir)
    if type(payload.get('revision')) is not int or payload['revision']!=revision:
        raise ValueError('Dữ liệu đã thay đổi ở tab khác. Tải lại trước khi lưu.')
    state=read_json(previous_dir/'workflow.json')
    check_transition(state,stage)
    started=now();timer=time.perf_counter()
    staging=Path(tempfile.mkdtemp(prefix='.stage-',dir=run_dir))
    try:
        shutil.copytree(previous_dir,staging,dirs_exist_ok=True)
        config=read_json(staging/'config.json')
        ctx=RunContext('t02',Path(state['input_dir']),staging,config,42,set_seed(42),
                       run_name='web',offline=True,audit=AuditLog(staging/'audit_log.jsonl'),stats=state['stats'].copy())
        if stage=='load':
            data=pipeline.load(ctx)
            data['images'].to_csv(ctx.out('loaded_images.csv'),index=False)
            data['manifest'].to_csv(ctx.out('loaded_manifest.csv'),index=False)
            state['input_hashes']={r['path']:r['sha256'] for r in data['manifest'].to_dict('records')}
            ctx.stats['n_items']=len(data['images'])
        else:
            # The loaded snapshot must still describe the pixels being processed/reviewed.
            for relative,digest in state['input_hashes'].items():
                if sha256_file(pipeline._inside(ctx.input_dir,relative))!=digest:
                    raise ValueError('Dữ liệu đầu vào đã đổi sau Load. Tạo lượt mới để kiểm lại.')
            raw=read_table(staging,'raw_predictions.csv') if (staging/'raw_predictions.csv').exists() else None
            if stage=='process':
                data={'images':read_table(staging,'loaded_images.csv'),'manifest':read_table(staging,'loaded_manifest.csv')}
                scored=pipeline.process(ctx,data)
                scored.to_csv(ctx.out('raw_predictions.csv'),index=False)
                ctx.stats.update(n_items=len(scored),algorithm='multifeature_v1')
            elif stage=='rank':
                pipeline.rank(ctx,raw)
            elif stage=='review':
                queue=read_table(staging,'review_queue.csv')
                prior=pd.read_csv(staging/'review_queue_reviewed.csv',dtype=str).fillna('').to_dict('records') if (staging/'review_queue_reviewed.csv').exists() else []
                if payload.get('source')=='confirmed':
                    from tools.t02_human_review import verify_confirmation, signed_rows
                    from tools.t02_cvat_demo import verify
                    receipt=verify_confirmation()
                    reviewed=pd.DataFrame(signed_rows(verify(),receipt))
                    immutable=[c for c in REVIEW_COLUMNS if c not in (*EDITABLE,'reviewer','reviewed_at')]
                    if not reviewed[immutable].astype(str).equals(queue[immutable].astype(str)):
                        raise ValueError('Xác nhận đã lưu không thuộc queue hiện tại.')
                    # A matching ID/score is insufficient if its pixels changed.
                    for row in queue.to_dict('records'):
                        reference=Path('fixtures/t02_raw_qc')/row['evidence_path']
                        if state['input_hashes'][row['evidence_path']]!=sha256_file(reference):
                            raise ValueError('Ảnh không khớp bằng chứng đã xác nhận.')
                    config['human_review_confirmed']=True
                    config['owner']=receipt['reviewer']+' — T004 / reviewer'
                    state['review_source']='confirmed_cvat'
                    write_json(staging/'review_confirmation.json',receipt | {'imported_at':now()})
                else:
                    reviewed,confirmed=review_entries(queue,payload,prior,config.get('human_review_confirmed',False))
                    config['human_review_confirmed']=confirmed
                    config['owner']=payload['reviewer'].strip()+' — T004 / reviewer'
                    state['review_source']='web_form'
                    write_json(staging/'review_confirmation.json',{
                        'source':'web_form', 'reviewer':payload['reviewer'].strip(),
                        'human_review_confirmed':confirmed, 'saved_at':now(),
                        'scope':'Current queue decisions submitted with the review form',
                        'item_ids':[r['item_id'] for r in payload['rows'] if r['reviewer_decision'] in ('approve','edit','reject')],
                    })
                reviewed.to_csv(ctx.out('review_queue_reviewed.csv'),index=False)
                previous_rows={r['item_id']:r for r in prior}
                for row in reviewed.to_dict('records'):
                    old=previous_rows.get(row['item_id'])
                    if old and old['reviewer_decision'] and not row['reviewer_decision']:
                        ctx.audit.log(config['owner'],'review:clear',row['item_id'],
                                      before=old['override_value'] or old['suggested_action'],
                                      after='unreviewed',reason=row['review_note'],human_confirmed=False)
                write_json(staging/'config.json',config)
                ctx.config=config
                final=pipeline.review(ctx,raw,queue)
                final.to_csv(ctx.out('ranked_review.csv'),index=False)
                final[['image_id','raw_action','pred_action','review_state','reviewer']].to_csv(ctx.out('item_decisions.csv'),index=False)
                state['steps']['decide']={'done':False}
                state['decision']=None
                (staging/'decision.json').unlink(missing_ok=True)
            elif stage=='decide':
                final=read_table(staging,'ranked_review.csv')
                decision=pipeline.decide(ctx,final)
                write_decision(decision,ctx.out('decision.json'),ctx.out('decision_log.csv'))
                state['decision']=read_json(staging/'decision.json')
        finished=now();seconds=round(time.perf_counter()-timer,4)
        state['stats']=ctx.stats
        state['human_confirmed']=bool(config.get('human_review_confirmed',False))
        state['owner']=config['owner']
        state['steps'][stage]={'done':True,'started_at':started,'finished_at':finished,'runtime_seconds':seconds}
        # A process interrupted just before pointer publication may leave an
        # orphan revision. Keep it intact and publish the next unused number.
        next_revision=max(int(p.name) for p in (run_dir/'revisions').iterdir() if p.name.isdigit())+1
        state['revision']=next_revision
        state['updated_at']=finished
        state['history'].append({'stage':stage,'revision':next_revision,'at':finished,'runtime_seconds':seconds})
        ctx.audit.log('pipeline','web:'+stage,state['run_id'],after=next_revision,reason='Interactive web stage completed')
        write_json(staging/'workflow.json',state)
        write_json(staging/'run_info.json',{'track':'t02','run_name':'web','seed':42,'offline':True,'status':0,
                    'stage':stage,'revision':next_revision,'stats':ctx.stats,'runtime_seconds':seconds,
                    'pipeline':'src.pipeline','input':str(ctx.input_dir)})
        destination=run_dir/'revisions'/f'{next_revision:06d}'
        staging.rename(destination)
        pointer=run_dir/'current.tmp'
        write_json(pointer,{'revision':next_revision})
        pointer.replace(run_dir/'current.json')
        return state
    finally:
        if staging.exists():shutil.rmtree(staging)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir',type=Path,required=True)
    parser.add_argument('--stage',choices=STEPS,required=True)
    args=parser.parse_args()
    enable_gt_guard();enable_offline_guard()
    try:
        run_stage(args.run_dir,args.stage,json.load(sys.stdin))
    except (ValueError,KeyError,OSError,TypeError) as error:
        print(json.dumps({'error':str(error)},ensure_ascii=False))
        return 2
    print(json.dumps({'ok':True}))
    return 0


if __name__=='__main__':raise SystemExit(main())
