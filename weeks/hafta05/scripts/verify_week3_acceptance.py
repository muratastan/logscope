"""Explicit pass/fail gates for the course's Week 3 Locust dataset.

No results are invented. The assessment reads an actual Locust-derived JSONL
and separate minute-label manifest produced by prepare_locust_dataset.py.
"""
from __future__ import annotations
import argparse
import csv
import json
from collections import Counter
from pathlib import Path

REQUIRED={
    'normal_steady','normal_hourly_rise','normal_campaign','normal_route_mix',
    'anomaly_5xx','anomaly_latency','anomaly_login_fail','anomaly_rare_route',
}


def check(manifest,minimum_events=120000,minimum_windows=1200,require_5seeds=True):
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
    # Ensure the same UTC minute is not counted more than once.
    minute_keys=[r['minute_start_utc'] for r in rows]
    duplicates=len(minute_keys)-len(set(minute_keys))
    checks={
        'genuine_locust_input_needed': 'source must be created by run_locust_matrix, not the offline statistical generator',
        'at_least_120000_http_events':total>=minimum_events,
        'at_least_1200_unambiguous_windows':len(accepted)>=minimum_windows,
        'all_8_scenarios':REQUIRED.issubset(scenarios),
        'at_least_5_seeds':len(seeds)>=5 if require_5seeds else True,
        'all_splits_present':all(splits.get(s,0)>0 for s in ('train','validation','test')),
        'unique_minute_utc_keys':duplicates==0,
    }
    return {'passed':all(v for v in checks.values() if isinstance(v,bool)),
            'checks':checks,'event_count':total,'usable_windows':len(accepted),
            'excluded_or_ambiguous_windows':len(rows)-len(accepted),
            'scenarios':sorted(scenarios),'seeds':sorted(seeds),'split_counts':dict(splits),
            'input':str(path)}


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--manifest',required=True)
    p.add_argument('--min-events',type=int,default=120000)
    p.add_argument('--min-windows',type=int,default=1200)
    p.add_argument('--out',default='reports/hafta3/live_locust_acceptance.json')
    a=p.parse_args()
    result=check(a.manifest,a.min_events,a.min_windows)
    target=Path(a.out);target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))
    raise SystemExit(0 if result['passed'] else 2)
