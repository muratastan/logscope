"""LogScope full-stack classroom MVP: real persisted REST endpoints and ML trials.

The canonical 27-table PostgreSQL *research schema* is under db/*.sql.
This operational UI adapter uses portable, isolated `ui_` tables in the same
PostgreSQL database (or SQLite for local no-install demo). Its records do not
pretend to be the canonical research experiment tables. They can be mapped to
those canonical tables in a later migration.
"""
from __future__ import annotations
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Literal
import csv
import hashlib
import threading
from collections import deque
import hmac
import io
import json
import os
import random
import re
import secrets
import time
import numpy as np

from fastapi import Cookie, Depends, FastAPI, File, HTTPException, Request, Response, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy import (create_engine, MetaData, Table, Column, Integer, Float, String,
                        Text, Boolean, ForeignKey, select, insert, update, delete, func, and_)
from sqlalchemy.exc import IntegrityError

from .analysis import run_experiment, analyze_ingested_events, SCENARIOS
from .event_contract import valid_event
from .research_training import score_persisted_events

ROOT = Path(__file__).resolve().parent.parent
os.environ.setdefault('LOGSCOPE_DATABASE_URL',f'sqlite:///{ROOT / "backend" / "logscope_fullstack.sqlite3"}')
DB_URL = os.environ['LOGSCOPE_DATABASE_URL']
engine=create_engine(DB_URL,future=True,pool_pre_ping=True,connect_args={'check_same_thread':False} if DB_URL.startswith('sqlite') else {})
metadata=MetaData()
COOKIE='logscope_mvp_session'
DEMO_EMAIL='demo@logscope.local'
DEMO_PASSWORD=os.environ.get('LOGSCOPE_DEMO_PASSWORD','Demo2026!')
DEMO_MODE=os.environ.get('LOGSCOPE_DEMO_MODE','1')=='1'
if not DEMO_MODE and not os.environ.get('LOGSCOPE_DEMO_PASSWORD'):
    raise RuntimeError('LOGSCOPE_DEMO_PASSWORD must be explicit when demo mode is off')
ROUTES=['/auth/login/','/catalog/','/search/','/items/{id}/','/forms/checkout/']
ALLOWED_EVENT_KEYS={'event_uid','occurred_at','http_method','route_template','status_code','duration_ms','session_ref','schema_version'}
STATES=['Yeni','İnceleniyor','Doğrulandı','Yanlış alarm']
SEVERITIES=['Kritik','Yüksek','Orta','Düşük']
app=FastAPI(title='LogScope Full Stack MVP API',version='0.7.0',docs_url='/api/docs',openapi_url='/api/openapi.json',redoc_url=None)

# Browser requests with an Origin are limited to the local React/API development origins.
# This guards against cross-origin POSTs using the session cookie. Production URLs
# must be set explicitly using LOGSCOPE_ALLOWED_ORIGINS; never use a wildcard.
_DEFAULT_ORIGINS='http://127.0.0.1:5173,http://localhost:5173,http://127.0.0.1:8000,http://localhost:8000'
_ALLOWED_ORIGINS=set(x.strip() for x in os.getenv('LOGSCOPE_ALLOWED_ORIGINS',_DEFAULT_ORIGINS).split(',') if x.strip())
_LOGIN_ATTEMPTS={}
_LOGIN_LOCK=threading.Lock()

def _login_limit(client_host, email):
    key=(client_host, email.strip().lower())
    current=time.monotonic()
    with _LOGIN_LOCK:
        attempts=_LOGIN_ATTEMPTS.setdefault(key,deque())
        while attempts and current-attempts[0]>60:attempts.popleft()
        if len(attempts)>=7:raise HTTPException(429,'Çok sayıda giriş denemesi; bir dakika sonra tekrar deneyin')
        return key

def _login_failure(key):
    with _LOGIN_LOCK:
        _LOGIN_ATTEMPTS.setdefault(key,deque()).append(time.monotonic())

def _login_success(key):
    with _LOGIN_LOCK:
        _LOGIN_ATTEMPTS.pop(key,None)

@app.middleware('http')
async def origin_guard(request:Request, call_next):
    origin=request.headers.get('origin')
    if request.method in ('POST','PUT','PATCH','DELETE') and origin and origin not in _ALLOWED_ORIGINS:
        return Response(status_code=403,content='Origin not allowed')
    return await call_next(request)



def T(name,*cols):return Table('ui_'+name,metadata,*cols)
users=T('users',Column('id',Integer,primary_key=True),Column('email',String(254),unique=True,nullable=False),
        Column('password_hash',Text,nullable=False),Column('display_name',String(140),nullable=False),
        Column('role',String(16),nullable=False,default='analyst'),Column('created_at',String(40),nullable=False))
sessions=T('sessions',Column('token_hash',String(64),primary_key=True),Column('user_id',Integer,ForeignKey('ui_users.id'),nullable=False),
           Column('expires_at',String(40),nullable=False))
workspaces=T('workspaces',Column('id',Integer,primary_key=True),Column('name',String(140),nullable=False),
             Column('owner_user_id',Integer,ForeignKey('ui_users.id'),nullable=False),Column('timezone',String(80),default='Europe/Istanbul'),
             Column('retention_days',Integer,default=30),Column('created_at',String(40),nullable=False))
memberships=T('memberships',Column('id',Integer,primary_key=True),Column('workspace_id',Integer,ForeignKey('ui_workspaces.id'),nullable=False),
              Column('user_id',Integer,ForeignKey('ui_users.id'),nullable=False),Column('role',String(20),nullable=False))
invitations=T('invitations',Column('id',Integer,primary_key=True),Column('workspace_id',Integer,ForeignKey('ui_workspaces.id'),nullable=False),
              Column('email',String(254),nullable=False),Column('role',String(20),nullable=False),Column('status',String(20),nullable=False),
              Column('invited_at',String(40),nullable=False))
reset_tokens=T('reset_tokens',Column('token_hash',String(64),primary_key=True),Column('user_id',Integer,ForeignKey('ui_users.id'),nullable=False),
               Column('expires_at',String(40),nullable=False),Column('used',Boolean,nullable=False,default=False))
notifications=T('notifications',Column('id',Integer,primary_key=True),Column('workspace_id',Integer,ForeignKey('ui_workspaces.id'),nullable=False),
                Column('user_id',Integer,ForeignKey('ui_users.id'),nullable=False),Column('title',String(180),nullable=False),
                Column('text',Text,nullable=False),Column('kind',String(30),nullable=False),Column('created_at',String(40),nullable=False),
                Column('read',Boolean,nullable=False,default=False))
integrations=T('integrations',Column('id',Integer,primary_key=True),Column('workspace_id',Integer,ForeignKey('ui_workspaces.id'),nullable=False),
               Column('provider',String(40),nullable=False),Column('name',String(140),nullable=False),
               Column('status',String(30),nullable=False),Column('safe_config',Text,nullable=False,default='{}'))
