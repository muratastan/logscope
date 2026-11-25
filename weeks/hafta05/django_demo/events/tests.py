"""Django tests for route templates and private-field exclusion from JSONL."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from django.test import TestCase, override_settings

class SafeAccessLogTests(TestCase):
    def test_log_allowlist_route_anonymization_and_synthetic_session(self):
        with TemporaryDirectory() as tmp:
            path=Path(tmp)/'access.jsonl'
            with override_settings(LOGSCOPE_JSONL_PATH=path):
                resp=self.client.get('/items/123/?token=secret',HTTP_X_LOGSCOPE_SESSION='123e4567-e89b-42d3-a456-426614174000',HTTP_X_FORWARDED_FOR='10.1.2.3',HTTP_AUTHORIZATION='Bearer abc')
                self.assertEqual(resp.status_code,200)
                self.client.get('/catalog/',HTTP_X_LOGSCOPE_SESSION='123e4567-e89b-42d3-a456-426614174000')
            events=[json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]
        self.assertEqual(len(events),2)
        self.assertEqual(events[0]['route_template'],'/items/{id}/')
        self.assertEqual(events[0]['session_ref'],events[1]['session_ref'])
        allowed={'event_uid','occurred_at','http_method','route_template','status_code','duration_ms','session_ref','schema_version'}
        self.assertEqual(set(events[0]),allowed)
        content=json.dumps(events)
        for bad in ('token=secret','10.1.2.3','Bearer abc','123/'):
            self.assertNotIn(bad,content)

    def test_template_and_form(self):
        self.assertEqual(self.client.get('/').status_code,200)
        self.assertContains(self.client.get('/catalog/'),'Ürün kataloğu')
        self.assertContains(self.client.get('/search/?q=Sentetik'),'Arama')
        self.assertEqual(self.client.post('/forms/checkout/',{}).status_code,200)
        self.assertEqual(self.client.get('/testing/error/').status_code,404)
