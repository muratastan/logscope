"""Prepare locally captured Locust HTTP logs with separate minute labels.

Chronological split is based on run start time (NOT numeric random-seed order).
Run files must be genuinely produced by local Django middleware; this script
checks content consistency but cannot independently certify its provenance.
Boundary minutes with mixed conditions are marked excluded.
"""
from __future__ import annotations
import csv
import json
import hashlib
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime, timezone
from backend.event_contract import valid_event
from backend.analysis import SCENARIOS


def _utc(value):
    dt=datetime.fromisoformat(value.replace('Z','+00:00'))
    if dt.utcoffset() is None:raise ValueError('Timezone required')
    return dt.astimezone(timezone.utc)


def transform(source_manifest,output_dir):
    manifest_path=Path(source_manifest).resolve()
    output=Path(output_dir);output.mkdir(parents=True,exist_ok=True)
    with manifest_path.open(encoding='utf-8-sig',newline='') as f:
        records=list(csv.DictReader(f))
    if not records:raise ValueError('No Locust runs')
    codes=set(SCENARIOS)
    if len({(int(r['seed']),r['scenario']) for r in records})!=len(records):
        raise ValueError('Duplicate seed/scenario run in Locust manifest')
    seeds=sorted({int(r['seed']) for r in records})
    if len(seeds)<5:raise ValueError('At least five distinct seed runs are required by proposal')
    for seed in seeds:
        present={r['scenario'] for r in records if int(r['seed'])==seed}
        if present!=codes:raise ValueError(f'Each seed needs all 8 scenarios; seed={seed}, got {sorted(present)}')
    # Sort by *actual recorded start*; only malformed test fixtures without a
    # positive timestamp fall back to their seed number.
    first_start={seed:min((float(r.get('start_unix') or 0) for r in records if int(r['seed'])==seed and float(r.get('start_unix') or 0)>0),default=0)
                 for seed in seeds}
    if all(first_start.values()):
        chronological_seeds=sorted(seeds,key=lambda seed:(first_start[seed],seed))
        if len(set(first_start.values()))!=len(seeds):
            raise ValueError('Identical seed start times; cannot prove chronological ordering')
    elif not any(first_start.values()):
        chronological_seeds=seeds
    else:
        raise ValueError('Incomplete seed start times; cannot safely split in chronological order')
    train_limit=int(.6*len(seeds));valid_limit=int(.8*len(seeds))
    split_by_seed={seed:('train' if index<train_limit else 'validation' if index<valid_limit else 'test')
                   for index,seed in enumerate(chronological_seeds)}
    minute_cases=defaultdict(Counter)
    seen_uids=set();count=0
    merged=output/'locust_labeled_events.jsonl'
    temporary=output/'locust_labeled_events.jsonl.tmp'
    try:
        # Sort all input runs by their declared starting time for reproducibility.
        sorted_runs=sorted(records,key=lambda r:(float(r.get('start_unix') or 0),int(r['seed']),r['scenario']))
        with temporary.open('w',encoding='utf-8') as out:
            for r in sorted_runs:
                if r['scenario'] not in codes:raise ValueError('Unknown scenario')
                case_path=Path(r['log_file'])
                if not case_path.is_absolute():
                    case_path=case_path if case_path.is_file() else manifest_path.parent/case_path
                if not case_path.is_file():raise FileNotFoundError(case_path)
                if r.get('capture_sha256'):
                    actual_hash=hashlib.sha256(case_path.read_bytes()).hexdigest()
                    if actual_hash!=r['capture_sha256']:
                        raise ValueError(f'Captured Locust file hash mismatch: {case_path.name}')
                run_count=0
                for line in case_path.open(encoding='utf-8'):
                    if not line.strip():continue
                    try:event=json.loads(line)
                    except json.JSONDecodeError as exc:raise ValueError(f'Invalid JSON in {case_path}') from exc
                    checked=valid_event(event)
                    if checked is None:raise ValueError(f'Invalid/private fields in {case_path}')
                    if checked['uid'] in seen_uids:
                        raise ValueError(f'Duplicate event UID in Locust inputs: {checked["uid"]}')
                    seen_uids.add(checked['uid'])
                    minute=_utc(checked['occurred_at']).replace(second=0,microsecond=0)
                    minute_cases[minute][(r['scenario'],int(r['seed']))]+=1
                    out.write(json.dumps(event,ensure_ascii=False,separators=(',',':'))+'\n')
                    count+=1;run_count+=1
                if run_count!=int(r['request_rows']):
                    raise ValueError(f'Locust capture size mismatch in {case_path}: expected {r["request_rows"]}, found {run_count}')
        temporary.replace(merged)
    finally:
        temporary.unlink(missing_ok=True)
    label_path=output/'scenario_manifest.csv'
    ambiguous_count=0
    with label_path.open('w',encoding='utf-8',newline='') as f:
        writer=csv.writer(f)
        writer.writerow(['minute_start_utc','scenario_code','ground_truth','split','seed','request_count','ambiguous'])
        for minute,counts in sorted(minute_cases.items()):
            cases=set(counts)
            ambiguous=len(cases)>1
            ambiguous_count+=int(ambiguous)
            code,seed=sorted(cases)[0]
            writer.writerow([minute.isoformat().replace('+00:00','Z'),code,
                             'anomaly' if code.startswith('anomaly_') else 'normal',
                             'excluded' if ambiguous else split_by_seed[seed],seed,
                             sum(counts.values()),str(ambiguous).lower()])
    result={'events':count,'unique_minute_windows':len(minute_cases),
            'ambiguous_windows':ambiguous_count,'split_by_seed':split_by_seed,
            'chronological_seed_order':chronological_seeds,'jsonl':str(merged),
            'manifest':str(label_path),'declared_source':str(manifest_path),
            'note':'Locally declared Locust run files; independently recheck via verify_week3_acceptance. Labels are excluded from JSONL.'}
    (output/'preparation_summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    return result


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument('--manifest',required=True)
    p.add_argument('--out',default='reports/hafta3/live_locust_prepared')
    a=p.parse_args()
    print(json.dumps(transform(a.manifest,a.out),ensure_ascii=False,indent=2))