onboarding=T('onboarding',Column('id',Integer,primary_key=True),Column('workspace_id',Integer,ForeignKey('ui_workspaces.id'),nullable=False),
             Column('step',Integer,nullable=False,default=0),Column('source_type',String(40),nullable=False,default='jsonl'),
             Column('privacy_checked',Boolean,nullable=False,default=False))
traffic=T('traffic',Column('id',Integer,primary_key=True),Column('workspace_id',Integer,ForeignKey('ui_workspaces.id'),nullable=False),
         Column('ts',String(40),nullable=False),Column('requests',Integer,nullable=False),Column('errors',Integer,nullable=False),
         Column('latency_ms',Float,nullable=False),Column('route',String(160),nullable=False))
alarms=T('alarms',Column('id',String(50),primary_key=True),Column('workspace_id',Integer,ForeignKey('ui_workspaces.id'),nullable=False),
        Column('occurred_at',String(40),nullable=False),Column('route',String(160),nullable=False),
        Column('severity',String(20),nullable=False),Column('reason',Text,nullable=False),Column('score',Float,nullable=False),
        Column('state',String(30),nullable=False),Column('m1',Float,nullable=False),Column('m2',Float,nullable=False),
        Column('m3',Float,nullable=False),Column('evidence',Text,nullable=False),Column('notes',Text,nullable=False,default=''),
        Column('source',String(35),nullable=False,default='demo'))
reviews=T('reviews',Column('id',Integer,primary_key=True),Column('alarm_id',String(50),ForeignKey('ui_alarms.id'),nullable=False),
          Column('user_id',Integer,ForeignKey('ui_users.id'),nullable=False),Column('state',String(30),nullable=False),
          Column('note',Text,nullable=False),Column('created_at',String(40),nullable=False))
batches=T('batches',Column('id',Integer,primary_key=True),Column('workspace_id',Integer,ForeignKey('ui_workspaces.id'),nullable=False),
          Column('filename',String(120),nullable=False),Column('accepted',Integer,nullable=False),
          Column('rejected',Integer,nullable=False),Column('created_at',String(40),nullable=False))
events=T('events',Column('id',Integer,primary_key=True),Column('workspace_id',Integer,ForeignKey('ui_workspaces.id'),nullable=False),
         Column('uid',String(96),unique=True,nullable=False),Column('batch_id',Integer,ForeignKey('ui_batches.id'),nullable=False),
         Column('occurred_at',String(40),nullable=False),Column('method',String(8),nullable=False),
         Column('route',String(160),nullable=False),Column('status',Integer,nullable=False),
         Column('duration_ms',Float,nullable=False),Column('session_ref',String(80)))
event_analyses=T('event_analyses',Column('id',Integer,primary_key=True),Column('workspace_id',Integer,ForeignKey('ui_workspaces.id'),nullable=False),Column('created_at',String(40),nullable=False),Column('result_json',Text,nullable=False))
experiments=T('experiments',Column('id',Integer,primary_key=True),Column('workspace_id',Integer,ForeignKey('ui_workspaces.id'),nullable=False),
              Column('started_at',String(40),nullable=False),Column('duration_ms',Float,nullable=False),
              Column('windows',Integer,nullable=False),Column('requests',Integer,nullable=False),Column('result_json',Text,nullable=False))


def now():return datetime.now(timezone.utc).isoformat()

def hash_pw(password,salt=None):
    salt=salt or secrets.token_bytes(16)
    return f'{salt.hex()}:{hashlib.pbkdf2_hmac("sha256",password.encode(),salt,250000).hex()}'

def verify_pw(password,stored):
    try:
        s,h=stored.split(':')
        return hmac.compare_digest(hashlib.pbkdf2_hmac('sha256',password.encode(),bytes.fromhex(s),250000).hex(),h)
    except (ValueError,TypeError):return False

def public_user(u):return {'id':u['id'],'email':u['email'],'display_name':u['display_name'],'role':u['role']}

def seed_workspace(c,user_id,display_name='Demo Workspace',with_demo=False):
    ws_id=c.execute(insert(workspaces).values(name=display_name,owner_user_id=user_id,timezone='Europe/Istanbul',retention_days=30,created_at=now())).inserted_primary_key[0]
    c.execute(insert(memberships).values(workspace_id=ws_id,user_id=user_id,role='owner'))
    c.execute(insert(onboarding).values(workspace_id=ws_id,step=0,source_type='jsonl',privacy_checked=False))
    if with_demo:
        rng=random.Random(20261028)
        stamp=datetime(2026,10,28,14,0,tzinfo=timezone.utc)
        for j in range(144):
            peak=1+.38*max(0,1-abs(j-93)/38)
            cnt=max(1,int((350+75*__import__('math').sin(j/11)+rng.randint(-28,28))*peak))
            err=rng.randint(0,13)+(rng.randint(20,45) if 72<=j<=76 else 0)
            c.execute(insert(traffic).values(workspace_id=ws_id,ts=(stamp-timedelta(minutes=10*(143-j))).isoformat(),requests=cnt,errors=err,latency_ms=round(rng.uniform(120,220),1),route='Tümü'))
        reasons=['Başarısız giriş artışı','5xx hata oranında sapma','Nadir rota geçişi','Yanıt gecikmesinde artış','Yoğunluk profili sapması']
        for i in range(38):
            a_id=f'LS-{1042-i}'
            c.execute(insert(alarms).values(id=a_id,workspace_id=ws_id,occurred_at=(stamp-timedelta(minutes=17*i+7)).isoformat(),
                 route=ROUTES[i%len(ROUTES)],severity=SEVERITIES[i%len(SEVERITIES)],reason=reasons[i%len(reasons)],
                 score=round(.55+rng.random()*.43,4),state='Yeni' if i%4 else 'İnceleniyor',m1=round(rng.random(),4),
                 m2=round(rng.random(),4),m3=round(rng.random(),4),
                 evidence=json.dumps({'note':'Sentetik gösterim. Eğitilmiş model çıktısı değildir.'},ensure_ascii=False),notes='',source='demo'))
        for title,body,kind in [('Kritik alarm','LS-1042 için örnek bildirim','alarm'),('Örnek JSONL akışı','Sentetik dosya yüklemeye hazır','ingestion'),('Deney planı','B2 karşılaştırması planlandı','experiment')]:
            c.execute(insert(notifications).values(workspace_id=ws_id,user_id=user_id,title=title,text=body,kind=kind,created_at=now(),read=False))
    return ws_id

def init_db():
    metadata.create_all(engine)
    with engine.begin() as c:
        existing=c.execute(select(users.c.id).where(users.c.email==DEMO_EMAIL)).first()
        if not existing and DEMO_MODE:
            uid=c.execute(insert(users).values(email=DEMO_EMAIL,password_hash=hash_pw(DEMO_PASSWORD),display_name='Demo Analist',role='admin',created_at=now())).inserted_primary_key[0]
            seed_workspace(c,uid,with_demo=True)

