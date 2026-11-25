# LogScope — 2, 3, 4 ve 5. Hafta Teknik Teslim Rehberi

**Dayanak:** `docs/LogScope_Proje_Onerisi_Kaynak.docx`, “İş Planı” tablosu. Bu dosya öğrencilerin ders projesi için hazırlanmış **kodu ve test kanıtlarını** gösterir. Üretim ortamı ya da bitmiş ticari SaaS onayı değildir.

## 1. Dört haftanın istenen işleri ve gerçekleştirilme düzeyi

| Hafta | Word'deki ister | Kaynaklar / çıktı | Doğrulama | Açık kalan koşul |
|---|---|---|---|---|
| **2 — Ar-Ge** | 6 Figma ekran, ER, veri sözlüğü, JSON middleware, 5 dk sunum | `design/figma_svg/` (6 düzenlenebilir SVG), `diagrams/drawio/` (use case, akış, ER), `db/veri_sozlugu_27_tablo.csv`, `contracts/logscope-event-v1.schema.json`, `django_demo/events/middleware.py` | Veri sözlüğü: 27 tablo, 225 alan, 41 FK; JSON alan beyaz liste ve gizlilik testleri | Gerçek Figma dosyası üzerindeki 6 ekranın tıklanabilir prototipi ayrı doğrulanmalı; beş dakikalık canlı sunum öğrenciler tarafından yapılacak |
| **3 — Veri ve başlangıç deneyleri** | 8 Locust senaryosu, etiketli 120.000+ HTTP istek, 1.200 dakika, 5 tohum, EDA, kronolojik ayrım, B0/B1 | `django_demo/loadtest/locustfile.py`, `scripts/run_locust_matrix.py`, `scripts/prepare_locust_dataset.py`, `scripts/verify_week3_acceptance.py`; **ayrı** çevrim dışı veri ve EDA `reports/hafta3/` | Çevrim dışı 142.726 olay / 1.200 pencere; 5 tohum üzerinde B0/IF hesaplandı; canlı koşucu kodu ve hazırlanma süreci test edildi | **Gerçek Django/Locust HTTP testleri henüz koşulmadı.** 120k gerçek istek ve 1200 pencerelik canlı kabul gerçekleşmiş sayılmaz |
| **4 — Yerel backend** | PostgreSQL migration, rol tabanlı giriş, FastAPI CRUD, Swagger, `.env.example` | `db/01..03*.sql`, `scripts/apply_postgres_migrations.py`, `scripts/import_canonical_postgres.py`, `backend/fullstack.py`, `docker-compose.yml`, `.env.example` | API giriş/oturum/rol/CSRF Origin/şema/SQL testi; 142.726 olay yükleme + analiz SQLite üzerinde doğrulandı | Canlı PostgreSQL kurulumu ve migrations **bu ortamda test edilemedi**; `ui_*` operasyonel şema ile 27 tabloluk araştırma şemasının tek ORM olarak birleştirilmesi ileriki iştir |
| **5 — React + M1** | React ekranlarını servise bağlama; K-Means/DBSCAN/IF kıyas; ara demo | `frontend/src/`, `backend/week5_cluster_compare.py`, `reports/hafta5/` | React 19 ekranın kaynak rotası / JSX denetimi; 5 tohumda eğitim-verisi tabanlı küme + IF test ölçümü | npm bağımlılıkları / React **tam derleme ve Chrome piksel düzeyi QA henüz yapılamadı**. Figma tasarımına birebir benzerlik doğrulanmadı |

## 2. Veri güvenliği ve çalışma kuralları

- JSONL alanları sadece `event_uid`, `occurred_at`, `http_method`, `route_template`, `status_code`, `duration_ms`, `session_ref`, `schema_version` olabilir. Etiket ve senaryo tohumu model girdisine konmaz.
- Gerçek IP, parola, erişim belirteci, çerez, sorgu değeri ve istek gövdesi kaydedilmez. Reddedilen ham satırlar saklanmaz.
- Giriş parolası PBKDF2 ile özetlenir; oturum çerezi HttpOnly, çarpraz origin mutasyonları engelli, yetki kontrolleri API tarafındadır. **Bu kontroller kendi başlarına üretim güvenliği belgesi değildir.**
- Django'nun hata/gecikme simülasyon rotaları sadece `127.0.0.1` testinde etkinleştirilmeli. Locust asla halka açık başka bir siteye yönlendirilmemeli.
- Fiyatlandırma, fatura, entegrasyon ve davet ekranlarının gerçek ödeme/e-posta servisleri mevcut değildir; bunlar açıkça demo/planlama akışlarıdır.

## 3. 3. hafta çevrim dışı deney kanıtı

