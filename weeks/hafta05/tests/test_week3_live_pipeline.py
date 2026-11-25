"""Small fixture verifies the real-HTTP capture assembly without contacting sites."""
from __future__ import annotations
import csv
import json
from datetime import datetime,timedelta,timezone
from pathlib import Path
from scripts.prepare_locust_dataset import transform
from scripts.verify_week3_acceptance import check
from scripts.run_locust_matrix import write_manifest,loopback


def test_live_locust_manifest_join_and_acceptance(tmp_path):
    assert loopback('http://127.0.0.1:8001').hostname=='127.0.0.1'
    try:loopback('https://example.com')
    except ValueError:pass
    else:assert False,'external hosts must be refused'
    codes=['normal_steady','normal_hourly_rise','normal_campaign','normal_route_mix',
           'anomaly_5xx','anomaly_latency','anomaly_login_fail','anomaly_rare_route']
    cases=[];start=datetime(2026,10,20,1,0,tzinfo=timezone.utc)
    for idx,(seed,code) in enumerate((seed,code) for seed in (11,23,42,71,97) for code in codes):
        path=tmp_path/f'case-{idx}.jsonl'
        event={'event_uid':f'evt-{idx}','occurred_at':(start+timedelta(minutes=idx)).isoformat(),
               'http_method':'GET','route_template':'/catalog/','status_code':200,'duration_ms':42.4,
               'session_ref':f'syn-{idx}','schema_version':'1.0'}
        path.write_text(json.dumps(event)+'\n',encoding='utf-8')
        cases.append({'seed':seed,'scenario':code,'label':'anomaly' if code.startswith('anomaly_') else 'normal',
                      'start_unix':0,'finish_unix':0,'request_rows':1,'log_file':str(path),
                      'test_duration_minutes':1,'users':1})
    write_manifest(tmp_path,cases)
    output=transform(tmp_path/'locust_runs_manifest.csv',tmp_path/'prepared')
    assert output['events']==40 and output['unique_minute_windows']==40
    assert output['ambiguous_windows']==0
    import_accepted=check(output['manifest'],minimum_events=40,minimum_windows=40)
    assert import_accepted['passed'],import_accepted
    assert import_accepted['split_counts']=={'train':24,'validation':8,'test':8}
    import_unmet=check(output['manifest'],minimum_events=120000,minimum_windows=1200)
    assert not import_unmet['passed']
    example=json.loads(Path(output['jsonl']).read_text().splitlines()[0])
    assert 'ground_truth' not in example and 'scenario_code' not in example