init_db()


def auth(logscope_mvp_session: str|None=Cookie(default=None)):
    if not logscope_mvp_session:raise HTTPException(401,'Giriş gerekli')
    digest=hashlib.sha256(logscope_mvp_session.encode()).hexdigest()
    with engine.connect() as c:
        data=c.execute(select(users,sessions.c.expires_at).join(sessions,sessions.c.user_id==users.c.id)
            .where(and_(sessions.c.token_hash==digest,sessions.c.expires_at>now()))).mappings().first()
        if not data:raise HTTPException(401,'Oturum geçersiz')
        m=c.execute(select(memberships.c.workspace_id,memberships.c.role).where(memberships.c.user_id==data['id']).order_by(memberships.c.id)).first()
        if not m:raise HTTPException(403,'Çalışma alanı erişimi yok')
        return {**public_user(data),'workspace_id':int(m[0]),'workspace_role':m[1]}

def admin(user):
    if user['workspace_role'] not in ('owner','admin'):raise HTTPException(403,'Yönetici yetkisi gerekli')

def analyst(user):
    if user['workspace_role'] not in ('owner','admin','analyst'):raise HTTPException(403,'Analist veya yönetici yetkisi gerekli')


def rowdict(row):return dict(row) if row is not None else None

def as_int(x,minimum,maximum):return max(minimum,min(maximum,int(x)))

def record_notify(c,u,title,text_value,kind='system'):
    c.execute(insert(notifications).values(workspace_id=u['workspace_id'],user_id=u['id'],title=title[:180],text=text_value[:700],kind=kind,created_at=now(),read=False))

class LoginPayload(BaseModel):
    email:str=Field(max_length=254)
    password:str=Field(min_length=1,max_length=200)

class RegisterPayload(BaseModel):
    name:str=Field(min_length=2,max_length=140)
    email:str=Field(max_length=254)
    password:str=Field(min_length=8,max_length=200)
    workspace:str=Field(min_length=2,max_length=140)

class ResetRequest(BaseModel):email:str=Field(max_length=254)
class ResetConfirm(BaseModel):token:str=Field(max_length=128);new_password:str=Field(min_length=8,max_length=200)
class ReviewPayload(BaseModel):state:Literal['Yeni','İnceleniyor','Doğrulandı','Yanlış alarm'];note:str=Field(max_length=800)
class InvitePayload(BaseModel):email:str=Field(max_length=254);role:Literal['analyst','reviewer','admin']
class IntegrationPayload(BaseModel):provider:Literal['django','rest_api','locust','postgresql','jsonl','webhook'];status:Literal['draft','configured','disabled'];name:str=Field(max_length=120)
class IntegrationPatch(BaseModel):
    name:str|None=Field(default=None,min_length=1,max_length=120)
    status:Literal['draft','configured','disabled']|None=None
class OnboardingPayload(BaseModel):step:int=Field(ge=0,le=4);workspace_name:str|None=Field(default=None,max_length=140);source_type:Literal['jsonl','django','rest_api']='jsonl';privacy_checked:bool=False
class SettingsPayload(BaseModel):name:str=Field(min_length=2,max_length=140);timezone:Literal['Europe/Istanbul','UTC']='Europe/Istanbul';retention_days:int=Field(ge=1,le=365)
class ExperimentPayload(BaseModel):windows:int=Field(default=1200,ge=120,le=2400);requests_per_window:int=Field(default=100,ge=10,le=500);seed:int=Field(default=42,ge=0,le=2147483647)

@app.get('/api/health')
def health():return {'ok':True,'mode':'classroom_mvp','storage':'postgresql' if engine.dialect.name=='postgresql' else 'sqlite','models':'executable_synthetic_experiment'}

@app.post('/api/login')
def login(p:LoginPayload,res:Response,request:Request):
    client_host=request.client.host if request.client else 'unknown'
    key=_login_limit(client_host,p.email)
    with engine.begin() as c:
        user=c.execute(select(users).where(func.lower(users.c.email)==p.email.strip().lower())).mappings().first()
        if not user or not verify_pw(p.password,user['password_hash']):
            _login_failure(key)
            raise HTTPException(401,'E-posta veya parola geçersiz')
        token=secrets.token_urlsafe(36)
        c.execute(insert(sessions).values(token_hash=hashlib.sha256(token.encode()).hexdigest(),user_id=user['id'],expires_at=(datetime.now(timezone.utc)+timedelta(hours=12)).isoformat()))
    _login_success(key)
    res.set_cookie(COOKIE,token,httponly=True,secure=os.getenv('LOGSCOPE_HTTPS','0')=='1',samesite='lax',max_age=43200,path='/')
    return {'ok':True,'user':public_user(user),'mode':'authenticated'}

@app.post('/api/register')
def register(p:RegisterPayload,res:Response,request:Request):
    if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',p.email.strip()):raise HTTPException(422,'Geçerli e-posta girin')
    with engine.begin() as c:
        try:
            uid=c.execute(insert(users).values(email=p.email.strip().lower(),display_name=p.name.strip(),role='admin',password_hash=hash_pw(p.password),created_at=now())).inserted_primary_key[0]
        except IntegrityError:raise HTTPException(409,'Bu e-posta zaten kayıtlı')
        seed_workspace(c,uid,p.workspace.strip())
    return login(LoginPayload(email=p.email,password=p.password),res,request)

@app.post('/api/logout')
def logout(res:Response,user=Depends(auth),logscope_mvp_session:str|None=Cookie(default=None)):
    if logscope_mvp_session:
        with engine.begin() as c:c.execute(delete(sessions).where(sessions.c.token_hash==hashlib.sha256(logscope_mvp_session.encode()).hexdigest()))
    res.delete_cookie(COOKIE,path='/')
    return {'ok':True}

@app.get('/api/session')
def session(user=Depends(auth)):return user

@app.post('/api/password/reset/request')
def reset_request(p:ResetRequest):
    token=secrets.token_urlsafe(26)
    with engine.begin() as c:
        user=c.execute(select(users.c.id).where(users.c.email==p.email.strip().lower())).first()
        if user:
            c.execute(insert(reset_tokens).values(user_id=user[0],token_hash=hashlib.sha256(token.encode()).hexdigest(),expires_at=(datetime.now(timezone.utc)+timedelta(minutes=15)).isoformat(),used=False))
    result={'ok':True,'message':'Hesap varsa sıfırlama isteği oluşturuldu. E-posta hizmeti bağlı değil.'}
    if DEMO_MODE and user:result['demo_token']=token
    return result

