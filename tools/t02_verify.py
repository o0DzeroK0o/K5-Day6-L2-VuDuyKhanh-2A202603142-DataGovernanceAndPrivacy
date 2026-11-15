"""Verify T004 submission evidence, report template and immutable score protocol."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from src.common.io import read_json, sha256_file, write_json
from src.common.manifest import verify_manifest
from src.metrics.tracks import eval_t02
from tools.t02_fill_report import TEMPLATE, validate_structure
from tools.t02_cvat_demo import verify as verify_cvat_demo
from tools.t02_cvat_review import verify_import as verify_cvat_import


def evidence_files():
    return sorted(p for root in (Path('reports'),Path('demo')) for p in root.rglob('*')
                  if p.is_file() and p!=Path('reports/evidence_manifest.json'))


def write_evidence_manifest():
    # Canonical LF avoids platform CSV newlines changing hashes after git checkout.
    for path in evidence_files():
        if path.suffix == '.csv':
            path.write_bytes(path.read_bytes().replace(b'\r\n', b'\n'))
    write_json('reports/evidence_manifest.json',{'algorithm':'sha256',
        'files':{str(p):sha256_file(p) for p in evidence_files()}})


def verify_evidence():
    problems=[]
    freeze=read_json('reports/protocol_freeze.json')
    for name,digest in freeze['hashes'].items():
        target={'configs/lab.yaml':'reports/protocol_config.yaml', 'reports/metric_contract.md':'reports/protocol_metric_contract.md'}.get(name,name)
        if sha256_file(target)!=digest:problems.append(f'frozen file changed: {name}')
    def contract_rows(path):
        return [[c.strip() for c in line.split('|')] for line in Path(path).read_text().splitlines()
                if line.startswith('|') and 'Ngày giờ chốt + người chốt' not in line
                and not set(line.replace('|','').replace(' ','')) <= {'-'}]
    if contract_rows('reports/metric_contract.md') != contract_rows('reports/protocol_metric_contract.md'):
        problems.append('current metric contract changed technical declarations')
    cfg=yaml.safe_load(Path('configs/lab.yaml').read_text())
    frozen=yaml.safe_load(Path('reports/protocol_config.yaml').read_text())
    if cfg['params']!=frozen['params']:problems.append('frozen scoring params changed')
    if cfg['group_id']!='T004' or cfg['track']!='t02':problems.append('wrong group/track')
    if verify_manifest('fixtures/t02_raw_qc/manifest.csv'):problems.append('input manifest failed')
    labels=Path('reports/annotations/internal_eval_labels.csv')
    for name in ('baseline','poc','no_roi','global_thresholds'):
        d=Path('reports/evidence')/name
        raw=pd.read_csv(d/'raw_predictions.csv');pred=pd.read_csv(d/'ranked_review.csv')
        if not raw[['image_id','score','pred_defect_type']].equals(pred[['image_id','score','pred_defect_type']]):
            problems.append(f'{name}: review changed immutable algorithm predictions')
        if pred.image_id.duplicated().any() or not np.isfinite(pred.score).all():
            problems.append(f'{name}: invalid predictions')
        result=eval_t02(labels,d/'ranked_review.csv',{'budget':20,'split':'eval'})
        actual={(m.name,m.slice):(m.value,m.numerator,m.denominator,m.n) for m in result.metrics}
        saved=read_json(f'reports/metrics_{name}.json')
        expected={(m['name'],m['slice']):(m['value'],m['numerator'],m['denominator'],m['n']) for m in saved['metrics']}
        if actual!=expected:problems.append(f'{name}: metrics differ from shared evaluator')
        run=read_json(d/'run_info.json')
        if run['status']!=0 or not run['offline'] or run['seed']!=42:problems.append(f'{name}: runner failed offline/seed contract')
    try:validate_structure(TEMPLATE.read_text(),Path('reports/group_report.md').read_text())
    except ValueError as e:problems.append(str(e))
    if '____' in Path('reports/group_report.md').read_text():problems.append('report contains unfilled answer slots')
    for doc in [Path('docs/README.md'),Path('docs/HUONG_DAN_HOAN_TAT_T004.md'),Path('reports/group_report.md')]:
        for link in re.findall(r'\]\(([^)]+)\)',doc.read_text()):
            if '://' not in link and not (doc.parent/link.split('#')[0]).exists():problems.append(f'broken link: {doc}: {link}')
    q=pd.read_csv('reports/review_queue.csv')
    if len(q)!=20 or q.item_id.duplicated().any() or q.reviewer.isna().any():problems.append('review evidence incomplete')
    contribution=pd.read_csv('reports/team_contributions.csv')
    if len(contribution)!=1 or contribution.git_author_name.isna().any() or contribution.commit_shas.isna().any():
        problems.append('one-member contribution evidence incomplete')
    try:verify_cvat_demo()
    except (ValueError, KeyError, OSError) as e:problems.append(f'CVAT demo: {e}')
    try:verify_cvat_import()
    except (ValueError, KeyError, OSError) as e:problems.append(f'CVAT review import: {e}')
    from tools.t02_web_demo import verify as verify_web
    try:verify_web()
    except (ValueError, KeyError, OSError) as e:problems.append(f'Web pipeline demo: {e}')
    manifest=Path('reports/evidence_manifest.json')
    if manifest.exists():
        expected=read_json(manifest)['files']
        actual={str(p):sha256_file(p) for p in evidence_files()}
        for name in sorted(set(actual)|set(expected)):
            if actual.get(name)!=expected.get(name):problems.append(f'evidence hash mismatch: {name}')
    else:problems.append('missing evidence_manifest.json')
    return problems


def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write-manifest',action='store_true');a=ap.parse_args(argv)
    if a.write_manifest:write_evidence_manifest()
    problems=verify_evidence()
    for p in problems:print('FAIL',p)
    if not problems:print('PASS: frozen protocol, evaluator metrics, immutable scores, report template, links, contributions, 20 CVAT frames and evidence hashes')
    print('Human review confirmed for 20 queue frames. Official GT, classroom tag timing and remote submission remain unverified.')
    return int(bool(problems))


if __name__=='__main__':raise SystemExit(main())
