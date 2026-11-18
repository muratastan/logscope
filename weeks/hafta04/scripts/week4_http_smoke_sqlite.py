"""Real loopback HTTP smoke of FastAPI using an isolated temporary SQLite DB.

PASS of this smoke is not evidence that PostgreSQL migrations work. That is
covered separately by scripts.week4_live_acceptance, which requires psycopg.
"""
from __future__ import annotations
from http.cookiejar import CookieJar
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
from urllib.request import HTTPCookieProcessor,build_opener,Request
from urllib.error import HTTPError,URLError

ROOT=Path(__file__).resolve().parents[1]

def get(opener,url,data=None):
    b=json.dumps(data).encode('utf-8') if data is not None else None
    req=Request(url,method='POST' if b is not None else 'GET',data=b,
                headers={'Content-Type':'application/json'} if b else {})
    try:
        with opener.open(req,timeout=4) as r:
            raw=r.read()
            obj=json.loads(raw) if raw and 'json' in r.headers.get('Content-Type','').lower() else {}
            return r.status,obj
    except HTTPError as exc:
        return exc.code,{}

def main():
    with tempfile.TemporaryDirectory(prefix='logscope_week4_http_') as temporary:
        with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as s:
            s.bind(('127.0.0.1',0));port=s.getsockname()[1]
        env=os.environ.copy()
        env['LOGSCOPE_DATABASE_URL']='sqlite:///'+str(Path(temporary)/'w4_http.sqlite3')
        env['LOGSCOPE_DEMO_MODE']='1'
        env['LOGSCOPE_DEMO_PASSWORD']='Week4SmokeGeneratedNotForUse'
        env['LOGSCOPE_HTTPS']='0'
        process=subprocess.Popen([sys.executable,'-m','uvicorn','backend.fullstack:app',
                  '--host','127.0.0.1','--port',str(port),'--no-access-log'],
                  cwd=ROOT,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
        try:
            opener=build_opener(HTTPCookieProcessor(CookieJar()))
            base='http://127.0.0.1:'+str(port)
            for attempt in range(60):
                if process.poll() is not None:
                    raise RuntimeError('FastAPI process exited before first HTTP request')
                try:
                    status,data=get(opener,base+'/api/health')
                    if status==200:break
                except (URLError,TimeoutError):pass
                time.sleep(.2)
            else:raise RuntimeError('FastAPI did not bind within 12 seconds')
            checks={}
            checks['real_http_health']=status==200 and data.get('storage')=='sqlite'
            checks['real_http_swagger']=get(opener,base+'/api/docs')[0]==200
            checks['real_http_openapi']=get(opener,base+'/api/openapi.json')[0]==200
            checks['anonymous_unauthorized']=get(opener,base+'/api/alarms')[0]==401
            status,body=get(opener,base+'/api/login',{'email':'demo@logscope.local','password':env['LOGSCOPE_DEMO_PASSWORD']})
            checks['real_http_login']=status==200 and body.get('ok') is True
            checks['authenticated_session']=get(opener,base+'/api/session')[0]==200
            checks['crud_list_alarms']=get(opener,base+'/api/alarms')[0]==200
            checks['crud_list_team']=get(opener,base+'/api/team')[0]==200
            checks['crud_list_traffic']=get(opener,base+'/api/traffic/windows?limit=10')[0]==200
            summary={'source':'LOCAL_FASTAPI_HTTP_SQLITE_ONLY','not_postgresql_proof':True,
                     'http_scheme':'http','local_port':port,'checks':checks,
                     'passed':all(checks.values())}
            result=ROOT/'reports/hafta4/fastapi_http_sqlite_smoke.json'
            result.parent.mkdir(parents=True,exist_ok=True)
            result.write_text(json.dumps(summary,indent=2),encoding='utf-8')
            print(json.dumps(summary,indent=2))
            return 0 if summary['passed'] else 2
        finally:
            process.terminate()
            try:process.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill();process.communicate()

if __name__=='__main__':raise SystemExit(main())