@app.post('/api/password/reset/confirm')
def reset_confirm(p:ResetConfirm):
    digest=hashlib.sha256(p.token.encode()).hexdigest()
    with engine.begin() as c:
        row=c.execute(select(reset_tokens).where(and_(reset_tokens.c.token_hash==digest,reset_tokens.c.expires_at>now(),reset_tokens.c.used==False))).mappings().first()
        if not row:raise HTTPException(400,'Kod geçersiz veya süresi dolmuş')
        c.execute(update(users).where(users.c.id==row['user_id']).values(password_hash=hash_pw(p.new_password)))
        c.execute(update(reset_tokens).where(reset_tokens.c.token_hash==digest).values(used=True))
        c.execute(delete(sessions).where(sessions.c.user_id==row['user_id']))
    return {'ok':True}

@app.get('/api/dashboard')
def dashboard(range:str='24h',user=Depends(auth)):
    cutoff={'1h':6,'6h':36,'24h':144}.get(range,144);wid=user['workspace_id']
    with engine.connect() as c:
        rows=[dict(r) for r in c.execute(select(traffic).where(traffic.c.workspace_id==wid).order_by(traffic.c.ts.desc()).limit(cutoff)).mappings()][::-1]
        aa=[dict(r) for r in c.execute(select(alarms).where(alarms.c.workspace_id==wid).order_by(alarms.c.occurred_at.desc()).limit(5)).mappings()]
        total=c.execute(select(func.count()).select_from(alarms).where(alarms.c.workspace_id==wid)).scalar_one()
        pending=c.execute(select(func.count()).select_from(alarms).where(and_(alarms.c.workspace_id==wid,alarms.c.state.in_(['Yeni','İnceleniyor'])))).scalar_one()
        event_count=c.execute(select(func.count()).select_from(events).where(events.c.workspace_id==wid)).scalar_one()
        run=c.execute(select(experiments).where(experiments.c.workspace_id==wid).order_by(experiments.c.id.desc()).limit(1)).mappings().first()
    req=sum(r['requests'] for r in rows);err=sum(r['errors'] for r in rows)
    return {'source':'seeded_demo' if not run else 'seeded_demo_plus_experiment', 'metrics':{'requests':req,'errorRate':round(100*err/max(1,req),2),'p95':max((r['latency_ms'] for r in rows),default=0),'alarms':total,'open':pending,'importedEvents':event_count},'timeline':rows,'recent':aa,'routes':[{'path':p,'requests':round(req*r)} for p,r in zip(ROUTES,[.28,.25,.2,.16,.11])], 'latest_experiment_id':run['id'] if run else None}

@app.get('/api/traffic')
def traffic_endpoint(range:str='24h',route:str='Tümü',user=Depends(auth)):
    wid=user['workspace_id'];cutoff={'1h':6,'6h':36,'24h':144}.get(range,144)
    with engine.connect() as c:
        points=[dict(r) for r in c.execute(select(traffic).where(traffic.c.workspace_id==wid).order_by(traffic.c.ts.desc()).limit(cutoff)).mappings()][::-1]
        query=select(events).where(events.c.workspace_id==wid).order_by(events.c.occurred_at.desc()).limit(50)
        if route!='Tümü':query=query.where(events.c.route==route)
        ev=[dict(r) for r in c.execute(query).mappings()]
    return {'source':'persisted_demo_and_imports','points':points,'events':ev,'routes':ROUTES}

@app.get('/api/traffic/windows')
def traffic_windows_endpoint(route:str='Tümü',limit:int=1200,user=Depends(auth)):
    """Actual aggregated imported HTTP events, per UTC minute (not demo samples).

    The 27-table canonical schema is still the PostgreSQL research model; this
    operation groups only the authenticated workspace's operational ui_events.
    """
    limit=as_int(limit,1,2400)
    wid=user['workspace_id']
    with engine.connect() as c:
        # Select only private-field-free columns. Bounded to the maximum upload scope.
        all_rows=c.execute(select(events.c.occurred_at,events.c.route,events.c.status,
                events.c.duration_ms,events.c.session_ref).where(events.c.workspace_id==wid)
                .order_by(events.c.occurred_at.desc()).limit(200000)).all()
    # No source: return an explicit empty result. Do not replace it with demo metrics.
    if not all_rows:return {'source':'imported_jsonl','points':[],'routes':[],'total_events':0,'route':route}
    group={};seen_routes=set();all_points={}
    for timestamp,route_name,status,delay,session in all_rows:
        seen_routes.add(route_name)
        if route!='Tümü' and route!=route_name:continue
        try:
            instant=datetime.fromisoformat(timestamp.replace('Z','+00:00')).astimezone(timezone.utc)
        except (ValueError,TypeError):continue
        key=instant.replace(second=0,microsecond=0).isoformat()
        record=group.setdefault(key,{'duration':[],'status':[],'routes':set(),'sessions':set(),'times':[]})
        record['duration'].append(float(delay));record['status'].append(status)
        record['routes'].add(route_name)
        if session:record['sessions'].add(session)
        record['times'].append(instant)
    output=[]
    for minute,agg in sorted(group.items())[-limit:]:
        durations=np.asarray(agg['duration'],float)
        n=len(durations)
        count_4xx=sum(400<=v<500 for v in agg['status'])
        count_5xx=sum(v>=500 for v in agg['status'])
        arr=sorted(agg['times'])
        avg_gap=sum((arr[j]-arr[j-1]).total_seconds()*1000 for j in range(1,len(arr)))/max(1,len(arr)-1)
        output.append({'ts':minute,'requests':n,'errors':count_4xx+count_5xx,
                       'count_4xx':count_4xx,'count_5xx':count_5xx,
                       'p50_ms':round(float(np.percentile(durations,50)),3),
                       'p95_ms':round(float(np.percentile(durations,95)),3),
                       'distinct_sessions':len(agg['sessions']),
                       'route_diversity':len(agg['routes']),
                       'avg_interval_ms':round(avg_gap,2) if n>1 else None})
    return {'source':'imported_jsonl','points':output,'routes':sorted(seen_routes),
            'total_events':len(all_rows),'route':route,'window_count':len(output)}

@app.get('/api/alarms')
def alarm_list(q:str='',state:str='Tümü',severity:str='Tümü',user=Depends(auth)):
    wid=user['workspace_id'];q=q.lower().strip()[:100]
    with engine.connect() as c:
        rows=[dict(r) for r in c.execute(select(alarms).where(alarms.c.workspace_id==wid).order_by(alarms.c.occurred_at.desc())).mappings()]
    rows=[r for r in rows if (state=='Tümü' or r['state']==state) and (severity=='Tümü' or r['severity']==severity) and (not q or q in (' '.join(str(v) for v in r.values()).lower()))]
    return {'total':len(rows),'alarms':rows}

@app.get('/api/alarms/{alarm_id}')
def alarm_detail(alarm_id:str,user=Depends(auth)):
    with engine.connect() as c:
        row=c.execute(select(alarms).where(and_(alarms.c.id==alarm_id,alarms.c.workspace_id==user['workspace_id']))).mappings().first()
        if not row:raise HTTPException(404,'Alarm bulunamadı')
        rv=[dict(r) for r in c.execute(select(reviews).where(reviews.c.alarm_id==alarm_id).order_by(reviews.c.id.desc())).mappings()]
    return {**dict(row),'evidence':json.loads(row['evidence']), 'reviews':rv}

