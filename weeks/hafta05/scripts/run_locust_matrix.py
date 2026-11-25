"""Resumable real HTTP Locust matrix against localhost Django only.

Eight named classes x five independent seeds. Each trial captures a distinct
JSONL segment, while scenario labels live in a separate CSV manifest.

Recommended >=34 minutes per case for >=1200 unambiguous one-minute windows;
this is a LONG controlled 40-run workload and must only target loopback.
Run it over multiple sessions with --resume, after starting Django.
"""
from __future__ import annotations
import argparse
import csv
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from urllib.parse import urlparse
from urllib.request import urlopen

SCENARIOS={
    'normal_steady':'NormalSteady',
    'normal_hourly_rise':'NormalHourlyRise',
    'normal_campaign':'NormalCampaign',
    'normal_route_mix':'NormalRouteMix',
    'anomaly_5xx':'Anomaly5xx',
    'anomaly_latency':'AnomalyLatency',
    'anomaly_login_fail':'AnomalyLoginFail',
    'anomaly_rare_route':'AnomalyRareRoute',
}


def loopback(host):
    p=urlparse(host)
    if p.hostname not in ('localhost','127.0.0.1','::1') or p.scheme!='http':
        raise ValueError('Load tests are permitted only against localhost HTTP Django')
    return p


def write_manifest(out,records):
    if not records:
        return
    fieldnames=list(records[0])
    manifest=out/'locust_runs_manifest.csv'
    temp=out/'locust_runs_manifest.csv.tmp'
    with temp.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fieldnames);w.writeheader();w.writerows(records)
    temp.replace(manifest)
    (out/'locust_runs_manifest.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')


def matrix(host='http://127.0.0.1:8001', minutes_per_case=34, users=20,
           seeds=(11,23,42,71,97),out_dir='reports/hafta3/live_locust',resume=True):
    loopback(host)
    if minutes_per_case<1 or users<1 or len(set(seeds))<5:
        raise ValueError('Positive time/users and at least 5 seeds are required')
    out=Path(out_dir).resolve();out.mkdir(parents=True,exist_ok=True)
    logpath=Path(os.getenv('LOGSCOPE_JSONL_PATH','django_demo/generated_access.jsonl')).resolve()
    if not logpath.is_file():
        raise RuntimeError(f'Django JSONL is not present: {logpath}. Start Django and generate a sample request.')
    try:
        with urlopen(host+'/catalog/',timeout=4) as reply:assert reply.status==200
        with urlopen(host+'/testing/slow/',timeout=4) as reply:assert reply.status==200
    except Exception as exc:
        raise RuntimeError('Local Django inactive or anomaly endpoints disabled; enable ONLY in local test environment') from exc
    path=out/'locust_runs_manifest.csv'
    records=list(csv.DictReader(path.open(encoding='utf-8-sig',newline=''))) if resume and path.is_file() else []
    existing={(int(r['seed']),r['scenario']):r for r in records}
    for seed in seeds:
        for code,cls in SCENARIOS.items():
            key=(seed,code)
            old=existing.get(key)
            if old:
                capture=Path(old['log_file'])
                if int(old['test_duration_minutes'])!=minutes_per_case or int(old['users'])!=users:
                    raise ValueError(f'Resume mismatch for {key}; use a fresh --out folder when changing users/time')
                if not capture.is_file() or capture.stat().st_size==0:
                    raise RuntimeError(f'Invalid existing Locust capture: {capture}')
                print(f'Skipping completed scenario: {seed} {code}',flush=True)
                continue
            before=logpath.stat().st_size
            prefix=out/f'locust_seed{seed}_{code}'
            command=[sys.executable,'-m','locust','-f','django_demo/loadtest/locustfile.py',
                     cls,'--host',host,'--headless','-u',str(users),'-r','5',
                     '-t',f'{minutes_per_case}m','--stop-timeout','3','--csv',str(prefix),'--only-summary']
            env=os.environ.copy();env['LOGSCOPE_TEST_SEED']=str(seed)
            print('Controlled local HTTP scenario:',seed,code,flush=True)
            started=time.time()
            subprocess.run(command,check=True,env=env,timeout=60*minutes_per_case+120)
            end=logpath.stat().st_size
            capture=prefix.with_suffix('.jsonl')
            with logpath.open('rb') as f, capture.open('wb') as output:
                f.seek(before)
                remaining=end-before
                while remaining:
                    block=f.read(min(1024*1024,remaining))
                    if not block:raise RuntimeError('Django JSONL truncated during capture')
                    output.write(block);remaining-=len(block)
            count=sum(1 for line in capture.open(encoding='utf-8') if line.strip())
            if not count:raise RuntimeError(f'Scenario generated zero HTTP records: {key}')
            records.append({'seed':seed,'scenario':code,
                            'label':'anomaly' if code.startswith('anomaly_') else 'normal',
                            'start_unix':started,'finish_unix':time.time(),
                            'request_rows':count,'log_file':str(capture.resolve()),
                            'test_duration_minutes':minutes_per_case,'users':users})
            write_manifest(out,records)  # recover completed trials after interruptions
    total=sum(int(row['request_rows']) for row in records)
    print(f'Captured {total} HTTP events across {len(records)} local Locust cases',flush=True)
    return records


if __name__=='__main__':
    p=argparse.ArgumentParser(description='Local-only resumable 8 x 5 Locust research matrix')
    p.add_argument('--host',default='http://127.0.0.1:8001')
    p.add_argument('--minutes-per-case',type=int,default=34)
    p.add_argument('--users',type=int,default=20)
    p.add_argument('--seed-list',default='11,23,42,71,97')
    p.add_argument('--out',default='reports/hafta3/live_locust')
    p.add_argument('--no-resume',action='store_true',help='Run fresh trials; use a new output folder to avoid accidental overwrite')
    a=p.parse_args()
    matrix(a.host,a.minutes_per_case,a.users,tuple(int(v) for v in a.seed_list.split(',')),a.out,not a.no_resume)
