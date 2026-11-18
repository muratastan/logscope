"""Integrity of declared local Locust captures. Does not assert real traffic was run."""
from datetime import datetime,timedelta,timezone
import hashlib
import json
from pathlib import Path
import uuid
from scripts.run_locust_matrix import write_manifest,validate_case
from scripts.verify_live_runs import verify


def _make_capture(tmp_path):
    path=tmp_path/'trial.jsonl';base=datetime.now(timezone.utc)
    sid=str(uuid.uuid4())
    records=[{'event_uid':f'verify-{i}','occurred_at':(base+timedelta(seconds=i)).isoformat(),
              'http_method':'GET','route_template':'/catalog/','status_code':200,
              'duration_ms':30.,'session_ref':sid,'schema_version':'1.0'} for i in range(5)]
    path.write_text(''.join(json.dumps(row)+'\n' for row in records),encoding='utf-8')
    record={'seed':11,'scenario':'normal_steady','label':'normal',
            'start_unix':base.timestamp()-1,'finish_unix':base.timestamp()+6,
            'request_rows':5,'log_file':path.name,'capture_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'test_duration_minutes':1,'users':2}
    write_manifest(tmp_path,[record])
    return path,tmp_path/'locust_runs_manifest.csv'


def test_sha256_and_uuid_checks_pass_for_a_canonical_capture(tmp_path):
    capture,manifest=_make_capture(tmp_path)
    assert validate_case(capture,'normal_steady',strict_schema=True)['events']==5
    passed=verify(manifest,require_full_matrix=False)
    assert passed['passed']
    assert passed['total_verified_capture_rows']==5
    assert not passed['issues']


def test_mutated_or_contaminated_capture_rejected(tmp_path):
    capture,manifest=_make_capture(tmp_path)
    content=capture.read_text(encoding='utf-8')
    capture.write_text(content.replace('"duration_ms": 30.0','"duration_ms": 31.0',1),encoding='utf-8')
    result=verify(manifest,require_full_matrix=False)
    assert not result['passed']
    assert any('SHA256' in issue for issue in result['issues'])


def test_non_locust_request_detected(tmp_path):
    capture,manifest=_make_capture(tmp_path)
    data=[json.loads(line) for line in capture.read_text(encoding='utf-8').splitlines()]
    data[0]['session_ref']=None
    capture.write_text(''.join(json.dumps(row)+'\n' for row in data),encoding='utf-8')
    assert not verify(manifest,require_full_matrix=False)['passed']