@app.post('/api/alarms/{alarm_id}/review')
def alarm_review(alarm_id:str,p:ReviewPayload,user=Depends(auth)):
    with engine.begin() as c:
        row=c.execute(select(alarms.c.id).where(and_(alarms.c.id==alarm_id,alarms.c.workspace_id==user['workspace_id']))).first()
        if not row:raise HTTPException(404,'Alarm bulunamadı')
        c.execute(update(alarms).where(alarms.c.id==alarm_id).values(state=p.state,notes=p.note))
        c.execute(insert(reviews).values(alarm_id=alarm_id,user_id=user['id'],state=p.state,note=p.note,created_at=now()))
        record_notify(c,user,'Alarm incelemesi güncellendi',f'{alarm_id}: {p.state}','alarm')
    return {'ok':True,'state':p.state}

@app.get('/api/research/week6')
def week6_results(user=Depends(auth)):
    """Read-only local research report, separately identified from demo trials.

    This endpoint never runs training, reads caller-controlled paths or exposes
    session-level data. All workspaces see the same public synthetic class report.
    """
    # Choose the most relevant report, never infer provenance from a filename.
    # The live report is preferred ONLY as a declared local Locust evaluation;
    # it is not independent proof of live HTTP collection.
    candidates=[('local_locust_declared','hafta6_live'),
                ('offline_main_5seed','ana_veri_model'),
                ('offline_previous_1seed','hafta6')]
    report_kind,report_path=next(
        ((kind,ROOT/'reports'/directory/'model_comparison.json') for kind,directory in candidates
         if (ROOT/'reports'/directory/'model_comparison.json').is_file()),
        (None,None))
    if report_path is None:
        return {'ready':False,'message':'Hafta 6 etiketli JSONL eğitim raporu henüz oluşturulmadı'}
    try:
        data=json.loads(report_path.read_text(encoding='utf-8'))
        if not isinstance(data,dict) or 'results_test_only' not in data:
            raise ValueError('Bad model report')
    except (OSError,ValueError,TypeError):
        raise HTTPException(503,'Hafta 6 raporu okunamıyor veya geçersiz')
    return {'ready':True,'report_kind':report_kind,
            'dataset_origin':data.get('dataset_origin','unverified'),
            'dataset_file':data.get('file_names',{}).get('jsonl',''),
            'data':data.get('data',{}),'results_test_only':data['results_test_only'],
            'scenario_breakdown_test_only':data.get('scenario_breakdown_test_only',{}),
            'comparison':data.get('comparison',{}),
            'protocol':data.get('protocol',''),
            'limitations':data.get('limitations',[])}


@app.get('/api/research/rolling-backtest')
def research_rolling_backtest(user=Depends(auth)):
    """Time-ordered offline robustness check; never a live validation claim."""
    location=ROOT/'reports'/'rolling_backtest'/'rolling_backtest_report.json'
    if not location.is_file():
        return {'ready':False,'message':'Kronolojik coklu test raporu henuz hazir degil'}
    try:
        report=json.loads(location.read_text(encoding='utf-8'))
        if not isinstance(report,dict) or report.get('num_folds',0)<1 or 'summaries' not in report:
            raise ValueError('Invalid rolling report')
    except (ValueError,OSError,TypeError):
        raise HTTPException(503,'Coklu test raporu okunamadi')
    return {'ready':True,'num_folds':report['num_folds'],
            'heldout_seeds':report.get('seed_heldouts',[]),
            'summaries':report['summaries'],
            'caveat':report.get('caveat',''),
            'primary_protocol_replaced':False}


@app.get('/api/models')
def models(user=Depends(auth)):
    with engine.connect() as c:row=c.execute(select(experiments).where(experiments.c.workspace_id==user['workspace_id']).order_by(experiments.c.id.desc()).limit(1)).mappings().first()
    return {'trained':bool(row),'conditions':['B0','B1','B1+D','B1+S','B2'],'modules':[{'code':'M1','title':'Trafik profili','algorithm':'K-Means ve DBSCAN','desc':'Dakika ve rota yoğunluk bağlamı'},{'code':'M2','title':'Anomali tespiti','algorithm':'Isolation Forest','desc':'Çok değişkenli sapma puanı'},{'code':'M3','title':'Davranış örüntüsü','algorithm':'PrefixSpan','desc':'Oturum rota geçişleri'},{'code':'M4','title':'Karar katmanı','algorithm':'Bağlamlı birleşim','desc':'Açıklanabilir alarm sonucu'}],
            'latest':json.loads(row['result_json']) if row else None,'latest_run_id':row['id'] if row else None}

@app.get('/api/experiments')
def experiment_history(user=Depends(auth)):
    with engine.connect() as c:
        rows=[dict(r) for r in c.execute(select(experiments).where(experiments.c.workspace_id==user['workspace_id']).order_by(experiments.c.id.desc()).limit(15)).mappings()]
    return {'experiments':[{'id':r['id'],'started_at':r['started_at'],'windows':r['windows'],'requests':r['requests'],'duration_ms':r['duration_ms']} for r in rows]}

@app.post('/api/experiments/run')
def experiment_run(p:ExperimentPayload,user=Depends(auth)):
    analyst(user)
    # CPU-bound, synchronous FastAPI handler runs in thread pool; request remains bounded.
    result=run_experiment(p.windows,p.requests_per_window,p.seed)
    with engine.begin() as c:
        pk=c.execute(insert(experiments).values(workspace_id=user['workspace_id'],started_at=now(),duration_ms=result['elapsed_ms'],windows=p.windows,requests=result['data']['total_http_requests'],result_json=json.dumps(result,ensure_ascii=False))).inserted_primary_key[0]
        for i,ex in enumerate(result['examples'][:7]):
            alarm_id=f'EXP-{pk}-{i+1:02d}'
            c.execute(insert(alarms).values(id=alarm_id,workspace_id=user['workspace_id'],occurred_at=now(),route='/synthetic/window/',severity='Orta' if ex['combined_score']<.85 else 'Yüksek',reason=ex['reason'],score=ex['combined_score'],state='Yeni',m1=ex['m1'],m2=ex['m2'],m3=ex['m3'],evidence=json.dumps(ex,ensure_ascii=False),notes='',source='experiment_synthetic'))
        record_notify(c,user,'Deney tamamlandı',f'Koşullar B0–B2; {result["data"]["windows"]} sentetik dakika değerlendirildi.','experiment')
    return {'ok':True,'run_id':pk,'result':result}

