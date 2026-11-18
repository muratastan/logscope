"""HTTP-level access controls and input checks for the week-4 FastAPI MVP."""
import json
import secrets
from fastapi.testclient import TestClient
from sqlalchemy import insert,select
from backend.fullstack import app,engine,users,memberships,workspaces,hash_pw,now,DEMO_EMAIL


def signed():
    c=TestClient(app)
    r=c.post('/api/login',json={'email':'demo@logscope.local','password':'Demo2026!'})
    assert r.status_code==200,r.text
    return c


def test_swagger_health_and_session_protection():
    c=TestClient(app)
    assert c.get('/api/health').json()['ok']
    assert c.get('/api/openapi.json').status_code==200
    assert c.get('/api/docs').status_code==200
    assert c.get('/api/alarms').status_code==401
    user=signed()
    assert user.get('/api/session').status_code==200
    cookie=user.cookies.get('logscope_mvp_session')
    assert cookie
    user.post('/api/logout')
    assert user.get('/api/alarms').status_code==401


def test_local_origin_guard_and_credentials_not_exposed():
    c=TestClient(app)
    data={'email':DEMO_EMAIL,'password':'Demo2026!'}
    assert c.post('/api/login',json=data,headers={'Origin':'https://external-attacker.example'}).status_code==403
    r=c.post('/api/login',json=data,headers={'Origin':'http://127.0.0.1:5173'})
    assert r.status_code==200,r.text
    assert 'httponly' in r.headers.get('set-cookie','').lower()
    assert 'password_hash' not in r.text


def test_login_rate_limit_with_distinct_nonexisting_identity():
    c=TestClient(app)
    email='not-real-'+secrets.token_hex(8)+'@none.example'
    codes=[]
    for i in range(8):
        codes.append(c.post('/api/login',json={'email':email,'password':'anything'}).status_code)
    assert codes[:7]==[401]*7
    assert codes[7]==429


def test_readonly_reviewer_cannot_import_or_train():
    with engine.begin() as conn:
        admin=conn.execute(select(users.c.id).where(users.c.email==DEMO_EMAIL)).scalar_one()
        workspace=conn.execute(select(workspaces.c.id).where(workspaces.c.owner_user_id==admin)).scalar_one()
        email='reviewer.'+secrets.token_hex(6)+'@example.test'
        uid=conn.execute(insert(users).values(email=email,display_name='Classroom Reviewer',
                          password_hash=hash_pw('ReviewerSecure123!'),role='analyst',created_at=now())).inserted_primary_key[0]
        conn.execute(insert(memberships).values(workspace_id=workspace,user_id=uid,role='reviewer'))
    c=TestClient(app)
    assert c.post('/api/login',json={'email':email,'password':'ReviewerSecure123!'}).status_code==200
    assert c.get('/api/alarms').status_code==200
    assert c.post('/api/experiments/run',json={'windows':120,'requests_per_window':40,'seed':2}).status_code==403
    assert c.post('/api/ingested/analyze').status_code==403
    event={'event_uid':'reviewer-test','occurred_at':'2026-10-28T15:00:00Z','http_method':'GET',
           'route_template':'/catalog/','status_code':200,'duration_ms':90,'session_ref':'syn-session','schema_version':'1.0'}
    result=c.post('/api/ingest',files={'file':('events.jsonl',json.dumps(event),'application/x-ndjson')})
    assert result.status_code==403
    assert c.post('/api/team/invitations',json={'email':'new@example.org','role':'analyst'}).status_code==403
