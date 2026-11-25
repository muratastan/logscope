from django_demo.events.privacy import build_safe_event,FIELDS


def test_route_template_and_no_sensitive_fields():
    safe=build_safe_event('GET','items/<int:item_id>/',200,16.5,
                           synthetic_session_header='123e4567-e89b-42d3-a456-426614174000',
                           event_uid='test-uid-01',timestamp='2026-10-28T14:00:00Z')
    assert safe['route_template']=='/items/{id}/'
    assert safe['session_ref']=='123e4567-e89b-42d3-a456-426614174000'
    assert safe['status_code']==200
    assert set(safe)==FIELDS
    assert not any(key in safe for key in ('ip_address','cookies','password','token','query','body'))


def test_invalid_session_cannot_be_logged():
    s=build_safe_event('POST','forms/checkout/',200,1.4,synthetic_session_header='Bearer user-secret')
    assert s['session_ref'] is None
    assert s['route_template']=='/forms/checkout/'


def test_same_synthetic_session_header_is_stable():
    uid='123e4567-e89b-42d3-a456-426614174000'
    a=build_safe_event('GET','catalog/',200,2,uid)
    b=build_safe_event('GET','search/',200,3,uid)
    assert a['session_ref']==b['session_ref']
