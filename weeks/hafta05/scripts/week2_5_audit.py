"""Static deliverable audit for LogScope Week 2-5 (not a substitute for live tests)."""
from pathlib import Path
import csv
import json
from collections import Counter
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
CHECKS={
'week2_six_figma_export_screens':len(list((ROOT/'design/figma_svg').glob('*.svg')))==6,
'week2_jsonl_contract':(ROOT/'contracts/logscope-event-v1.schema.json').is_file(),
'week2_data_dictionary':(ROOT/'db/veri_sozlugu_27_tablo.csv').is_file(),
'week2_erd_drawio':len(list((ROOT/'diagrams/drawio').glob('*.drawio')))>=5,
'week3_eight_locust_scenarios':sum('class '+name in (ROOT/'django_demo/loadtest/locustfile.py').read_text(encoding='utf-8') for name in
    ['NormalSteady','NormalHourlyRise','NormalCampaign','NormalRouteMix','Anomaly5xx','AnomalyLatency','AnomalyLoginFail','AnomalyRareRoute'])==8,
'week3_1200_offline_windows':(ROOT/'reports/hafta3/dataset_summary.json').is_file() and json.loads((ROOT/'reports/hafta3/dataset_summary.json').read_text(encoding='utf-8')).get('windows',0)>=1200,
'week3_five_seed_comparison':(ROOT/'reports/hafta3/baseline_summary_5seeds.json').is_file() and json.loads((ROOT/'reports/hafta3/baseline_summary_5seeds.json').read_text(encoding='utf-8')).get('iterations')==5,
'week3_real_locust_runner':(ROOT/'scripts/run_locust_matrix.py').is_file(),
'week3_live_acceptance_gates':(ROOT/'scripts/verify_week3_acceptance.py').is_file(),
'week4_pg_migrations':all((ROOT/'db'/p).is_file() for p in ('01_research_core.sql','02_product_extensions.sql','03_demo_plan_seed.sql')),
'week4_role_auth_and_crud':(ROOT/'backend/fullstack.py').is_file(),
'week4_canonical_pg_importer':(ROOT/'scripts/import_canonical_postgres.py').is_file(),
'week4_swagger':"docs_url='/api/docs'" in (ROOT/'backend/fullstack.py').read_text(encoding='utf-8'),
'week5_react_routes':(ROOT/'frontend/src/App.jsx').is_file(),
'week5_clustering_comparison':(ROOT/'backend/week5_cluster_compare.py').is_file(),
'week5_model_metrics':(ROOT/'reports/hafta5/model_comparison_by_seed.csv').is_file(),
'week5_real_ingested_traffic_route':"@app.get('/api/traffic/windows')" in (ROOT/'backend/fullstack.py').read_text(encoding='utf-8'),
}

with (ROOT/'db/veri_sozlugu_27_tablo.csv').open(encoding='utf-8-sig',newline='') as f: columns=list(csv.DictReader(f))
with (ROOT/'db/tum_iliskiler.csv').open(encoding='utf-8-sig',newline='') as f: foreign_keys=list(csv.DictReader(f))
CHECKS['27_tables_225_columns_41_links']=len({r['table'] for r in columns})==27 and len(columns)==225 and len(foreign_keys)==41

ui=(ROOT/'frontend/src/App.jsx').read_text(encoding='utf-8')
public=['/','/login','/register','/reset-password','/pricing']
auth=['/app/overview','/app/traffic','/app/models','/app/alarms','/app/sources','/app/reports','/app/settings',
      '/app/onboarding','/app/integrations','/app/team','/app/notifications','/app/help','/app/billing']
CHECKS['19_screen_route_sources']=all((f"'{u}'" in ui or f'"{u}"' in ui) for u in public+auth) and 'const match=page.match(' in ui and 'AlarmDetailPage app={app}' in ui

result={'passed':all(CHECKS.values()),'static_checks':CHECKS,
'week3_data_source':'offline statistical simulation, NOT real Django/Locust HTTP workload',
'week4_database_verification':'SQLite API tests; PostgreSQL live migration requires local Docker/psycopg',
'week5_frontend_verification':'JSX syntax checked; npm install/build and browser rendering require local npm/network'}
print(json.dumps(result,ensure_ascii=False,indent=2))
(ROOT/'reports/hafta2_5').mkdir(parents=True,exist_ok=True)
(ROOT/'reports/hafta2_5/static_audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
raise SystemExit(0 if result['passed'] else 2)
