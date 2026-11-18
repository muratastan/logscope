"""Independent localhost FastAPI + real PostgreSQL acceptance for Week 4.

This script will fail if only SQLite is running. It reads .env but NEVER prints
DB passwords/session cookies. It creates/updates one safe demo integration row.
Run only on your own local LogScope test environment, not production.
"""
from __future__ import annotations
import argparse
import hashlib
from http.cookiejar import CookieJar
import json
import os
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import Request,HTTPCookieProcessor,build_opener
from scripts.local_env import ensure_database_env,load_local_env
from scripts.apply_postgres_migrations import MIGRATIONS

ROOT=Path(__file__).resolve().parents[1]

def fetch(opener,base,path,method='GET',payload=None):
    body=json.dumps(payload).encode('utf-8') if payload is not None else None
    headers={'Content-Type':'application/json'} if payload is not None else {}
    req=Request(base+path,data=body,method=method,headers=headers)
    try:
        with opener.open(req,timeout=15) as result:
            text=result.read()
            return result.status, json.loads(text) if text and 'json' in result.headers.get('Content-Type','').lower() else text
    except HTTPError as exc:
        return exc.code,exc.read()

def check_pg():
    try: import psycopg
    except ImportError as e:raise RuntimeError('Install psycopg[binary] to verify PostgreSQL') from e
    db_url=os.environ['LOGSCOPE_DATABASE_URL'].replace('postgresql+psycopg://','postgresql://')
    if not db_url.startswith('postgresql://'):
        raise RuntimeError('PostgreSQL URL required; SQLite is not acceptable for Week 4 signoff')
    with psycopg.connect(db_url,connect_timeout=8) as conn:
        with conn.cursor() as c:
            c.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='logscope' AND table_type='BASE TABLE'")
            tables=c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM pg_constraint k JOIN pg_namespace n ON n.oid=k.connamespace WHERE n.nspname='logscope' AND k.contype='f'")
            fks=c.fetchone()[0]
            c.execute("SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='ui_users')")
            operational=c.fetchone()[0]
            c.execute('SELECT filename,sha256 FROM public.logscope_schema_migrations')
            versions=dict(c.fetchall())
    expected={f:hashlib.sha256((ROOT/'db'/f).read_bytes()).hexdigest() for f in MIGRATIONS}
    return {'canonical_tables':tables,'canonical_fk_constraints':fks,
            'operational_ui_users_table':operational,
            'migration_checksums_match':all(versions.get(f)==digest for f,digest in expected.items()),
            'migration_files_recorded':sorted(versions),
            'passed':tables==27 and fks==41 and operational and all(versions.get(f)==digest for f,digest in expected.items())}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--api',default='http://127.0.0.1:8000')
    ap.add_argument('--out',default=str(ROOT/'reports/hafta4/real_postgres_api_acceptance.json'))
    opts=ap.parse_args()
    p=urlparse(opts.api)
    if p.scheme!='http' or p.hostname not in ('localhost','127.0.0.1','::1'):
        raise SystemExit('Only localhost demo API can be tested')
    load_local_env();ensure_database_env()
    pg=check_pg()
    opener=build_opener(HTTPCookieProcessor(CookieJar()))
    checks={}
    status,data=fetch(opener,opts.api,'/api/health')
    checks['postgresql_backed_api']=status==200 and isinstance(data,dict) and data.get('storage')=='postgresql'
    status,_=fetch(opener,opts.api,'/api/docs');checks['swagger_docs']=status==200
    status,api_spec=fetch(opener,opts.api,'/api/openapi.json')
    checks['openapi_schema']=status==200 and isinstance(api_spec,dict) and '/api/alarms' in api_spec.get('paths',{})
    status,_=fetch(opener,opts.api,'/api/alarms');checks['anonymous_rejected']=status==401
    email='demo@logscope.local'
    password=os.environ.get('LOGSCOPE_DEMO_PASSWORD','')
    if not password:
        raise RuntimeError('LOGSCOPE_DEMO_PASSWORD missing from local .env')
    status,login=fetch(opener,opts.api,'/api/login','POST',{'email':email,'password':password})
    checks['demo_login']=status==200 and isinstance(login,dict) and login.get('ok') is True
    if checks['demo_login']:
        status,account=fetch(opener,opts.api,'/api/session')
        checks['session_and_workspace_role']=status==200 and account.get('workspace_role') in ('owner','admin')
        status,alarms=fetch(opener,opts.api,'/api/alarms')
        checks['read_alarms']=status==200 and isinstance(alarms,dict) and 'alarms' in alarms
        status,_=fetch(opener,opts.api,'/api/team')
        checks['read_team']=status==200
        status,_=fetch(opener,opts.api,'/api/traffic/windows?limit=10')
        checks['read_traffic_windows']=status==200
        status,created=fetch(opener,opts.api,'/api/integrations','POST',
                             {'provider':'locust','status':'draft','name':'Week4 Local Acceptance'})
        checks['crud_create_or_update_integration']=status==200 and isinstance(created,dict) and created.get('ok') is True
        status,items=fetch(opener,opts.api,'/api/integrations')
        checks['crud_read_integration']=status==200 and any(x.get('provider')=='locust' for x in items.get('integrations',[]))
        status,_=fetch(opener,opts.api,'/api/logout','POST')
        checks['logout']=status==200
        status,_=fetch(opener,opts.api,'/api/alarms')
        checks['logout_revokes_auth']=status==401
    report={'source':'LIVE_LOCAL_POSTGRESQL_AND_FASTAPI','postgresql':pg,'api':checks,
            'passed':pg['passed'] and len(checks)==13 and all(checks.values()),
            'notes':'Local-only acceptance. Execute role permission pytest separately; this does not prove production security.'}
    output=Path(opts.out);output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))
    return 0 if report['passed'] else 2

if __name__=='__main__':raise SystemExit(main())
