"""Eight repeatable, named Locust scenarios for LOCAL Django demo only.
Run with: locust -f loadtest/locustfile.py --host http://127.0.0.1:8001
Choose one scenario user class in Locust; enable anomaly endpoints explicitly.
Avoid production targets: these tests deliberately generate 5xx and latency.
"""
from locust import HttpUser,task,between
import random
import uuid
import os
import itertools

class BaseScenario(HttpUser):
 _user_indices=itertools.count()
 abstract=True
 wait_time=between(.1,.3)
 def on_start(self):
  self.rng=random.Random(int(os.getenv("LOGSCOPE_TEST_SEED","42")) + 1009*next(BaseScenario._user_indices))
  self.client.headers.update({"X-LogScope-Session":str(uuid.uuid4())})

class NormalSteady(BaseScenario):
 @task(3)
 def catalog(self):self.client.get('/catalog/')
 @task(2)
 def item(self):self.client.get('/items/1/')

class NormalHourlyRise(BaseScenario):
 @task
 def browse(self):self.client.get('/catalog/');self.client.get('/search/')

class NormalCampaign(BaseScenario):
 @task
 def campaign(self):self.client.get('/');self.client.get('/items/2/')

class NormalRouteMix(BaseScenario):
 @task
 def varied(self):self.client.get(self.rng.choice(['/','/catalog/','/search/','/items/1/','/forms/checkout/']))

class Anomaly5xx(BaseScenario):
 @task(3)
 def error(self):self.client.get('/testing/error/',name='/testing/error/')
 @task
 def normal(self):self.client.get('/catalog/')

class AnomalyLatency(BaseScenario):
 @task
 def slow(self):self.client.get('/testing/slow/',name='/testing/slow/')

class AnomalyLoginFail(BaseScenario):
 @task
 def auth_attempts(self):
  # No credentials are submitted. Generates route repetition only.
  for _ in range(4):self.client.get('/auth/login/')

class AnomalyRareRoute(BaseScenario):
 @task
 def rare(self):self.client.get('/');self.client.get('/admin/export/');self.client.get('/auth/login/')
