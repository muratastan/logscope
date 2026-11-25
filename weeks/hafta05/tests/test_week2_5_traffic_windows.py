"""Week 3/5: aggregation tests against real persisted (synthetic) event rows."""
import json
import secrets
from fastapi.testclient import TestClient
from backend.fullstack import app


def test_imported_traffic_minute_route_and_privacy():
    c=TestClient(app)
    salt=secrets.token_hex(4)
    res=c.post('/api/register',json={'name':'Analiz Test','email':f'window-{salt}@sample.org',
                                     'password':'WindowSecure123!','workspace':'İzole test'})
    assert res.status_code==200,res.text
    assert c.get('/api/traffic/windows').json()['points']==[]
    events=[
      {'event_uid':f'{salt}-001','occurred_at':'2026-10-28T14:00:02Z','http_method':'GET','route_template':'/catalog/',
       'status_code':200,'duration_ms':100.0,'session_ref':'sessA','schema_version':'1.0'},
      {'event_uid':f'{salt}-002','occurred_at':'2026-10-28T14:00:11Z','http_method':'GET','route_template':'/catalog/',
       'status_code':503,'duration_ms':900.0,'session_ref':'sessB','schema_version':'1.0'},
      {'event_uid':f'{salt}-003','occurred_at':'2026-10-28T14:00:17Z','http_method':'POST','route_template':'/auth/login/',
       'status_code':401,'duration_ms':300.0,'session_ref':'sessB','schema_version':'1.0'},
      {'event_uid':f'{salt}-004','occurred_at':'2026-10-28T14:01:19Z','http_method':'GET','route_template':'/catalog/',
       'status_code':200,'duration_ms':200.0,'session_ref':'sessA','schema_version':'1.0'},
    ]
    body='\n'.join(json.dumps(x) for x in events)+'\n'
    imported=c.post('/api/ingest',files={'file':('test.jsonl',body,'application/x-ndjson')})
    assert imported.status_code==200,imported.text
    assert imported.json()['accepted']==4
    out=c.get('/api/traffic/windows').json()
    assert out['source']=='imported_jsonl' and out['total_events']==4 and out['window_count']==2
    assert set(out['routes'])=={'/catalog/','/auth/login/'}
    p=out['points'][0]
    assert (p['requests'],p['errors'],p['count_4xx'],p['count_5xx'])==(3,2,1,1)
    assert p['distinct_sessions']==2 and p['route_diversity']==2
    assert p['p50_ms']==300.0 and p['p95_ms']==840.0
    assert 'ip_address' not in json.dumps(out)
    cat=c.get('/api/traffic/windows',params={'route':'/catalog/','limit':1}).json()
    assert cat['window_count']==1 and cat['points'][0]['requests']==1
    assert c.get('/api/traffic/windows',params={'route':'/absent/'}).json()['points']==[]


def test_traffic_windows_requires_session():
    c=TestClient(app)
    assert c.get('/api/traffic/windows').status_code==401
