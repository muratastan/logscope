"""Verify that deliberately failed HTTP simulations are not mislabeled normal."""
import json
import pytest
from scripts.run_locust_matrix import validate_case


def _capture(path,statuses,route='/auth/login/',delay=120):
    data=[{'event_uid':f'case-{i}','status_code':s,'route_template':route,'duration_ms':delay}
          for i,s in enumerate(statuses)]
    path.write_text('\n'.join(json.dumps(item) for item in data)+'\n',encoding='utf-8')
    return path


def test_failed_login_must_generate_actual_401(tmp_path):
    path=tmp_path/'captured.jsonl'
    _capture(path,[200]*10)
    with pytest.raises(RuntimeError,match='401'):
        validate_case(path,'anomaly_login_fail')
    _capture(path,[401]*5+[200]*5)
    assert validate_case(path,'anomaly_login_fail')['statuses'][401]==5


def test_error_case_must_generate_503_and_normal_must_not(tmp_path):
    path=tmp_path/'captured.jsonl'
    _capture(path,[503]*6+[200]*4)
    assert validate_case(path,'anomaly_5xx')['statuses'][503]==6
    with pytest.raises(RuntimeError,match='normal baseline'):
        validate_case(path,'normal_steady')


def test_latent_and_rare_route_gates(tmp_path):
    path=tmp_path/'captured.jsonl'
    _capture(path,[200]*10,route='/catalog/',delay=400)
    assert validate_case(path,'anomaly_latency')['events']==10
    with pytest.raises(RuntimeError,match='rare route'):
        validate_case(path,'anomaly_rare_route')
    _capture(path,[200]*10,route='/admin/export/',delay=100)
    assert validate_case(path,'anomaly_rare_route')['events']==10