@app.get('/api/experiments/{run_id}')
def experiment_detail(run_id:int,user=Depends(auth)):
    with engine.connect() as c:r=c.execute(select(experiments).where(and_(experiments.c.id==run_id,experiments.c.workspace_id==user['workspace_id']))).mappings().first()
    if not r:raise HTTPException(404,'Deney bulunamadı')
    return {'id':r['id'],'result':json.loads(r['result_json'])}


@app.post('/api/ingested/analyze-trained')
def trained_ingested_analysis(user=Depends(auth)):
    """Frozen research model -> persisted alarm; no implicit online fitting.

    Designed as an explicitly local, exploratory Week 7 acceptance path. The
    model is loaded exclusively from server-owned fixed paths and the records
    are isolated by the authenticated workspace. Re-running is idempotent.
    """
    analyst(user)
    choices=[('local_locust_declared',ROOT/'models'/'hafta6_live'/'research_week6.joblib'),
             ('offline_main_5seed',ROOT/'models'/'ana_veri_model'/'research_week6.joblib'),
             ('offline_previous_1seed',ROOT/'models'/'hafta6'/'research_week6.joblib')]
    kind,model_path=next(((kind,path) for kind,path in choices if path.is_file()),(None,None))
    if model_path is None:
        raise HTTPException(503,'Once etiketli JSONL ile yerel model egitimini yapin')
    with engine.connect() as c:
        loaded=[dict(r) for r in c.execute(select(events).where(events.c.workspace_id==user['workspace_id'])
                .order_by(events.c.occurred_at).limit(200000)).mappings()]
    if not loaded:raise HTTPException(422,'Önce JSONL verisi yüklenmeli')
    try:
        result=score_persisted_events(loaded,model_path,model_origin=kind)
    except (ValueError,KeyError) as exc:
        raise HTTPException(422,f'Model girdileri islenemedi: {exc}')
    artifact_sha256=hashlib.sha256(model_path.read_bytes()).hexdigest()
    added=0
    with engine.begin() as c:
        rid=c.execute(insert(event_analyses).values(workspace_id=user['workspace_id'],created_at=now(),
                 result_json=json.dumps(result,ensure_ascii=False))).inserted_primary_key[0]
        from sqlalchemy.dialects.sqlite import insert as sqlite_insert
        from sqlalchemy.dialects.postgresql import insert as pg_insert
        for alert in result['alarms']:
            alarm_id='ML-'+hashlib.sha256(f"{user['workspace_id']}|{artifact_sha256}|{alert['minute_start_utc']}".encode()).hexdigest()[:24]
            row={'id':alarm_id,'workspace_id':user['workspace_id'],
                 'occurred_at':alert['minute_start_utc'],'route':alert['representative_route'],
                 'severity':'Yüksek' if alert['b2_score']>=.90 else 'Orta',
                 'reason':alert['reason'],'score':alert['b2_score'], 'state':'Yeni',
                 'm1':alert['m1'],'m2':alert['m2'],'m3':alert['m3'] if alert['m3'] is not None else 0.0,
                 'evidence':json.dumps({**alert,'model_origin':kind,'model_sha256':artifact_sha256,'is_verified_attack':False,
                      'distribution_shift_warning':result['shift_warning']},ensure_ascii=False),
                 'notes':'','source':'frozen_research_model'}
            if engine.dialect.name=='sqlite':
                stmt=sqlite_insert(alarms).values(**row).on_conflict_do_nothing(index_elements=['id'])
            elif engine.dialect.name=='postgresql':
                stmt=pg_insert(alarms).values(**row).on_conflict_do_nothing(index_elements=['id'])
            else:
                raise HTTPException(501,'Desteklenmeyen veritabanı')
            added+=max(0,c.execute(stmt).rowcount)
        record_notify(c,user,'Donmuş model analizi',f'{result["total_alerts"]} araştırma uyarısı; {added} yeni kayıt.','experiment')
    return {'ok':True,'analysis_id':rid,'new_alarms':added,'result':result}


@app.get('/api/ingested/analyses')
def ingested_analyses(user=Depends(auth)):
    with engine.connect() as c:
        rows=[dict(r) for r in c.execute(select(event_analyses).where(event_analyses.c.workspace_id==user['workspace_id']).order_by(event_analyses.c.id.desc()).limit(10)).mappings()]
    return {'runs':[{'id':r['id'],'created_at':r['created_at'],'data':json.loads(r['result_json'])['data'],'total_alerts':json.loads(r['result_json'])['total_alerts']} for r in rows]}

@app.post('/api/ingested/analyze')
def ingested_analysis(user=Depends(auth)):
    analyst(user)
    with engine.connect() as c:
        rows=[dict(r) for r in c.execute(select(events).where(events.c.workspace_id==user['workspace_id']).order_by(events.c.occurred_at).limit(200000)).mappings()]
    try: result=analyze_ingested_events(rows)
    except ValueError as exc: raise HTTPException(422,str(exc))
    with engine.begin() as c:
        run_id=c.execute(insert(event_analyses).values(workspace_id=user['workspace_id'],created_at=now(),result_json=json.dumps(result,ensure_ascii=False))).inserted_primary_key[0]
        record_notify(c,user,'Yüklenen HTTP günlükleri analiz edildi',f'{result["data"]["minutes"]} dakika; {result["total_alerts"]} keşifsel uyarı','experiment')
    return {'ok':True,'id':run_id,'result':result}

@app.get('/api/batches')
def batch_list(user=Depends(auth)):
    with engine.connect() as c:
        rows=[dict(r) for r in c.execute(select(batches).where(batches.c.workspace_id==user['workspace_id']).order_by(batches.c.id.desc()).limit(40)).mappings()]
        count=c.execute(select(func.count()).select_from(events).where(events.c.workspace_id==user['workspace_id'])).scalar_one()
    return {'batches':rows,'eventCount':count}

@app.get('/api/sample.jsonl')
def sample_jsonl(user=Depends(auth)):
    line={'event_uid':'sample-001','occurred_at':'2026-10-28T14:00:00Z','http_method':'GET','route_template':'/catalog/','status_code':200,'duration_ms':136.5,'session_ref':'synthetic-s1','schema_version':'1.0'}
    from fastapi.responses import Response as R
    return R('\n'.join(json.dumps(v,ensure_ascii=False) for v in [line,{**line,'event_uid':'sample-002','status_code':401,'route_template':'/auth/login/'}])+'\n',media_type='application/x-ndjson',headers={'Content-Disposition':'attachment; filename=logscope_ornek.jsonl'})

