"""Independent audit of LogScope MAIN *offline-simulated* JSONL and minute CSV.

Even when every offline criterion passes, NEVER report the real Django/Locust
HTTP collection requirement as passed. Only verify_week3_acceptance + original
Locust/Django run evidence can support the latter.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
from collections import Counter,defaultdict
from datetime import datetime,timezone
from pathlib import Path
from backend.analysis import SCENARIOS
from backend.event_contract import valid_event


def _file_hash(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as src:
        for chunk in iter(lambda:src.read(1024*1024),b''):
            h.update(chunk)
    return h.hexdigest()


def audit(jsonl, labels, min_events=120000, min_windows=1200):
    path=Path(jsonl);manifest=Path(labels)
    index={};secs=Counter();seeds=Counter();scenarios=Counter();per_split=Counter();uids=set()
    with manifest.open('r',newline='',encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            key=row['minute_start_utc']
            if key in index:raise ValueError('Duplicate minute')
            if row['scenario_code'] not in SCENARIOS:raise ValueError('Invalid scenario')
            if row['ground_truth']!=('anomaly' if row['scenario_code'].startswith('anomaly_') else 'normal'):
                raise ValueError('Scenario does not match ground truth')
            if row['split'] not in ('train','validation','test'):raise ValueError('Invalid partition')
            if row['ambiguous']!='false':raise ValueError('Offline dataset should not silently include ambiguous windows')
            index[key]=row;seeds[int(row['seed'])]+=1;scenarios[row['scenario_code']]+=1
            per_split[row['split']]+=1
    rows=0;invalid=0;unknown_minutes=0
    with path.open('r',encoding='utf-8') as f:
        for line in f:
            if not line.strip():continue
            try:e=valid_event(json.loads(line))
            except json.JSONDecodeError:e=None
            if e is None or e['uid'] in uids:
                invalid+=1;continue
            uids.add(e['uid']);rows+=1
            stamp=datetime.fromisoformat(e['occurred_at'].replace('Z','+00:00'))
            key=stamp.astimezone(timezone.utc).replace(second=0,microsecond=0).isoformat().replace('+00:00','Z')
            secs[key]+=1
            if key not in index:unknown_minutes+=1
    count_matches=unknown_minutes==0 and all(int(row['request_count'])==secs[minute] for minute,row in index.items()) and sum(secs.values())==rows
    checks={
        'event_rows_at_least_120000':rows>=min_events,
        'logical_minute_windows_at_least_1200':len(index)>=min_windows,
        'distinct_seeds_equal_5':len(seeds)==5,
        'all_8_scenarios':set(scenarios)==set(SCENARIOS),
        '60_20_20_split':per_split==Counter({'train':720,'validation':240,'test':240}) if len(index)==1200 else per_split['train']==int(len(index)*.6) and per_split['validation']==int(len(index)*.2),
        'valid_private_fields_and_unique_uids':invalid==0,
        'event_minute_counts_match_manifest':count_matches,
        'seed_partition_isolated':all(len({row['split'] for row in index.values() if int(row['seed'])==seed})==1 for seed in seeds),
    }
    return {'source_type':'OFFLINE_SIMULATION_NOT_REAL_HTTP',
            'passed_offline_schema_and_volume':all(checks.values()),
            'passed_real_django_locust_requirement':False,
            'checks':checks,'simulated_events':rows,'simulated_minute_windows':len(index),
            'seeds':dict(seeds),'scenario_minute_counts':dict(scenarios),
            'split_minute_counts':dict(per_split),'invalid_or_duplicate_events':invalid,
            'extra_unknown_event_minutes':unknown_minutes,
            'sha256':{'jsonl':_file_hash(path),'manifest':_file_hash(manifest)},
            'explicit_note':'Full live HTTP/Locust requirement remains OPEN; generation took no 20-hour real-time period.'}


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--jsonl',default='datasets/ana/logscope_ana_5tohum_OFFLINE_SIMULASYON.jsonl')
    p.add_argument('--manifest',default='datasets/ana/logscope_ana_dakika_etiketleri.csv')
    p.add_argument('--out',default='datasets/ana/ANA_VERI_SETI_KABUL_RAPORU.json')
    a=p.parse_args()
    report=audit(a.jsonl,a.manifest)
    output=Path(a.out);output.parent.mkdir(exist_ok=True,parents=True)
    output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))
    return 0 if report['passed_offline_schema_and_volume'] else 2

if __name__=='__main__':
    raise SystemExit(main())
