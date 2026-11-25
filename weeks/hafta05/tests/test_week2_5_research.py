"""No external services required for these unit-contract checks."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from backend.fullstack import valid_event
from backend.week5_cluster_compare import compare
from scripts.week3_generate_dataset import make_offline_events

ROOT=Path(__file__).resolve().parents[1]

def test_week2_json_contract_and_privacy():
    schema=json.loads((ROOT/'contracts/logscope-event-v1.schema.json').read_text(encoding='utf-8'))
    assert schema['additionalProperties'] is False
    expected=set(schema['properties'])
    assert expected=={'event_uid','occurred_at','http_method','route_template','status_code','duration_ms','session_ref','schema_version'}
    valid={'event_uid':'abcd-1','occurred_at':'2026-10-01T00:00:00Z','http_method':'GET','route_template':'/catalog/',
           'status_code':200,'duration_ms':41.4,'session_ref':'syn-11','schema_version':'1.0'}
    assert valid_event(valid) is not None
    for key in ('ip','cookie','token','body','query','authorization'):
        assert valid_event({**valid,key:'secret'}) is None

def test_week3_offline_event_labels_are_separate():
    with TemporaryDirectory() as temp:
        out=make_offline_events(120,35,77,temp)
        assert out['total_requests']>3500
        manifest=Path(out['labels_file']).read_text().splitlines()
        assert len(manifest)==121
        examples=Path(out['data_file']).read_text().splitlines()
        assert len(examples)==out['total_requests']
        first=json.loads(examples[0]);assert valid_event(first)
        assert 'scenario' not in first and 'ground_truth' not in first and 'seed' not in first
        assert all(v not in examples[0] for v in ('ip_address','password','cookie','token=','Authorization'))

def test_week5_train_held_out_and_models():
    r=compare(seed=5,n_windows=160,requests_per_window=80)
    assert r['split']=={'train':96,'validation':32,'test':32}
    assert set(r['results'])=={'B0_robust_volume_z','KMeans','DBSCAN_core','B1_IsolationForest','B1_plus_D'}
    assert r['dbscan']['refit_on_test'] is False
    assert 2<=r['kmeans']['selected_k']<=6
    for metrics in r['results'].values():
        assert 0<=metrics['f1']<=1
        assert 0<=metrics['normal_fpr']<=1
        assert sum(metrics[k] for k in ('tp','fp','tn','fn'))==32

def test_locust_host_safety():
    import pytest
    from scripts.run_locust_matrix import loopback
    assert loopback('http://127.0.0.1:8001').hostname=='127.0.0.1'
    for url in ('https://example.com','http://example.com','http://192.168.1.2:8001'):
        with pytest.raises(ValueError):loopback(url)
