"""Canonical research importer for the PostgreSQL 27-table schema.

Use only in a local controlled setup (not exposed as a public API). The importer
writes to logscope.scenario_runs, ingestion_batches, synthetic_sessions,
http_events, traffic_windows. No scenario labels enter model feature payloads.

It requires a live PostgreSQL database with db/01_*.sql and db/02_*.sql applied.
"""
from __future__ import annotations
import csv
import json
import math
import uuid
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from statistics import median
from backend.event_contract import valid_event
from backend.analysis import SCENARIOS

_NAMESPACE=uuid.UUID('f6cd5020-236d-4d10-9501-f5dd434324a0')


def date(value):
    z=datetime.fromisoformat(value.replace('Z','+00:00'))
    if z.utcoffset() is None:raise ValueError('UTC or offset-aware timestamps required')
    return z.astimezone(timezone.utc)


def read_manifest(path):
    """Returns minute-indexed *external label metadata*, not model features."""
    data={};seen_splits=set()
    with Path(path).open(encoding='utf-8-sig',newline='') as f:
        for item in csv.DictReader(f):
            key=date(item['minute_start_utc']).replace(second=0,microsecond=0)
            if key in data:raise ValueError(f'Duplicate manifest minute: {key}')
            if item['scenario_code'] not in SCENARIOS:raise ValueError('Unknown scenario')
            if item['ground_truth'] not in ('normal','anomaly'):raise ValueError('Invalid label')
            if item['split'] not in ('train','validation','test','excluded'):raise ValueError('Invalid split')
            if item['ambiguous'] not in ('True','False','true','false','0','1'):
                raise ValueError('Invalid ambiguous marker')
            if (item['ground_truth']=='anomaly') != item['scenario_code'].startswith('anomaly_'):
                raise ValueError('Scenario class conflicts with truth label')
            data[key]=item
            seen_splits.add(item['split'])
    if not {'train','validation','test'}.issubset(seen_splits):raise ValueError('Train/validation/test required')
    # The split must not move backward over chronological time
    rank={'train':0,'validation':1,'test':2}
    prev=-1
    for key in sorted(data):
        if data[key]['split']=='excluded':continue  # boundary minute; not used in model fitting/evaluation
        current=rank[data[key]['split']]
        if current<prev:raise ValueError('Non-chronological dataset split')
        prev=current
    return data


def preview_import(events_path,manifest_path,limit=None):
    """Validate and aggregate before opening a DB transaction.

    For full datasets, this streams events from disk, retaining per-minute
    summary arrays and per-session min/max timestamps only.
    """
    manifest=read_manifest(manifest_path)
    stats=defaultdict(lambda:{'durations':[],'statuses':Counter(),'routes':Counter(),
                              'sessions':set(),'times':[]})
    sessions={};count=0
    bad=0;uids=set()
    for line in Path(events_path).open(encoding='utf-8'):
        if not line.strip():continue
        if limit is not None and count>=limit:break
        try:raw=json.loads(line)
        except json.JSONDecodeError:bad+=1;continue
        event=valid_event(raw)
        if event is None or event['uid'] in uids:
            bad+=1;continue
        dt=date(event['occurred_at']);minute=dt.replace(second=0,microsecond=0)
        if minute not in manifest:
            bad+=1;continue
        uids.add(event['uid']);count+=1
        st=stats[minute];st['durations'].append(event['duration_ms']);st['statuses'][event['status']]+=1;st['routes'][event['route']]+=1;st['times'].append(dt)
        session=event.get('session_ref')
        if session:
            st['sessions'].add(session)
            scenario=manifest[minute]['scenario_code']
            key=(scenario,int(manifest[minute]['seed']),session)
            if key in sessions:
                old=sessions[key]
                old[0]=min(old[0],dt);old[1]=max(old[1],dt)
            else:sessions[key]=[dt,dt]
    return {'events':count,'rejected':bad,'minutes_with_events':len(stats),
            'manifest_minutes':len(manifest),'scenario_codes':sorted({v['scenario_code'] for v in manifest.values()}),
            'session_groups':len(sessions),'truth_kept_out_of_log':True},manifest,stats,sessions


def _p95(xs):
    ys=sorted(xs);return ys[min(len(ys)-1,math.ceil(.95*len(ys))-1)]


