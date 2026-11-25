"""Offline controlled synthetic JSONL dataset generator (NOT a Locust HTTP run).

Purpose: development/EDA when Django+Locust are not yet installed. Produces
valid privacy-filtered HTTP events + separate ground-truth manifest. Run:
 python -m scripts.week3_generate_dataset --minutes 1200 --seed 42
"""
from __future__ import annotations
import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
import random
from backend.analysis import synthetic_windows

ROUTES = ('/','/catalog/','/search/','/items/{id}/','/forms/checkout/','/auth/login/','/admin/export/')
METHODS = ('GET','GET','GET','GET','POST')


def make_offline_events(minutes=1200, target_per_minute=102, seed=42, out_dir=None):
    """Return a dataset summary; no actual HTTP request is sent."""
    if minutes<120 or target_per_minute<30:
        raise ValueError('At least 120 minute windows and 30 planned events per minute')
    out_dir=Path(out_dir or Path('reports/hafta3'))
    out_dir.mkdir(parents=True, exist_ok=True)
    filename=out_dir/f'logscope_offline_seed{seed}_{minutes}m.jsonl'
    manifest_file=out_dir/f'scenario_manifest_seed{seed}.csv'
    windows=synthetic_windows(minutes,target_per_minute,seed)
    rng=random.Random(seed)
    start=datetime(2026,10,1,tzinfo=timezone.utc)+timedelta(days=seed%25)
    counts=Counter()
    seen_sessions=set()
    with filename.open('w',encoding='utf-8') as stream,manifest_file.open('w',encoding='utf-8',newline='') as mf:
        manifest=csv.writer(mf)
        manifest.writerow(['minute_start_utc','scenario_code','ground_truth','split','seed','request_count','ambiguous'])
        for w in windows:
            stamp=start+timedelta(minutes=w.index)
            split='train' if w.index<int(.6*minutes) else 'validation' if w.index<int(.8*minutes) else 'test'
            manifest.writerow([stamp.isoformat().replace('+00:00','Z'),w.scenario,'anomaly' if w.label else 'normal',split,seed,w.request_count,False])
            counts[w.scenario]+=w.request_count
            session_count=max(1,w.distinct_sessions)
            for j in range(w.request_count):
                sidx=j%session_count
                sid=f'syn-{seed}-{w.index}-{sidx}'
                seen_sessions.add((split,sid))
                if w.scenario=='anomaly_rare_route':
                    route='/admin/export/' if rng.random()<.7 else rng.choice(ROUTES[:5])
                elif w.scenario=='anomaly_login_fail':
                    route='/auth/login/' if rng.random()<.85 else '/catalog/'
                else:
                    route=rng.choices(ROUTES[:6],weights=[12,25,18,20,17,8])[0]
                status=200
                if w.scenario=='anomaly_5xx' and rng.random()<.28: status=503
                elif w.scenario=='anomaly_login_fail' and route=='/auth/login/' and rng.random()<.55:status=401
                elif rng.random()<.008:status=404
                elif rng.random()<.005:status=500
                latency=max(2,round(rng.gauss(w.p50_ms, max(4,w.p50_ms*.15)),3))
                if w.scenario=='anomaly_latency' and rng.random()<.7:latency+=round(rng.uniform(500,1050),3)
                obj={'event_uid':f'syn-{seed}-{w.index}-{j}',
                     'occurred_at':(stamp+timedelta(seconds=j*60/max(w.request_count,1))).isoformat(timespec='milliseconds').replace('+00:00','Z'),
                     'http_method':'POST' if route=='/forms/checkout/' else 'GET',
                     'route_template':route,'status_code':status,'duration_ms':latency,
                     'session_ref':sid,'schema_version':'1.0'}
                stream.write(json.dumps(obj,ensure_ascii=False,separators=(',',':'))+'\n')
    return {'mode':'offline_statistical_simulation_not_locust','seed':seed,'windows':minutes,
            'total_requests':sum(counts.values()),'scenario_counts':dict(counts),
            'data_file':str(filename),'labels_file':str(manifest_file),
            'session_groups':len(seen_sessions),
            'split':{'train':int(.6*minutes),'validation':int(.8*minutes)-int(.6*minutes),'test':minutes-int(.8*minutes)},
            'warning':'Generated statistical synthetic events without sending live HTTP requests. Do not label as Django/Locust test results.'}


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--minutes',type=int,default=1200)
    p.add_argument('--rate',type=int,default=102)
    p.add_argument('--seed',type=int,default=42)
    p.add_argument('--out',default='reports/hafta3')
    a=p.parse_args()
    result=make_offline_events(a.minutes,a.rate,a.seed,a.out)
    file=Path(a.out)/'dataset_summary.json'
    file.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
