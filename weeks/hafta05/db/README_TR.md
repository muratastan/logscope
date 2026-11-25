# PostgreSQL: Araştırma Şeması ve Operasyonel API

`db/01_research_core.sql` 13 araştırma tablosunu; `02_product_extensions.sql` çalışma alanı ve SaaS altyapı tablolarını oluşturur. Toplam 27 mantıksal tablo ve 41 FK (genişletme alanları dahil) tasarımı bulunmaktadır.

**Önemli:** Mevcut `backend/fullstack.py` API kodu `public.ui_*` adında ayrı operasyonel tablolar oluşturur. Bu sınıftaki alarm ve JSONL kayıtları *henüz* canonical 27 tabloya bire bir haritalanmamaktadır. Şema ile çalışma verilerini birbirine bağlama ve tek migrasyon/ORM modeli kurma işi 4. ve 7. haftaların teslimidir.

**Docker ile:** `.env` doldurulduktan sonra `docker compose up -d postgres`. Daha sonra gerekirse `LOGSCOPE_USE_POSTGRES=1` seçilip FastAPI çalıştırılır. `postgres` ilk boş volume başlatıldığında `01`, `02`, `03` SQL dosyalarını sırayla çalıştırır; volume doluyken otomatik yeniden çalıştırmaz. Üretim için veritabanı parolası, yetki, yedek, migration ayrıca ele alınmalıdır.

**Öncelikli tablolar:** `scenario_runs`, `ingestion_batches`, `synthetic_sessions`, `http_events`, `traffic_windows`, `model_versions`, `learned_patterns`, `model_scores`, `alarms`, `alarm_signals`, `alarm_reviews`, `evaluation_results`, `users`.

**Hassas alanlar:** IP, erişim belirteci, çerez, parola, istek gövdesi ve hassas sorgular kesinlikle kaydedilmez. PostgreSQL henüz bu ortamda canlı test edilmedi.
