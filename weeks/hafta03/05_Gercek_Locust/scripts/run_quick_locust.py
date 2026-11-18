"""Short localhost HTTP demonstration across 8 LogScope scenario classes.

This is NOT the full research matrix (5 seeds, 120k requests, 1200 minute
windows), nor a substitute for real-data model evaluation. The runner calls
actual Locust subprocesses, captures Django JSONL middleware rows and saves
checksums, Locust CSVs, and a transparent, inspectable summary.
"""
from __future__ import annotations
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from urllib.error import HTTPError
from urllib.request import urlopen
from scripts.run_locust_matrix import SCENARIOS, loopback, validate_case

ROOT=Path(__file__).resolve().parents[1]

def check_response(base,route,expected):
    try:
        with urlopen(base+route,timeout=8) as r:
            got=r.status
    except HTTPError as e:
        got=e.code
    if got!=expected:
        raise RuntimeError(f'Expected HTTP {expected} from {route}, got {got}. Check the local Django server and LOGSCOPE_ENABLE_ANOMALY_ENDPOINTS=1.')

def main():
    ap=argparse.ArgumentParser(description='8 case fast local HTTP demo, NOT full IP3 acceptance')
    ap.add_argument('--host',default='http://127.0.0.1:8001')
    ap.add_argument('--seconds-per-case',type=int,default=25)
    ap.add_argument('--users',type=int,default=8)
    ap.add_argument('--seed',type=int,default=11)
    ap.add_argument('--out',default='reports/hafta3/HIZLI_HTTP_DEMO')
    opts=ap.parse_args()
    loopback(opts.host)
    if not 15<=opts.seconds_per_case<=600 or not 1<=opts.users<=40:
        raise ValueError('Use 15-600 seconds per case and 1-40 users on localhost only.')
    logpath=Path(os.environ.get('LOGSCOPE_JSONL_PATH','django_demo/generated_access.jsonl')).resolve()
    out=Path(opts.out).resolve();out.mkdir(parents=True,exist_ok=True)
    check_response(opts.host,'/catalog/',200)
    check_response(opts.host,'/testing/error/',503)
    check_response(opts.host,'/auth/login/?simulate_failure=1',401)
    check_response(opts.host,'/testing/slow/',200)
    if not logpath.is_file():
        raise FileNotFoundError(f'Django JSONL missing: {logpath}')
    summary={'source':'LOCUST_TO_LOCAL_DJANGO_HTTP_SHORT_DEMO',
             'full_research_acceptance':False,
             'limits':'Only 8 short classes/one seed; cannot prove 5 seeds, 120000 requests, 1200 windows or final model scores. Normal hour rise/campaign phases cannot be faithfully assessed in a short run.',
             'host':opts.host,'seconds_per_case':opts.seconds_per_case,'users':opts.users,'seed':opts.seed,
             'started_utc':datetime.now(timezone.utc).isoformat(), 'cases':[]}
    try:
        for code, cls in SCENARIOS.items():
            prefix=out/f'{code}_seed{opts.seed}'
            if prefix.with_suffix('.jsonl').exists():
                raise FileExistsError(f'Existing capture {prefix.with_suffix(".jsonl")}. Use a new --out directory so evidence is not overwritten.')
            before=logpath.stat().st_size
            command=[sys.executable,'-m','locust','-f',str(ROOT/'django_demo/loadtest/locustfile.py'),cls,
                    '--host',opts.host,'--headless','-u',str(opts.users),'-r',str(min(opts.users,5)),
                    '-t',f'{opts.seconds_per_case}s','--stop-timeout','3',
                    '--csv',str(prefix),'--only-summary']
            env=os.environ.copy();env['LOGSCOPE_TEST_SEED']=str(opts.seed)
            log=Path(str(prefix)+'_locust_console.txt')
            print(f'[{len(summary["cases"])+1}/8] {code}: real localhost HTTP Locust {opts.seconds_per_case}s',flush=True)
            with log.open('w',encoding='utf-8') as fp:
                finished=subprocess.run(command,env=env,cwd=ROOT,stdout=fp,stderr=subprocess.STDOUT,
                                        timeout=opts.seconds_per_case+100)
            if finished.returncode:
                tail='\n'.join(log.read_text(encoding='utf-8',errors='replace').splitlines()[-15:])
                raise RuntimeError(f'Locust exited {finished.returncode} in {code}.\n{tail}')
            end=logpath.stat().st_size
            capture=prefix.with_suffix('.jsonl')
            if end<before:raise RuntimeError('Django log truncated while Locust was running')
            with logpath.open('rb') as inp,capture.open('wb') as dest:
                inp.seek(before)
                remaining=end-before
                while remaining:
                    chunk=inp.read(min(1048576,remaining))
                    if not chunk:raise RuntimeError('Django log truncated during copy')
                    dest.write(chunk);remaining-=len(chunk)
            checked=validate_case(capture,code,strict_schema=True)
            case={'scenario':code,'label':'anomaly' if code.startswith('anomaly_') else 'normal',
                  'real_http_events':checked['events'],'http_status_counts':checked['statuses'],
                  'sha256':hashlib.sha256(capture.read_bytes()).hexdigest(),
                  'captured_jsonl':capture.name,'locust_console':log.name}
            summary['cases'].append(case)
            (out/'HIZLI_HTTP_SONUC.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
        summary['finished_utc']=datetime.now(timezone.utc).isoformat()
        summary['all_eight_short_cases_verified']=len(summary['cases'])==8
        summary['real_http_events_total']=sum(i['real_http_events'] for i in summary['cases'])
        (out/'HIZLI_HTTP_SONUC.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
        print('\nDEMO PASS: eight local Locust classes ran and produced real HTTP JSONL rows.',flush=True)
        print('HTTP rows:',summary['real_http_events_total'],'Evidence:',out/'HIZLI_HTTP_SONUC.json',flush=True)
        print('This is NOT completion of the long 8x5/120000/1200 research acceptance.',flush=True)
        return 0
    except Exception:
        (out/'HIZLI_HTTP_SONUC.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
        raise

if __name__=='__main__':
    raise SystemExit(main())