`reports/hafta3/dataset_summary.json` içinde (seed=42) 1.200 pencerede **142.726** anonim JSONL kaydı, sekiz senaryo, 9.909 sentetik oturum grubu yer alır. Kronolojik bölünme **720 eğitim + 240 doğrulama + 240 test** penceresidir. Dosyanın adı `logscope_offline_seed42_1200m.jsonl`. **Bu kayıtlar canlı HTTP isteği değildir; sentetik olay simülasyonudur.**

`reports/hafta5/model_comparison_by_seed.csv` dosyasında beş ayrı rastgele tohum (`11, 23, 42, 71, 97`) üzerinden **B0 sağlam z-skor, K-Means, DBSCAN çekirdek yakınlığı, B1 Isolation Forest ve B1+D** karşılaştırılmıştır. Ölçekleme ve modeller yalnız normal eğitim verisinde öğrenilir; eşikler yalnız doğrulama döneminde seçilir; test bölümü değerlendirmeye ayrılır. Testte DBSCAN yeniden eğitilmez.

| Yöntem | 5 simülasyon ortalama test F1 | Ortalama normal yanlış alarm oranı |
|---|---:|---:|
| B0 / sağlam hacim eşiği | 0,0000 | %5,67 |
| K-Means uzaklığı | 0,9774 | %4,67 |
| DBSCAN çekirdeğine uzaklık | 0,9681 | %6,67 |
| B1 Isolation Forest | 0,2154 | %6,50 |
| B1+D, IF + yoğunluk | 0,4365 | %5,50 |

Bu sayılar **yalnız çevrim dışı sentetik simülasyon sonuçlarıdır**. Sentetik örneklerin bazı yöntemlere kolay ayrışması yüksek F1 üretebilir. Gerçek Django/Locust verisi üzerinde aynı sayılar beklenmemelidir. Özellikle IF ve B1+D hedef F1>=0,80'e ulaşmamıştır; çeşitli yöntemler normal FPR<=%5 hedefini aşmıştır. B1+S ve B2 karşılaştırmaları sonraki (6. hafta) tam ablasyon aşamasında ayrıca tamamlanır; mevcut 5. hafta raporuna yanlışlıkla “tam B2 deneyleri” başlığı konmamalıdır.

## 4. 3. haftanın GERÇEK Locust matrisi (öğrenci bilgisayarında)

1. Django ve Locust kurulu, yerel Django çalışıyor, `.env` içinde yalnız test için `LOGSCOPE_ENABLE_ANOMALY_ENDPOINTS=1` olmalı.
2. `09_HAFTA3_LOCUST_WINDOWS.bat` çalıştırılabilir. Matris **8 senaryo × 5 seed × 34 dakika** sürecek şekilde planlandı; **yaklaşık 22 saat 40 dakika**, fazla kaynak gerektirir ve birden fazla oturuma yayılarak sürdürülebilir. Zaman/istek sayısına rağmen kabul eşiğine ulaşılmazsa test süresi yeniden artırılmalıdır. Bu script kesintiye dayanıklı manifest oluşturur.
3. Ardından `10_HAFTA3_ETIKET_KABUL_WINDOWS.bat` ile JSONL ve dakika etiketleri hazırlanır, karma/çakışan sınır dakikaları F1 hesabından ayrı tutulur.
4. Kabul şartları: **>=120.000 gerçek HTTP olayı, >=1.200 belirsiz olmayan dakika, sekiz senaryo, en az beş seed, eğitim/doğrulama/test dönemleri ve tekrar etmeyen dakika kimlikleri**. Script `reports/hafta3/live_locust_acceptance.json` içinde her koşul için gerçek PASS/FAIL üretir.
5. Yukarıdaki canlı veriler hazır olduğunda `scripts/import_canonical_postgres.py` ile PostgreSQL'e aktarılır. **Canlı Locust deneyleri bu ZIP oluşturulurken yürütülmemiştir.**

## 5. 4. hafta PostgreSQL ve CRUD yerel doğrulama

Önerilen PowerShell terminal komutları, proje kökünde:

```powershell
# Docker Desktop çalışıyor, .env parolaları değiştirilmiş olsun
docker compose up -d postgres
# .env: LOGSCOPE_USE_POSTGRES=1
.\.venv\Scripts\python.exe -m scripts.apply_postgres_migrations
.\.venv\Scripts\python.exe -m scripts.import_canonical_postgres --jsonl reports/hafta3/logscope_offline_seed42_1200m.jsonl --manifest reports/hafta3/scenario_manifest_seed42.csv --dry-run
# Dry run geçerse istemli olarak canlı PostgreSQL'e aktar:
.\.venv\Scripts\python.exe -m scripts.import_canonical_postgres --jsonl reports/hafta3/logscope_offline_seed42_1200m.jsonl --manifest reports/hafta3/scenario_manifest_seed42.csv
```

