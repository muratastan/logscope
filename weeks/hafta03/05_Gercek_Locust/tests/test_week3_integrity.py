from __future__ import annotations
import csv
import json
from datetime import datetime,timedelta,timezone
from pathlib import Path
from scripts.prepare_locust_dataset import transform
from scripts.verify_week3_acceptance import check
from backend.research_pg import preview_import


def test_chronological_seed_split_and_multi_seed_session_integrity(tmp_path):
    codes=['normal_steady','normal_hourly_rise','normal_campaign','normal_route_mix',
           'anomaly_5xx','anomaly_latency','anomaly_login_fail','anomaly_rare_route']
    records=[];start=datetime(2026,10,20,1,0,tzinfo=timezone.utc)
    # High seed first on purpose: numeric seed order is NOT chronology.
    chronological_seeds=[97,71,42,23,11]
    for idx,(seed,code) in enumerate((seed,code) for seed in chronological_seeds for code in codes):
        data=tmp_path/f'{idx}.jsonl'
        event={'event_uid':f'evt-{idx}', 'occurred_at':(start+timedelta(minutes=idx)).isoformat(),
               'http_method':'GET','route_template':'/catalog/','status_code':200,
               'duration_ms':40.,'session_ref':'same_pseudonym_for_all_runs', 'schema_version':'1.0'}
        data.write_text(json.dumps(event)+'\n',encoding='utf-8')
        records.append({'seed':seed,'scenario':code,'label':'anomaly' if code.startswith('anomaly_') else 'normal',
                        'start_unix':(start+timedelta(minutes=idx)).timestamp(),
                        'finish_unix':(start+timedelta(minutes=idx,seconds=30)).timestamp(),
                        'request_rows':1,'log_file':str(data),'test_duration_minutes':1,'users':1})
    with (tmp_path/'runs.csv').open('w',encoding='utf-8',newline='') as f:
        wr=csv.DictWriter(f,fieldnames=list(records[0]));wr.writeheader();wr.writerows(records)
    result=transform(tmp_path/'runs.csv',tmp_path/'prepared')
    assert result['chronological_seed_order']==chronological_seeds
    assert result['split_by_seed']=={97:'train',71:'train',42:'train',23:'validation',11:'test'}
    review=check(result['manifest'],minimum_events=40,minimum_windows=40)
    assert review['passed'],review
    summary,_,_,sessions=preview_import(result['jsonl'],result['manifest'])
    assert summary['events']==40
    # The importer MUST keep the same pseudonym separate per scenario AND seed.
    assert len(sessions)==40
    assert all(len(key)==3 for key in sessions)
    # Tampering with the paired JSONL must fail the acceptance gate.
    path=Path(result['jsonl']);lines=path.read_text(encoding='utf-8').splitlines()
    path.write_text('\n'.join(lines[:-1])+'\n',encoding='utf-8')
    failed=check(result['manifest'],minimum_events=40,minimum_windows=40)
    assert not failed['passed']
    assert not failed['checks']['paired_jsonl_counts_match']
