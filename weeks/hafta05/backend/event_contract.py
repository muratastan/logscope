"""Pure privacy allowlist validation. No database side effects."""
import re
from datetime import datetime
ALLOWED_EVENT_KEYS={'event_uid','occurred_at','http_method','route_template','status_code','duration_ms','session_ref','schema_version'}

def valid_event(d):
    if not isinstance(d,dict) or set(d)-ALLOWED_EVENT_KEYS:return None
    try:
        uid,stamp,method,route,status,duration=(d[v] for v in ['event_uid','occurred_at','http_method','route_template','status_code','duration_ms'])
        if not isinstance(uid,str) or not re.fullmatch(r'[A-Za-z0-9._-]{1,96}',uid):return None
        if not isinstance(stamp,str) or not re.fullmatch(r'\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?(?:Z|[+-]\d\d:\d\d)',stamp):return None
        datetime.fromisoformat(stamp.replace('Z','+00:00'))
        if method not in ('GET','POST','PUT','PATCH','DELETE','HEAD','OPTIONS') or not isinstance(route,str) or not re.fullmatch(r'/[\w/{}/-]{0,150}',route):return None
        if type(status)!=int or not 100<=status<=599 or not isinstance(duration,(int,float)) or type(duration)==bool or not 0<=duration<=1e7:return None
        ref=d.get('session_ref')
        if ref is not None and (not isinstance(ref,str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,80}',ref)):return None
        return {'uid':uid,'occurred_at':stamp,'method':method,'route':route,'status':status,'duration_ms':float(duration),'session_ref':ref}
    except (ValueError,TypeError,KeyError):return None