@app.post('/api/ingest')
async def ingest(file:UploadFile=File(...),user=Depends(auth)):
    analyst(user)
    if not file.filename or not file.filename.lower().endswith('.jsonl'):
        raise HTTPException(400,'Sadece JSONL')
    # Maximum permits one full 1200-minute synthetic sample (about 30 MB).
    max_bytes=50*1024*1024
    raw=await file.read(max_bytes+1)
    if len(raw)>max_bytes:raise HTTPException(413,'Dosya 50 MiB sınırını aşıyor')
    try:lines=raw.decode('utf-8').splitlines()
    except UnicodeDecodeError:raise HTTPException(400,'UTF-8 gerekli')
    if len(lines)>160000:raise HTTPException(413,'En çok 160.000 satır')
    accepted=[];rejected=0;used=set()
    for line in lines:
        if not line.strip():continue
        try:v=valid_event(json.loads(line))
        except json.JSONDecodeError:v=None
        if not v or v['uid'] in used:rejected+=1;continue
        used.add(v['uid']);accepted.append(v)
    # No rejected raw request content is ever persisted. SQLAlchemy binds all params.
    # Bulk insert prevents O(n) duplicate lookups for large datasets.
    from sqlalchemy.dialects.sqlite import insert as sqlite_insert
    from sqlalchemy.dialects.postgresql import insert as pg_insert
    with engine.begin() as c:
        bid=c.execute(insert(batches).values(workspace_id=user['workspace_id'],filename=Path(file.filename).name[:120],accepted=0,rejected=0,created_at=now())).inserted_primary_key[0]
        count=0
        for offset in range(0,len(accepted),1000):
            rows=[{'workspace_id':user['workspace_id'],'batch_id':bid,**v} for v in accepted[offset:offset+1000]]
            if not rows:break
            if engine.dialect.name=='sqlite':
                stmt=sqlite_insert(events).on_conflict_do_nothing(index_elements=['uid'])
            elif engine.dialect.name=='postgresql':
                stmt=pg_insert(events).on_conflict_do_nothing(index_elements=['uid'])
            else:
                raise HTTPException(501,'Desteklenmeyen veritabanı')
            outcome=c.execute(stmt,rows)
            count+=max(0,outcome.rowcount)
        rejected+=len(accepted)-count
        c.execute(update(batches).where(batches.c.id==bid).values(accepted=count,rejected=rejected))
        record_notify(c,user,'JSONL içe aktarma',f'{count} kabul / {rejected} reddedildi','ingestion')
    return {'ok':True,'batch':bid,'accepted':count,'rejected':rejected,
            'note':'Yalnız izinli alanlar kaydedildi; loglarda etiket bulunmaz. Analizi ayrıca başlatın.'}

@app.get('/api/team')
def team(user=Depends(auth)):
    with engine.connect() as c:
        members=[dict(r) for r in c.execute(select(users.c.email,users.c.display_name,memberships.c.role).join(memberships,memberships.c.user_id==users.c.id).where(memberships.c.workspace_id==user['workspace_id'])).mappings()]
        invites=[dict(r) for r in c.execute(select(invitations).where(invitations.c.workspace_id==user['workspace_id']).order_by(invitations.c.id.desc())).mappings()]
    return {'members':members,'invitations':invites}

@app.post('/api/team/invitations')
def invite(p:InvitePayload,user=Depends(auth)):
    admin(user)
    if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',p.email):raise HTTPException(422,'E-posta hatalı')
    with engine.begin() as c:
        key=c.execute(insert(invitations).values(workspace_id=user['workspace_id'],email=p.email.strip().lower(),role=p.role,status='draft',invited_at=now())).inserted_primary_key[0]
    return {'ok':True,'id':key,'status':'draft','email_sent':False}

@app.get('/api/integrations')
def integration_list(user=Depends(auth)):
    with engine.connect() as c:rows=[dict(r) for r in c.execute(select(integrations).where(integrations.c.workspace_id==user['workspace_id'])).mappings()]
    return {'integrations':[{**r,'safe_config':json.loads(r['safe_config'])} for r in rows]}

@app.post('/api/integrations')
def integration_upsert(p:IntegrationPayload,user=Depends(auth)):
    admin(user)
    with engine.begin() as c:
        row=c.execute(select(integrations.c.id).where(and_(integrations.c.workspace_id==user['workspace_id'],integrations.c.provider==p.provider))).first()
        if row:c.execute(update(integrations).where(integrations.c.id==row[0]).values(name=p.name,status=p.status));pid=row[0]
        else:pid=c.execute(insert(integrations).values(workspace_id=user['workspace_id'],provider=p.provider,name=p.name,status=p.status,safe_config='{}')).inserted_primary_key[0]
    return {'ok':True,'id':pid,'status':p.status,'live_connection':False}

@app.get('/api/integrations/{integration_id}')
def integration_get(integration_id:int,user=Depends(auth)):
    with engine.connect() as c:
        row=c.execute(select(integrations).where(and_(integrations.c.id==integration_id,
            integrations.c.workspace_id==user['workspace_id']))).mappings().first()
    if not row:raise HTTPException(404,'Entegrasyon bulunamadi')
    return {**dict(row),'safe_config':json.loads(row['safe_config'])}

@app.patch('/api/integrations/{integration_id}')
def integration_patch(integration_id:int,p:IntegrationPatch,user=Depends(auth)):
    admin(user)
    values=p.model_dump(exclude_none=True)
    if not values:raise HTTPException(422,'No changes specified')
    with engine.begin() as c:
        result=c.execute(update(integrations).where(and_(integrations.c.id==integration_id,
            integrations.c.workspace_id==user['workspace_id'])).values(**values))
    if result.rowcount!=1:raise HTTPException(404,'Entegrasyon bulunamadi')
    return {'ok':True,'id':integration_id,'changed':sorted(values),'live_connection':False}

@app.delete('/api/integrations/{integration_id}')
def integration_delete(integration_id:int,user=Depends(auth)):
    admin(user)
    with engine.begin() as c:
        result=c.execute(delete(integrations).where(and_(integrations.c.id==integration_id,
            integrations.c.workspace_id==user['workspace_id'])))
    if result.rowcount!=1:raise HTTPException(404,'Entegrasyon bulunamadi')
    return {'ok':True,'deleted_id':integration_id}

@app.get('/api/onboarding')
def onboarding_get(user=Depends(auth)):
    with engine.connect() as c:
        row=c.execute(select(onboarding).where(onboarding.c.workspace_id==user['workspace_id'])).mappings().first()
        ws=c.execute(select(workspaces).where(workspaces.c.id==user['workspace_id'])).mappings().first()
    return {'step':row['step'] if row else 0,'source_type':row['source_type'] if row else 'jsonl', 'privacy_checked':row['privacy_checked'] if row else False,'workspace':ws['name']}

@app.put('/api/onboarding')
def onboarding_save(p:OnboardingPayload,user=Depends(auth)):
    admin(user)
    with engine.begin() as c:
        c.execute(update(onboarding).where(onboarding.c.workspace_id==user['workspace_id']).values(step=p.step,source_type=p.source_type,privacy_checked=p.privacy_checked))
        if p.workspace_name and p.workspace_name.strip():c.execute(update(workspaces).where(workspaces.c.id==user['workspace_id']).values(name=p.workspace_name.strip()))
    return {'ok':True,'step':p.step}

