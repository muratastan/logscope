# LogScope Hafta 2–5 — Hızlı Başlangıç

ZIP'i açıp `logscope.code-workspace` dosyasını VS Code ile açın. Tüm komutlar proje kökünden çalıştırılır.

## Kurulum ve ekranları açma

1. `00_KURULUM_WINDOWS.bat`: Python sanal ortamı, Django, Locust, FastAPI, scikit-learn ve test paketleri. İnternet gerektirir.
2. `.env` dosyasında örnek parolaları **değiştirin**. `.env` Git'e yüklenmez.
3. Terminal 1: `01_DJANGO_WINDOWS.bat` → `http://127.0.0.1:8001/` (kontrollü site ve anonim JSONL üretimi).
4. Terminal 2: `02_FASTAPI_WINDOWS.bat` → `http://127.0.0.1:8000/api/docs` (API, giriş, alarm, analiz).
5. Terminal 3: `03_REACT_WINDOWS.bat` → `http://127.0.0.1:5173/` (19 ekranlı gerçek React site).
6. Veritabanı: `04_POSTGRES_WINDOWS.bat`; `.env` içinde `LOGSCOPE_USE_POSTGRES=1` yapın ve `11_HAFTA4_POSTGRES_MIGRATION_WINDOWS.bat` çalıştırın, sonra API'yi yeniden başlatın.

## Test ve haftalık deney komutları

- `08_HAFTA2_5_TEST_WINDOWS.bat`: pytest + 27 tablolu şema + JSX + React rota doğrulama.
- `12_HAFTA5_DENEY_WINDOWS.bat`: **çevrim dışı** beş tohumlu B0/K-Means/DBSCAN/IF karşılaştırması; ölçümler `reports/` içinde.
- `09_HAFTA3_LOCUST_WINDOWS.bat`: **gerçek localhost Django HTTP** senaryo matrisi. Anomali uç noktaları yalnız yerelde açılmalı. Bu varsayılan 40 koşulu, 34 dakika/koşu nedeniyle uzun sürelidir; gerektiğinde kaldığı yerden devam eder.
- `10_HAFTA3_ETIKET_KABUL_WINDOWS.bat`: gerçek HTTP dosyalarını ayrı etiketlerle birleştirir, 120k/1200/5 seed/8 senaryo hedeflerine PASS/FAIL yazar.
- `python -m scripts.import_canonical_postgres --jsonl reports/hafta3/logscope_offline_seed42_1200m.jsonl --manifest reports/hafta3/scenario_manifest_seed42.csv --dry-run`: veri sözleşmesini PostgreSQL'e yazmadan denetler.

**Detaylı hafta bazlı teslim raporu:** `docs/hafta2_5/HAFTA2_5_TESLIM.md`

**Önemli:** 142.726 olaylık veri çevrim dışı simülasyondan üretildi; gerçek HTTP/Locust çalışması değildir. PostgreSQL canlı kurulumu ve React build işlemi bu teslim ortamında doğrulanmadı. Gerçek deney hedefleri ancak ilgili kontrol çıktıları geçtikten sonra tamamlanmış sayılır.
