"""Functional API integration tests against isolated SQLite database."""
import io
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory

_tmp = TemporaryDirectory(prefix="logscope_test_")
os.environ['LOGSCOPE_DATABASE_URL'] = "sqlite:///" + str(Path(_tmp.name) / "run.sqlite3")
os.environ['LOGSCOPE_DEMO_MODE']='1'
from fastapi.testclient import TestClient
from backend.fullstack import app,engine,metadata
from backend.analysis import run_experiment,prefixspan,subsequence,synthetic_windows


def client():
    c=TestClient(app)
    r=c.post('/api/login',json={'email':'demo@logscope.local','password':'Demo2026!'})
    assert r.status_code==200,r.text
    return c

def test_public_and_auth():
    c=TestClient(app)
    assert c.get('/api/health').json()['ok']
    assert c.get('/api/dashboard').status_code==401
    assert c.post('/api/login',json={'email':'demo@logscope.local','password':'wrong'}).status_code==401
    c=client()
    assert c.get('/api/session').json()['email']=='demo@logscope.local'
    assert c.get('/api/dashboard').json()['metrics']['requests']>0
    assert c.get('/api/traffic').status_code==200
    assert len(c.get('/api/alarms').json()['alarms'])>0
    assert c.get('/').status_code==200
    assert c.post('/api/logout').status_code==200
    assert c.get('/api/session').status_code==401


def test_alarm_review_and_csv_and_filter():
    c=client()
    alarm=c.get('/api/alarms').json()['alarms'][0]
    id_=alarm['id'];payload={'state':'Doğrulandı','note':'Kontrollü deney notu'}
    r=c.post(f'/api/alarms/{id_}/review',json=payload)
    assert r.status_code==200,r.text
    d=c.get(f'/api/alarms/{id_}').json()
    assert d['state']=='Doğrulandı'
    assert any('Kontrollü' in rev['note'] for rev in d['reviews'])
    assert c.get('/api/alarms',params={'state':'Doğrulandı'}).status_code==200
    assert c.post('/api/alarms/MISSING/review',json=payload).status_code==404
    assert c.get('/api/export/alarms.csv').content.startswith(b'\xef\xbb\xbf')
    assert c.get('/api/export/traffic.csv').status_code==200


def test_upload_whitelist_and_duplicate():
    c=client()
    sample={'event_uid':'pytest-unique-1001','occurred_at':'2026-10-28T14:00:00Z','http_method':'GET','route_template':'/catalog/',
            'status_code':200,'duration_ms':124.3,'session_ref':'anonymous_10','schema_version':'1.0'}
    forbidden={**sample,'event_uid':'pytest-unique-1002','ip_address':'192.168.1.8'}
    bad={**sample,'event_uid':'pytest-unique-1003','route_template':'/secret/?token=abc'}
    body='\n'.join(map(json.dumps,[sample,forbidden,bad,sample]))+'\n'
    r=c.post('/api/ingest',files={'file':('sample.jsonl',body,'application/x-ndjson')})
    assert r.status_code==200,r.text
    assert r.json()['accepted'] in (0,1)  # test repeat-safe
    assert r.json()['rejected']>=3
    assert c.get('/api/batches').status_code==200
    events=c.get('/api/traffic',params={'route':'/catalog/'}).json()['events']
    assert all('ip_address' not in event for event in events)
    assert c.post('/api/ingest',files={'file':('bad.txt','x','text/plain')}).status_code==400


def test_research_experiment():
    c=client()
    r=c.post('/api/experiments/run',json={'windows':1200,'requests_per_window':100,'seed':42})
    assert r.status_code==200,r.text
    d=r.json()['result']
    assert d['trained'] and d['data']['windows']==1200
    assert d['data']['total_http_requests']>=120000
    assert d['data']['train_windows']==720 and d['data']['validation_windows']==240 and d['data']['test_windows']==240
    assert set(d['conditions'])=={'B0','B1','B1+D','B1+S','B2'}
    assert all(0<=v['f1']<=1 and 0<=v['normal_fpr']<=1 for v in d['conditions'].values())
    assert d['learned_patterns']
    assert c.get('/api/models').json()['trained']
    assert c.get('/api/experiments').json()['experiments']
    assert c.get('/api/experiments/'+str(r.json()['run_id'])).status_code==200
    assert c.get('/api/export/experiments.csv').status_code==200
    assert c.get('/api/alarms').json()['total']>=38
    assert c.post('/api/experiments/run',json={'windows':5}).status_code==422


