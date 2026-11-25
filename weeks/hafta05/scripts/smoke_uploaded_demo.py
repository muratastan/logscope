"""End-to-end local smoke test: FastAPI login, sample JSONL, M1-M4 data path."""
import json,os
from pathlib import Path
from tempfile import TemporaryDirectory
from fastapi.testclient import TestClient

def run():
    with TemporaryDirectory(prefix='logscope_smoke_') as tmp:
        os.environ['LOGSCOPE_DATABASE_URL']='sqlite:///'+str(Path(tmp)/'smoke.sqlite3')
        os.environ['LOGSCOPE_DEMO_MODE']='1'
        from backend.fullstack import app
        client=TestClient(app)
        user=client.post('/api/login',json={'email':'demo@logscope.local','password':os.getenv('LOGSCOPE_DEMO_PASSWORD','Demo2026!')})
        assert user.status_code==200,user.text
        content=Path(__file__).resolve().parent.parent/'preview'/'ORNEK_80_DAKIKA_SENTETIK.jsonl'
        res=client.post('/api/ingest',files={'file':(content.name,content.read_bytes(),'application/x-ndjson')})
        assert res.status_code==200,res.text
        assert res.json()['accepted']==1120,res.json()
        r=client.post('/api/ingested/analyze')
        assert r.status_code==200,r.text
        d=r.json()['result']
        assert d['data']['minutes']==80
        assert d['data']['events']==1120
        assert client.get('/api/export/ingested.csv').status_code==200
        report={
            'mode':'actual JSONL upload and unsupervised scoring of synthetic example records',
            'accepted':res.json()['accepted'], 'minutes':d['data']['minutes'],
            'alerts':d['total_alerts'], 'threshold':d['threshold'],
            'elapsed_ms':d['elapsed_ms'], 'has_labels':False,
            'has_f1':False, 'date':'2026-10-29'
        }
        dest=Path(__file__).resolve().parent.parent/'tests'/'DEMO_UPLOADED_LOG_ANALYSIS.json'
        dest.write_text(json.dumps({'report':report,'result':d},ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':run()
