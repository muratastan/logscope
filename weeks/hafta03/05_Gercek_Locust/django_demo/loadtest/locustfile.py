"""Eight repeatable, named Locust scenarios for LOCAL Django demo only.
Run with: locust -f loadtest/locustfile.py --host http://127.0.0.1:8001
Choose one scenario user class in Locust; enable anomaly endpoints explicitly.
Avoid production targets: these tests deliberately generate 5xx and latency.
"""
from locust import HttpUser,task,between
import random
import uuid
import os
import time
import itertools

class BaseScenario(HttpUser):
 _user_indices=itertools.count()
 abstract=True
 wait_time=between(.1,.3)
 def on_start(self):
  self.started_monotonic=time.monotonic()
  self.rng=random.Random(int(os.getenv("LOGSCOPE_TEST_SEED","42")) + 1009*next(BaseScenario._user_indices))
  self.client.headers.update({"X-LogScope-Session":str(uuid.uuid4())})

class NormalSteady(BaseScenario):
 @task(3)
 def catalog(self):self.client.get('/catalog/')
 @task(2)
 def item(self):self.client.get('/items/1/')

class NormalHourlyRise(BaseScenario):
 # Gradual rate increase within a 34-minute test, not merely the class name.
 def wait_time(self):
  elapsed=time.monotonic()-getattr(self,'started_monotonic',time.monotonic())
  return max(.04,.42-.35*min(1.0,elapsed/(34*60)))
 @task
 def browse(self):self.client.get('/catalog/');self.client.get('/search/')

class NormalCampaign(BaseScenario):
 # Temporary mid-run burst: still NORMAL traffic by experiment design.
 def wait_time(self):
  elapsed=time.monotonic()-getattr(self,'started_monotonic',time.monotonic())
  phase=(elapsed/(34*60))%1.0
  return .05 if .45<=phase<.68 else .40
 @task
 def campaign(self):self.client.get('/');self.client.get('/items/2/')

class NormalRouteMix(BaseScenario):
 @task
 def varied(self):self.client.get(self.rng.choice(['/','/catalog/','/search/','/items/1/','/forms/checkout/']))

class Anomaly5xx(BaseScenario):
 @task(3)
 def error(self):
  # HTTP 503 is intentionally generated; keep it in Django JSONL but do
  # not make Locust abort the experiment due to an EXPECTED response.
  with self.client.get('/testing/error/',name='/testing/error/',catch_response=True) as resp:
   if resp.status_code==503:resp.success()
   else:resp.failure(f'Expected controlled 503; received {resp.status_code}')
 @task
 def normal(self):self.client.get('/catalog/')

class AnomalyLatency(BaseScenario):
 @task
 def slow(self):self.client.get('/testing/slow/',name='/testing/slow/')

class AnomalyLoginFail(BaseScenario):
 @task
 def auth_attempts(self):
  # Controlled 401; query is never persisted in JSONL, no credentials are sent.
  for _ in range(4):
   with self.client.get('/auth/login/?simulate_failure=1',name='/auth/login/',catch_response=True) as resp:
    if resp.status_code==401:resp.success()
    else:resp.failure(f'Expected controlled 401; received {resp.status_code}')

class AnomalyRareRoute(BaseScenario):
 @task
 def rare(self):self.client.get('/');self.client.get('/admin/export/');self.client.get('/auth/login/')