def test_team_notifications_settings_onboarding_and_integrations():
    c=client()
    r=c.post('/api/team/invitations',json={'email':'example@sample.org','role':'reviewer'})
    assert r.status_code==200 and not r.json()['email_sent']
    assert any(x['email']=='example@sample.org' for x in c.get('/api/team').json()['invitations'])
    r=c.post('/api/integrations',json={'provider':'django','name':'Django Test','status':'configured'})
    assert r.status_code==200 and not r.json()['live_connection']
    assert any(x['provider']=='django' for x in c.get('/api/integrations').json()['integrations'])
    assert c.put('/api/onboarding',json={'step':2,'workspace_name':'LogScope Eğitim','source_type':'jsonl','privacy_checked':True}).status_code==200
    assert c.get('/api/onboarding').json()['step']==2
    assert c.put('/api/settings',json={'name':'LogScope Eğitim','timezone':'UTC','retention_days':30}).status_code==200
    assert c.get('/api/settings').json()['timezone']=='UTC'
    notify=c.get('/api/notifications').json()['notifications'];assert notify
    assert c.post('/api/notifications/'+str(notify[0]['id'])+'/toggle').status_code==200
    assert c.post('/api/notifications/read-all').status_code==200
    assert c.get('/api/notifications').json()['unread']==0


def test_registration_isolation_and_password_reset():
    c=TestClient(app)
    email='separate.account@sample.org'
    r=c.post('/api/register',json={'name':'Other Workspace','email':email,'password':'DifferentPwd123!','workspace':'Team isolated'})
    assert r.status_code in (200,409),r.text
    if r.status_code==409:
        r=c.post('/api/login',json={'email':email,'password':'DifferentPwd123!'})
        assert r.status_code==200,r.text
    assert c.get('/api/alarms').json()['total']==0
    assert c.get('/api/dashboard').json()['metrics']['alarms']==0
    assert c.get('/api/alarms/LS-1042').status_code==404
    token_res=c.post('/api/password/reset/request',json={'email':email})
    assert token_res.status_code==200
    token=token_res.json().get('demo_token');assert token
    assert c.post('/api/password/reset/confirm',json={'token':token,'new_password':'NewSecurePwd1234!'}).status_code==200
    assert c.post('/api/login',json={'email':email,'password':'NewSecurePwd1234!'}).status_code==200


def test_pattern_miner_and_splits():
    patterns=prefixspan([('a','b','c'),('a','b'),('a','c'),('a','b','c')],min_support=.5,max_length=3)
    assert any(x['sequence']==['a','b'] and x['support_count']==3 for x in patterns)
    assert subsequence(('a','c'),('a','b','c'))
    w=synthetic_windows(1200,100,42)
    assert len(set(x.scenario for x in w[:720]))==8
    assert len(set(x.scenario for x in w[720:960]))==8
    assert len(set(x.scenario for x in w[960:]))==8
    assert all(len(x.feature_vector())==10 for x in w)


def test_unlabeled_ingested_m1_to_m4():
    from datetime import datetime, timezone, timedelta
    c = client()
    # Two HTTP events per minute, 60 distinct minute windows; never a target label.
    start = datetime(2026, 10, 20, 11, 0, tzinfo=timezone.utc)
    rows=[]
    for i in range(60):
        for j in range(2):
            event={
                'event_uid':f'raw-window-{i}-{j}',
                'occurred_at':(start+timedelta(minutes=i,seconds=j)).isoformat(),
                'http_method':'GET' if j==0 else 'POST',
                'route_template':'/catalog/' if j==0 else '/auth/login/',
                'status_code':503 if i>48 and j==1 else 200,
                'duration_ms':102.3 if i<48 else 725.2,
                'session_ref':f'window_session_{i}',
                'schema_version':'1.0'
            }
            rows.append(json.dumps(event))
    payload='\n'.join(rows)+'\n'
    imp=c.post('/api/ingest',files={'file':('observed.jsonl',payload,'application/x-ndjson')})
    assert imp.status_code==200,imp.text
    assert imp.json()['accepted']==120
    result=c.post('/api/ingested/analyze')
    assert result.status_code==200,result.text
    data=result.json()['result']
    assert data['mode']=='ingested_unlabeled_analysis'
    assert data['data']['minutes']>=60
    assert data['data']['events']>=120
    assert 'conditions' not in data
    assert 'f1' not in data
    assert all(k in a for a in data['alarms'] for k in ('m1','m2','m3','score'))
    assert c.get('/api/ingested/analyses').json()['runs']
    assert c.get('/api/export/ingested.csv').status_code==200
