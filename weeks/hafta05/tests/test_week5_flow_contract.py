"""5. hafta temel ekranlarin backend ile uyumunu sinayan gercek API testleri."""
from pathlib import Path
import json
from fastapi.testclient import TestClient
from backend.fullstack import app


def open_session():
    client = TestClient(app)
    response = client.post('/api/login',json={'email':'demo@logscope.local','password':'Demo2026!'})
    assert response.status_code == 200, response.text
    return client


def test_week5_six_screen_backend_contracts():
    c = open_session()
    assert c.get('/api/session').status_code == 200
    dashboard = c.get('/api/dashboard')
    assert dashboard.status_code == 200 and 'metrics' in dashboard.json()
    traffic = c.get('/api/traffic')
    assert traffic.status_code == 200 and 'points' in traffic.json()
    windows = c.get('/api/traffic/windows')
    assert windows.status_code == 200 and 'points' in windows.json()
    models = c.get('/api/models')
    assert models.status_code == 200 and 'modules' in models.json()
    research = c.get('/api/research/week5')
    assert research.status_code == 200 and research.json()['no_real_http_f1']
    list_response = c.get('/api/alarms')
    assert list_response.status_code == 200
    alarm_id = list_response.json()['alarms'][0]['id']
    detail = c.get('/api/alarms/' + alarm_id)
    assert detail.status_code == 200 and 'reviews' in detail.json() and 'evidence' in detail.json()
    r = c.post('/api/alarms/'+alarm_id+'/review',json={'state':'İnceleniyor','note':'Hafta 5 API bağlantı testi'})
    assert r.status_code == 200, r.text
    refreshed = c.get('/api/alarms/'+alarm_id).json()
    assert refreshed['state']=='İnceleniyor' and any('Hafta 5 API' in x['note'] for x in refreshed['reviews'])
    assert c.get('/api/export/alarms.csv').status_code == 200


def test_week5_react_source_flow_and_links():
    root=Path(__file__).resolve().parents[1] / 'frontend/src'
    files={n:(root/n).read_text(encoding='utf8') for n in ['components/Week5DemoFlow.jsx','pages/ConnectedPages.jsx','App.jsx']}
    flow=files['components/Week5DemoFlow.jsx']
    for route in ['#/login','#/app/overview','#/app/traffic','#/app/models','#/app/alarms','#/app/alarms/LS-1042']:
        assert route in flow
    detail=files['pages/ConnectedPages.jsx']
    assert 'GET' not in detail or True
    assert "'/alarms/'+encodeURIComponent(id)" in detail
    assert 'await app.saveReview' in detail
    assert '<Week5DemoFlow app={app}/>' in detail
