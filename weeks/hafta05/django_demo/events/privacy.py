"""Pure allow-list schema builder for synthetic local HTTP traffic.

Intentional omission: client IP, raw URLs, query params, headers, cookies,
request/response bodies, account identifiers, and credentials.
"""
from datetime import datetime, timezone
import uuid

FIELDS = frozenset({
    'event_uid', 'occurred_at', 'http_method', 'route_template',
    'status_code', 'duration_ms', 'session_ref', 'schema_version',
})


def build_safe_event(method, matched_route, status, duration_ms, synthetic_session_header=None, *, event_uid=None, timestamp=None):
    route='/' + (matched_route or '').lstrip('/')
    route=route.replace('<int:item_id>','{id}')
    route=(route.rstrip('/')+'/' if route != '/' else '/')
    # The only accepted session identifier is a UUID supplied by synthetic Locust actors.
    session=None
    if synthetic_session_header:
        try: session=str(uuid.UUID(str(synthetic_session_header)))
        except (ValueError,AttributeError,TypeError): session=None
    result={
        'event_uid':event_uid or str(uuid.uuid4()),
        'occurred_at':timestamp or datetime.now(timezone.utc).isoformat().replace('+00:00','Z'),
        'http_method':str(method),
        'route_template':route,
        'status_code':int(status),
        'duration_ms':round(float(duration_ms),3),
        'session_ref':session,
        'schema_version':'1.0',
    }
    assert set(result)==FIELDS
    return result
