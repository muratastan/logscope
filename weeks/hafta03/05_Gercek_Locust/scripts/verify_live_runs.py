"""Verify integrity of individual Locust capture files BEFORE assembly.

A PASS proves consistent *declared* localhost capture artifacts (canonical schema,
synthetic session UUIDs, scenario HTTP behavior, timestamps and SHA256). It
CANNOT independently prove 40 trials were really performed on a real webserver.
Keep original Locust CSV performance logs for external inspection.
"""
from __future__ import annotations
import argparse
import csv
from collections import Counter
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
from backend.event_contract import valid_event
from scripts.run_locust_matrix import SCENARIOS,validate_case


def verify(manifest,require_full_matrix=True):
    src=Path(manifest).resolve()
    if not src.is_file():
        raise FileNotFoundError(src)
    with src.open('r',encoding='utf-8-sig',newline='') as file:
        records=list(csv.DictReader(file))
    if not records:
        raise ValueError('No Locust trial records')
    pair={(int(r['seed']),r['scenario']) for r in records}
    if len(pair)!=len(records):
        raise ValueError('Duplicate scenario+seed rows in original run manifest')
    checks={};issues=[]
    unique_seeds={seed for seed,_ in pair}
    checks['all_8_scenarios_with_5_seeds']=len(unique_seeds)>=5 and all({code for seed,code in pair if seed==s}==set(SCENARIOS) for s in unique_seeds)
    if not require_full_matrix:
        checks['all_8_scenarios_with_5_seeds']=True
    valid_count=0;seen_uids=set();total=0;sha_count=0
    for row in records:
        capture=Path(row['log_file'])
        if not capture.is_absolute():
            capture=src.parent/capture
        if not capture.is_file():
            issues.append(f'Missing capture for {row["seed"]}/{row["scenario"]}')
            continue
        try:
            trial=validate_case(capture,row['scenario'],strict_schema=True)
            if trial['events']!=int(row['request_rows']):
                raise ValueError('Mismatch between trial manifest and captured rows')
            if not row.get('capture_sha256'):
                raise ValueError('Missing capture_sha256; regenerate using current runner')
            if hashlib.sha256(capture.read_bytes()).hexdigest()!=row['capture_sha256']:
                raise ValueError('Locust capture SHA256 does not match original run manifest')
            sha_count+=1
            start=float(row['start_unix']);finish=float(row['finish_unix'])
            if start<=0 or finish<=start:
                raise ValueError('Missing/invalid real wall-clock trial start/end')
            with capture.open(encoding='utf-8') as f:
                for line in f:
                    if not line.strip():continue
                    item=valid_event(json.loads(line))
                    if item['uid'] in seen_uids:
                        raise ValueError('Duplicate event ID across Locust trials')
                    seen_uids.add(item['uid'])
                    at=datetime.fromisoformat(item['occurred_at'].replace('Z','+00:00')).astimezone(timezone.utc).timestamp()
                    if not start-20<=at<=finish+20:
                        raise ValueError('HTTP event timestamp lies outside declared trial bounds')
            total+=trial['events'];valid_count+=1
        except (ValueError,KeyError,TypeError,json.JSONDecodeError) as exc:
            issues.append(f'{row["seed"]}/{row["scenario"]}: {exc}')
    checks['all_capture_files_valid']=valid_count==len(records)
    checks['all_capture_files_sha256_present_and_matching']=sha_count==len(records)
    checks['at_least_120000_declared_http_rows']=total>=120000 if require_full_matrix else total>0
    result={'passed':all(checks.values()),'checks':checks,
            'run_count':len(records),'valid_run_count':valid_count,'total_verified_capture_rows':total,
            'seed_count':len(unique_seeds),'issues':issues[:40],
            'provenance_limit':'Integrity verification only; original Locust CSV reports, local server logs and collection metadata must be retained to substantiate live HTTP execution.'}
    return result


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--manifest',default='reports/hafta3/live_locust/locust_runs_manifest.csv')
    parser.add_argument('--out',default='reports/hafta3/live_locust_provenance.json')
    args=parser.parse_args()
    result=verify(args.manifest)
    target=Path(args.out);target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0 if result['passed'] else 2

if __name__=='__main__':
    raise SystemExit(main())