@app.get('/api/settings')
def settings_get(user=Depends(auth)):
    with engine.connect() as c:ws=c.execute(select(workspaces).where(workspaces.c.id==user['workspace_id'])).mappings().first()
    return {'name':ws['name'],'timezone':ws['timezone'],'retention_days':ws['retention_days']}

@app.put('/api/settings')
def settings_save(p:SettingsPayload,user=Depends(auth)):
    admin(user)
    with engine.begin() as c:c.execute(update(workspaces).where(workspaces.c.id==user['workspace_id']).values(name=p.name.strip(),timezone=p.timezone,retention_days=p.retention_days))
    return {'ok':True}

@app.get('/api/notifications')
def notification_list(user=Depends(auth)):
    with engine.connect() as c:rows=[dict(r) for r in c.execute(select(notifications).where(and_(notifications.c.user_id==user['id'],notifications.c.workspace_id==user['workspace_id'])).order_by(notifications.c.id.desc()).limit(80)).mappings()]
    return {'notifications':rows,'unread':sum(not r['read'] for r in rows)}

@app.post('/api/notifications/read-all')
def notification_read_all(user=Depends(auth)):
    with engine.begin() as c:c.execute(update(notifications).where(and_(notifications.c.user_id==user['id'],notifications.c.workspace_id==user['workspace_id'])).values(read=True))
    return {'ok':True}

@app.post('/api/notifications/{notice_id}/toggle')
def notification_toggle(notice_id:int,user=Depends(auth)):
    with engine.begin() as c:
        q=select(notifications).where(and_(notifications.c.id==notice_id,notifications.c.user_id==user['id'],notifications.c.workspace_id==user['workspace_id']))
        row=c.execute(q).mappings().first()
        if not row:raise HTTPException(404,'Bildirim yok')
        c.execute(update(notifications).where(notifications.c.id==notice_id).values(read=not row['read']))
    return {'ok':True,'read':not row['read']}

def csv_safe(x):
    v=str(x if x is not None else '')
    return "'"+v if re.match(r'^\s*[=+@\-\t\r]',v) else v

def csv_return(rows,headers,name):
    out=io.StringIO();w=csv.writer(out);w.writerow(headers)
    for row in rows:w.writerow([csv_safe(row.get(h,'')) for h in headers])
    return Response(out.getvalue().encode('utf-8-sig'),media_type='text/csv; charset=utf-8',headers={'Content-Disposition':f'attachment; filename={name}'})

@app.get('/api/export/ingested.csv')
def export_ingested(user=Depends(auth)):
    with engine.connect() as c:
        row=c.execute(select(event_analyses).where(event_analyses.c.workspace_id==user['workspace_id']).order_by(event_analyses.c.id.desc()).limit(1)).mappings().first()
    if not row: raise HTTPException(404,'Yüklenen log analizi bulunamadı')
    r=json.loads(row['result_json'])
    return csv_return(r['alarms'],['minute','count','score','m1','m2','m3','reason'],'logscope_yuklenen_log_analizi.csv')

@app.get('/api/export/alarms.csv')
def export_alarms(user=Depends(auth)):
    with engine.connect() as c:rows=[dict(r) for r in c.execute(select(alarms).where(alarms.c.workspace_id==user['workspace_id'])).mappings()]
    return csv_return(rows,['id','occurred_at','route','severity','reason','score','state','source'],'logscope_alarmlar.csv')

@app.get('/api/export/traffic.csv')
def export_traffic(user=Depends(auth)):
    with engine.connect() as c:rows=[dict(r) for r in c.execute(select(traffic).where(traffic.c.workspace_id==user['workspace_id'])).mappings()]
    return csv_return(rows,['ts','requests','errors','latency_ms','route'],'logscope_trafik.csv')

@app.get('/api/export/experiments.csv')
def export_experiments(user=Depends(auth)):
    with engine.connect() as c:rows=[dict(r) for r in c.execute(select(experiments).where(experiments.c.workspace_id==user['workspace_id'])).mappings()]
    results=[]
    for row in rows:
        result=json.loads(row['result_json'])
        for code,metric in result['conditions'].items():results.append({'run_id':row['id'],'condition':code,**metric})
    return csv_return(results,['run_id','condition','precision','recall','f1','normal_fpr','pr_auc','alarms','test_windows','threshold'],'logscope_deneyler.csv')

@app.post('/api/reset')
def demo_reset(user=Depends(auth)):
    admin(user)
    if not DEMO_MODE:raise HTTPException(403,'Yalnız demo modunda')
    wid=user['workspace_id']
    with engine.begin() as c:
        alarm_ids=[r[0] for r in c.execute(select(alarms.c.id).where(alarms.c.workspace_id==wid))]
        if alarm_ids:c.execute(delete(reviews).where(reviews.c.alarm_id.in_(alarm_ids)))
        c.execute(delete(events).where(events.c.workspace_id==wid));c.execute(delete(batches).where(batches.c.workspace_id==wid))
        c.execute(delete(alarms).where(alarms.c.workspace_id==wid));c.execute(delete(traffic).where(traffic.c.workspace_id==wid))
        c.execute(delete(experiments).where(experiments.c.workspace_id==wid));c.execute(delete(event_analyses).where(event_analyses.c.workspace_id==wid))
        # Re-seed existing workspace with same deterministic dataset, not a second workspace.
        rng=random.Random(20261028);stamp=datetime(2026,10,28,14,tzinfo=timezone.utc)
        for j in range(144):
            c.execute(insert(traffic).values(workspace_id=wid,ts=(stamp-timedelta(minutes=(143-j)*10)).isoformat(),requests=round(350+30*rng.random()),errors=rng.randint(0,12),latency_ms=round(150+50*rng.random(),1),route='Tümü'))
        for i in range(18):
            c.execute(insert(alarms).values(id=f'LS-{1042-i}',workspace_id=wid,occurred_at=(stamp-timedelta(minutes=i*17)).isoformat(),route=ROUTES[i%5],severity=SEVERITIES[i%4],reason='Sentetik alarm',score=round(.5+.48*rng.random(),3),state='Yeni',m1=.4,m2=.6,m3=.3,evidence='{"demo":true}',notes='',source='demo'))
        record_notify(c,user,'Demo sıfırlandı','Örnek veriler yeniden oluşturuldu','system')
    return {'ok':True}

# Host the production frontend if built; API remains available separately.
DIST=ROOT/'frontend'/'dist'
if DIST.is_dir():
    from fastapi.responses import HTMLResponse
    app.mount('/assets',StaticFiles(directory=str(DIST/'assets')),name='assets') if (DIST/'assets').is_dir() else None
    @app.get('/')
    def home():return FileResponse(DIST/'index.html')

if not DIST.is_dir():
    @app.get('/')
    def standalone_home():
        """Week-4 API-only package: use Swagger as the landing page."""
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url='/api/docs')
