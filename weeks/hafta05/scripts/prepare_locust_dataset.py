"""Join real Locust run files into anonymized events + separate minute labels.

Boundary minutes where multiple scenarios overlap are marked ambiguous and
excluded from primary F1 evaluation. Splits follow chronological SEED blocks
(train first 60%, validation next 20%, test final 20%). No metadata is placed
inside JSONL events, protecting against label leakage.
"""
from __future__ import annotations
import csv
import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timezone
from backend.event_contract import valid_event


def transform(source_manifest,output_dir):
    output=Path(output_dir);output.mkdir(parents=True,exist_ok=True)
    records=list(csv.DictReader(Path(source_manifest).open(encoding='utf-8-sig',newline='')))
    if not records:raise ValueError('No Locust runs')
    seeds=sorted({int(r['seed']) for r in records})
    if len(seeds)<5:raise ValueError('At least five distinct seed runs are required by proposal')
    boundaries=(int(.6*len(seeds)),int(.8*len(seeds)))
    split_by_seed={v:('train' if i<boundaries[0] else 'validation' if i<boundaries[1] else 'test') for i,v in enumerate(seeds)}
    # verify all eight classes for each split
    periods=defaultdict(set)
    for r in records:periods[split_by_seed[int(r['seed'])]].add(r['scenario'])
    required={'normal_steady','normal_hourly_rise','normal_campaign','normal_route_mix',
              'anomaly_5xx','anomaly_latency','anomaly_login_fail','anomaly_rare_route'}
    if any(not required.issubset(periods[sp]) for sp in ('train','validation','test')):
        raise ValueError('Each chronological split must include all eight scenarios')
    minute_cases=defaultdict(list);count=0
    merged=output/'locust_labeled_events.jsonl'
    with merged.open('w',encoding='utf-8') as out:
        for r in records:
            case_path=Path(r['log_file'])
            if not case_path.is_absolute():
                case_path=case_path if case_path.is_file() else Path(source_manifest).parent/case_path
            if not case_path.is_file():raise FileNotFoundError(case_path)
            for line in case_path.open(encoding='utf-8'):
                if not line.strip():continue
                try:event=json.loads(line)
                except json.JSONDecodeError:continue
                checked=valid_event(event)
                if checked is None:continue
                stamp=datetime.fromisoformat(checked['occurred_at'].replace('Z','+00:00')).astimezone(timezone.utc)
                minute=stamp.replace(second=0,microsecond=0)
                minute_cases[minute].append((r['scenario'],int(r['seed'])))
                out.write(json.dumps(event,ensure_ascii=False,separators=(',',':'))+'\n')
                count+=1
    file=output/'scenario_manifest.csv'
    ambiguous_count=0
    with file.open('w',encoding='utf-8',newline='') as f:
        writer=csv.writer(f)
        writer.writerow(['minute_start_utc','scenario_code','ground_truth','split','seed','request_count','ambiguous'])
        for minute,pairs in sorted(minute_cases.items()):
            choices=set(pairs)
            amb=len(choices)>1
            ambiguous_count+=int(amb)
            code,seed=sorted(choices)[0]
            writer.writerow([minute.isoformat().replace('+00:00','Z'),code,
                             'anomaly' if code.startswith('anomaly_') else 'normal',
                             'excluded' if amb else split_by_seed[seed],seed,len(pairs),str(amb).lower()])
    return {'events':count,'unique_minute_windows':len(minute_cases),'ambiguous_windows':ambiguous_count,
            'split_by_seed':split_by_seed,'jsonl':str(merged),'manifest':str(file),
            'note':'Locust HTTP-generated events; ambiguous transition minutes excluded from F1; no labels in JSONL'}

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--manifest',required=True);p.add_argument('--out',default='reports/hafta3/live_locust_prepared')
    a=p.parse_args()
    print(json.dumps(transform(a.manifest,a.out),ensure_ascii=False,indent=2))
