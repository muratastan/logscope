"""Verify bulk-import + exploratory ML flow against an ephemeral local SQLite DB.
This does not prove live PostgreSQL, Locust, React npm or production security.
Run: python -m scripts.smoke_week4_5_offline
"""
from pathlib import Path
import json
import os
import tempfile
import time
from fastapi.testclient import TestClient


def main():
    project=Path(__file__).resolve().parents[1]
    source=project/'reports/hafta3/logscope_offline_seed42_1200m.jsonl'
    if not source.exists():raise SystemExit('Run python -m scripts.week3_generate_dataset first')
    with tempfile.TemporaryDirectory() as tmp:
        os.environ['LOGSCOPE_DATABASE_URL']='sqlite:///'+str(Path(tmp)/'smoke.sqlite3')
        os.environ['LOGSCOPE_DEMO_MODE']='1'
        from backend.fullstack import app
        c=TestClient(app)
        s=c.post('/api/login',json={'email':'demo@logscope.local','password':os.getenv('LOGSCOPE_DEMO_PASSWORD','Demo2026!')})
        assert s.status_code==200,s.text
        start=time.perf_counter()
        with source.open('rb') as file:
            r=c.post('/api/ingest',files={'file':(source.name,file,'application/x-ndjson')})
        import_seconds=round(time.perf_counter()-start,2)
        assert r.status_code==200,r.text
        stored=c.get('/api/batches').json()
        assert stored['eventCount']==r.json()['accepted'],stored
        traffic=c.get('/api/traffic/windows',params={'limit':1200})
        assert traffic.status_code==200,traffic.text
        timeline=traffic.json()
        assert timeline['total_events']==stored['eventCount']
        assert timeline['window_count']==1200
        assert all('p95_ms' in row and 'count_5xx' in row for row in timeline['points'])
        start=time.perf_counter()
        model=c.post('/api/ingested/analyze')
        model_seconds=round(time.perf_counter()-start,2)
        assert model.status_code==200,model.text
        outcome=model.json()['result']
        assert outcome['data']['events']==r.json()['accepted']
        assert outcome['data']['minutes']==1200
        assert not any(key in outcome for key in ('f1','recall','precision'))
        report={'storage':'ephemeral SQLite (not PostgreSQL)',
                'source':'offline statistical synthetic JSONL, NOT Locust HTTP workload',
                'upload':r.json(),'stored_events':stored['eventCount'],'analysis':{'minutes':outcome['data']['minutes'],
                    'alerts':outcome['total_alerts'],'mode':outcome['mode']},
                'traffic_windows':{'count':timeline['window_count'],'total_events':timeline['total_events'],
                   'source':timeline['source'],'last_p95_ms':timeline['points'][-1]['p95_ms']},
                'elapsed_seconds':{'import':import_seconds,'analysis':model_seconds},
                'http_codes':{'login':s.status_code,'ingest':r.status_code,'analyze':model.status_code}}
        out=project/'reports/hafta4'
        out.mkdir(parents=True,exist_ok=True)
        (out/'e2e_local_smoke.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps(report,ensure_ascii=False,indent=2));return report

if __name__=='__main__':main()