- **PG şema:** `logscope.*` altında 27 tasarım tablosu. Araştırma etiketleri `scenario_runs` ve dakika tablosunda saklanır, `http_events` model girdisinde olmaz.
- **API operasyonu:** PostgreSQL ayarı etkinse `public.ui_*` tablolarını kullanır. Bu, bilinçli bir geçiş katmanıdır; araştırma şemasıyla henüz tek tablo grubu değildir.
- **FastAPI:** `http://127.0.0.1:8000/api/docs`. `/api/traffic/windows` yüklenen olaylardan gerçek dakikalık istek, p50, p95, 4xx/5xx bilgisi çıkarır. `/api/ingest` 50 MiB /160 bin satıra kadar kabul eder, hatalı/çift UID'yi eler. Endpoint'lerin giriş/rol testleri otomatik olarak uygulanır.
- **Uçtan uca offline test:** geçici SQLite ile 142.726 olay / 1.200 dakika API'den geçirilmiş ve 5 keşifsel uyarı hesaplanmıştır. Kanıt: `reports/hafta4/e2e_local_smoke.json`. Bu bir PostgreSQL canlı testi değildir.
- PostgreSQL canlı migrations/CRUD için GitHub Actions taslağı `.github/workflows/hafta2_5_ci.yml` içinde otomatik kurulum aşamasına alınmıştır; CI henüz çalıştırılıp yeşil doğrulanmadı.

## 6. 5. hafta React ara demo

1. `02_FASTAPI_WINDOWS.bat` (API) ve `03_REACT_WINDOWS.bat` (React) ayrı terminallerde çalıştırılır. `http://127.0.0.1:5173/` üzerinde giriş yapılır.
2. `frontend/src/App.jsx` **5 ziyaretçi + 13 panel + dinamik alarm detayı = 19 ekran** rotasını içerir. Menülerin tamamı React bileşenlerinden oluşur.
3. **Veri Kaynakları → JSONL Yükle → Analiz Et:** JSONL içe aktarma ve M1–M4 keşifsel analizi veritabanına kaydedilir.
4. **Trafik Analizi:** `/api/traffic/windows` API sonuçlarından dakikalık grafik, gecikme ve hata oranları gösterilir; veri yüklenmemişse ekran açıkça demo diye işaretlenir.
5. **Alarm Merkezi → Alarm Detayı:** inceleme durumunu değiştirme ve not kaydı API üzerinden gerçekleşir. **Raporlar** bölümünde CSV veritabanından gelir.
6. **Model Merkezi:** ayrı simüle B0–B2 deney sonuçları görüntülenir. Bunlar üretim başarımı değildir.
7. `08_HAFTA2_5_TEST_WINDOWS.bat` Python, 27 tablo, 19 rota, JSX testlerini doğrular. `cd frontend; npm install; npm run build` **kullanıcının Windows PC'sinde** ek doğrulanmalıdır; paket hazırlanırken npm kurulumu ortamda mümkün olmadı.

## 7. Test durumu (üretim testi gibi yorumlamayın)

| Kontrol | Sonuç |
|---|---|
| Pytest API/ML/gizlilik/veri sözleşmesi | 25 test başarıyla geçti (teslim hazırlanırken) |
| React JSX kaynak sözdizimi | 8 JS/JSX dosyası, 0 hata |
| React kaynak rota envanteri | 19/19 bileşen rotası kaynak düzeyinde mevcut |
| Statik teslim sözleşmesi | 19/19 denetim (27/225/41 ayrıca) |
| API yükleme / analiz | 142.726 kayıt, 1.200 dakika, 5 keşifsel uyarı, geçici SQLite |
| Figma tam prototip / görsel piksel QA | Bu çalışmada tekrar doğrulanmadı; Figma MCP limiti mevcut |
| PostgreSQL Docker canlı migration | Bu ortamda Docker/psycopg yok, doğrulanmadı |
| Django + Locust gerçek 120k HTTP | Bu ortamda Django/Locust yok, **henüz çalıştırılmadı** |
| React npm üretim derlemesi | npm bağımlılık indirmesi sınırlı, doğrulanmadı |
| 20 kullanıcı API p95 / panel p95 | Ölçülmedi; 9. hafta yük testinde ayrıca yapılır |

**Akademik doğruluk:** Teslim edilen kod ileriye dönük deneyleri kolaylaştırır; canlı yürütülmemiş deneyin tamamlandığını veya hedef F1/FPR değerlerinin sağlandığını ifade etmez.