def import_postgres(connection,events_path,manifest_path,workspace_id=None):
    """Transactional canonical import; connection is a psycopg v3 Connection.

    Operations use parameterized SQL. Returns recorded/rejected counts.
    A failure rolls back the entire import. The DB tables must already exist.
    """
    summary,manifest,stats,sessions=preview_import(events_path,manifest_path)
    if summary['events']==0:raise ValueError('No valid data to import')
    group=defaultdict(list)
    for minute,row in manifest.items():group[(row['scenario_code'],int(row['seed']))].append(minute)
    with connection.transaction():
        with connection.cursor() as cur:
            cur.execute('SET LOCAL search_path TO logscope, public')
            # Reimporting the same named file used to create fresh scenario runs
            # while ON CONFLICT silently skipped old HTTP events. Reject it rather
            # than produce orphan research windows or mismatched sessions.
            cur.execute('''SELECT id FROM ingestion_batches
                           WHERE source_name=%s AND state='completed' LIMIT 1''',(Path(events_path).name,))
            if cur.fetchone():
                raise ValueError('This JSONL filename is already imported; use a distinct named dataset for another run')
            run_ids={}
            for (code,seed),timestamps in group.items():
                cur.execute('''INSERT INTO scenario_runs(scenario_code, traffic_class, random_seed, started_at, ended_at, config,workspace_id)
                    VALUES (%s,%s,%s,%s,%s,%s::jsonb,%s) RETURNING id''',(
                    code,'anomaly' if code.startswith('anomaly_') else 'normal',seed,min(timestamps),max(timestamps)+timedelta(minutes=1),
                    json.dumps({'source':'offline_generated_events' if 'offline' in str(events_path) else 'controlled_external_jsonl','label_manifest':Path(manifest_path).name}),workspace_id))
                run_ids[(code,seed)]=cur.fetchone()[0]
            cur.execute('''INSERT INTO ingestion_batches(source_name,schema_version,state,workspace_id,error_summary)
                VALUES(%s,'1.0','processing',%s,%s::jsonb) RETURNING id''',(Path(events_path).name,workspace_id,json.dumps({'initial_rejected':summary['rejected']})))
            batch_id=cur.fetchone()[0]
            session_ids={}
            for (code,seed,session),bounds in sessions.items():
                run_id=run_ids[(code,seed)]
                cur.execute('''INSERT INTO synthetic_sessions(session_ref,scenario_run_id,first_seen_at,last_seen_at)
                     VALUES (%s,%s,%s,%s) ON CONFLICT(session_ref) DO UPDATE SET last_seen_at=EXCLUDED.last_seen_at RETURNING id''',
                            (uuid.uuid5(_NAMESPACE,f'{code}|{seed}|{session}'),run_id,bounds[0],bounds[1]))
                session_ids[(code,seed,session)]=cur.fetchone()[0]
            count=0;duplicate=0;values=[]
            def flush():
                nonlocal count,duplicate
                if not values:return
                cur.executemany('''INSERT INTO http_events(event_uid,ingestion_batch_id,scenario_run_id,synthetic_session_id,occurred_at,http_method,route_template,status_code,duration_ms,schema_version)
                  VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,'1.0') ON CONFLICT(event_uid) DO NOTHING''',values)
                count+=max(0,cur.rowcount)
                duplicate+=len(values)-max(0,cur.rowcount)
                values.clear()
            for line in Path(events_path).open(encoding='utf-8'):
                if not line.strip():continue
                try:ev=valid_event(json.loads(line))
                except json.JSONDecodeError:ev=None
                if not ev:continue
                dt=date(ev['occurred_at']);minute=dt.replace(second=0,microsecond=0)
                label=manifest.get(minute)
                if not label:continue
                scenario=label['scenario_code'];run=run_ids[(scenario,int(label['seed']))]
                sess=session_ids.get((scenario,int(label['seed']),ev.get('session_ref')))
                values.append((uuid.uuid5(_NAMESPACE,ev['uid']),batch_id,run,sess,dt,ev['method'],ev['route'],ev['status'],ev['duration_ms']))
                if len(values)>=1000:flush()
            flush()
            for minute,vals in stats.items():
                label=manifest[minute]
                times=sorted(vals['times'])
                intervals=[(b-a).total_seconds()*1000 for a,b in zip(times,times[1:])]
                cnt=len(vals['durations'])
                p50=median(vals['durations']);p95=_p95(vals['durations'])
                cur.execute('''INSERT INTO traffic_windows(scenario_run_id,window_start,window_end,scope,route_template,request_count,count_4xx,count_5xx,p50_duration_ms,p95_duration_ms,distinct_session_count,route_diversity,avg_request_interval_ms,features,ground_truth_label,dataset_split)
                    VALUES(%s,%s,%s,'global',NULL,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s,%s)
                    ON CONFLICT DO NOTHING''',(
                    run_ids[(label['scenario_code'],int(label['seed']))],minute,minute+timedelta(minutes=1),cnt,
                    sum(v for code,v in vals['statuses'].items() if 400<=code<500),
                    sum(v for code,v in vals['statuses'].items() if code>=500),p50,p95,len(vals['sessions']),len(vals['routes']),
                    sum(intervals)/len(intervals) if intervals else None,
                    json.dumps({'source':'offline_statistical_simulation' if 'offline' in str(events_path) else 'unverified_external_jsonl','rate_4xx':sum(v for code,v in vals['statuses'].items() if 400<=code<500)/cnt,
                                'rate_5xx':sum(v for code,v in vals['statuses'].items() if code>=500)/cnt}),
                    'ambiguous' if label['ambiguous'].lower() in ('true','1') else label['ground_truth'],label['split']))
            cur.execute('''UPDATE ingestion_batches SET accepted_rows=%s,rejected_rows=%s,duplicate_rows=%s,state='completed' WHERE id=%s''',
                        (count,summary['rejected'],duplicate,batch_id))
    return {'batch_id':batch_id,'accepted':count,'rejected':summary['rejected'],'duplicate':duplicate,'windows':len(stats),
            'scenario_runs':len(group),'source':'canonical PostgreSQL logscope schema'}
