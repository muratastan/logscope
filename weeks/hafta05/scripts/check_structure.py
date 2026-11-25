"""Offline scaffold validation, including the project proposal's basic deliverables."""
import csv
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
required=['frontend/src/App.jsx','frontend/src/pages/ConnectedPages.jsx','frontend/src/product.css',
'backend/fullstack.py','backend/analysis.py','django_demo/manage.py','django_demo/events/middleware.py',
'django_demo/templates/base.html','django_demo/loadtest/locustfile.py','db/01_research_core.sql',
'db/02_product_extensions.sql','docker-compose.yml','docs/HAFTA_HAFTA_YOL_HARITASI.md',
'diagrams/drawio/05_Tum_Tablolar_Chen_ER_1.drawio']
missing=[p for p in required if not (ROOT/p).is_file()]
with (ROOT/'db'/'veri_sozlugu_27_tablo.csv').open(encoding='utf-8-sig') as f:
    fields=list(csv.DictReader(f))
with (ROOT/'db'/'tum_iliskiler.csv').open(encoding='utf-8-sig') as f:
    relations=list(csv.DictReader(f))
table_count=len({f['table'] for f in fields})
print(f'Klasörler: {len(required)-len(missing)}/{len(required)} · SQL tabloları: {table_count} · Alan: {len(fields)} · İlişkiler: {len(relations)}')
if missing: print('Eksikler:',missing)
assert not missing, missing
assert table_count==27 and len(fields)==225
assert len(relations)>=41
print('VS Code başlangıç yapısı: OK')
