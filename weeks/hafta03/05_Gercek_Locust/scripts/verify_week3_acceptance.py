"""Explicit live Locust dataset pass/fail gates (no results are fabricated).

A manifest alone is insufficient: counts are independently cross-checked by
streaming its paired JSONL. This proves internal consistency, not that HTTP
requests really occurred; run provenance requires saved Locust/Django logs.
"""
from __future__ import annotations
import argparse
import csv
import json
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
from backend.event_contract import valid_event
from backend.analysis import SCENARIOS

REQUIRED=set(SCENARIOS)


def check(manifest,minimum_events=120000,minimum_windows=1200,require_5seeds=True,events_path=None):
    path=Path(manifest)
    if not path.is_file():raise FileNotFoundError(path)
    with path.open('r',encoding='utf-8-sig',newline='') as f:
        rows=list(csv.DictReader(f))
    if not rows:raise ValueError('Empty Locust minute manifest')
    total=sum(int(r['request_count']) for r in rows)
    accepted=[r for r in rows if str(r['ambiguous']).lower() not in ('true','1') and r['split'] in ('train','validation','test')]
    seeds={int(r['seed']) for r in accepted}
    scenarios={r['scenario_code'] for r in accepted}
    splits=Counter(r['split'] for r in accepted)
    minute_keys=[r['minute_start_utc'] for r in rows]
    duplicates=len(minute_keys)-len(set(minute_keys))
    normalized_minutes={}
    for row in rows:
        try:
            dt=datetime.fromisoformat(row['minute_start_utc'].replace('Z','+00:00'))
            if dt.utcoffset() is None or dt.second or dt.microsecond:
                raise ValueError('Invalid UTC minute boundary')
            dt=dt.astimezone(timezone.utc)
            normalized_minutes[dt]=int(row['request_count'])
        except (ValueError,KeyError):
            duplicates+=1
    actual_counts=Counter();seen=set();invalid=0
    jsonl=Path(events_path) if events_path else path.with_name('locust_labeled_events.jsonl')
    available=jsonl.is_file()
    if available:
        for line in jsonl.open(encoding='utf-8-sig'):
            if not line.strip():continue
            try:event=valid_event(json.loads(line))
            except json.JSONDecodeError:event=None
            if event is None:
                invalid+=1;continue
            if event['uid'] in seen:
                invalid+=1;continue
            seen.add(event['uid'])
            dt=datetime.fromisoformat(event['occurred_at'].replace('Z','+00:00')).astimezone(timezone.utc)
            actual_counts[dt.replace(second=0,microsecond=0)]+=1
    score_by_split={s:{r['ground_truth'] for r in accepted if r['split']==s} for s in ('train','validation','test')}
    ranks={'train':0,'validation':1,'test':2};prev=-1;chronological=True
    for row in sorted(rows,key=lambda r:r['minute_start_utc']):
        if row['split'] not in ranks:continue
        if ranks[row['split']]<prev:chronological=False
        prev=ranks[row['split']]
    checks={
       'at_least_120000_http_events':total>=minimum_events,
       'at_least_1200_unambiguous_windows':len(accepted)>=minimum_windows,
       'all_8_scenarios':REQUIRED.issubset(scenarios),
       'at_least_5_seeds':len(seeds)>=5 if require_5seeds else True,
       'all_splits_present':all(splits.get(s,0)>0 for s in ('train','validation','test')),
       'normal_and_anomaly_in_each_split':all(v=={'normal','anomaly'} for v in score_by_split.values()),
       'split_is_chronological':chronological,
       'unique_minute_utc_keys':duplicates==0,
       'paired_jsonl_exists':available,
       'paired_jsonl_allowlist_valid':available and invalid==0,
       'paired_jsonl_counts_match':available and sum(actual_counts.values())==total and actual_counts==normalized_minutes,
    }
    return {'passed':all(checks.values()),'checks':checks,'event_count_manifest':total,
            'events_verified_in_jsonl':sum(actual_counts.values()),'jsonl_invalid_or_duplicate':invalid,
            'usable_windows':len(accepted),'excluded_or_ambiguous_windows':len(rows)-len(accepted),
            'scenarios':sorted(scenarios),'seeds':sorted(seeds),'split_counts':dict(splits),
            'manifest':str(path),'events_file':str(jsonl),
            'provenance_limit':'This gate cannot independently prove real HTTP/Locust execution. Keep original run manifests and Locust CSV logs.'}

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--manifest',required=True)
    p.add_argument('--events')
    p.add_argument('--min-events',type=int,default=120000)
    p.add_argument('--min-windows',type=int,default=1200)
    p.add_argument('--out',default='reports/hafta3/live_locust_acceptance.json')
    a=p.parse_args()
    result=check(a.manifest,a.min_events,a.min_windows,events_path=a.events)
    target=Path(a.out);target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))
    raise SystemExit(0 if result['passed'] else 2)
