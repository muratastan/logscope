"""Privacy allow-list JSONL logger for local controlled Django/Locust traffic.

Only the explicitly allowed event fields are persisted.  Sensitive request
payloads, cookies, authorization headers, client addresses and query values
are never passed to the log serializer.
"""
import json
import threading
import time
from pathlib import Path
from django.conf import settings
from .privacy import build_safe_event

_LOCK = threading.Lock()

class SafeAccessLogMiddleware:
    def __init__(self,get_response):
        self.get_response=get_response

    def __call__(self,request):
        started=time.perf_counter()
        response=self.get_response(request)
        matched=getattr(request,'resolver_match',None)
        event=build_safe_event(
            method=request.method,
            matched_route=matched.route if matched is not None else '/',
            status=response.status_code,
            duration_ms=(time.perf_counter()-started)*1000,
            synthetic_session_header=request.headers.get('X-LogScope-Session'),
        )
        path=Path(settings.LOGSCOPE_JSONL_PATH)
        path.parent.mkdir(parents=True,exist_ok=True)
        with _LOCK, path.open('a',encoding='utf-8') as out:
            out.write(json.dumps(event,ensure_ascii=False)+'\n')
        return response
