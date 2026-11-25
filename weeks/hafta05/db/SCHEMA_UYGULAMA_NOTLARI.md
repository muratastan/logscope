# Veritabani entegrasyonu icin dikkat edilmesi gerekenler

- PostgreSQL DDL `http_events.event_uid` ve `synthetic_sessions.session_ref` alanlarini UUID bekler. Mevcut SQLite demo ve ornek JSONL `sample-001` / `synthetic-s1` gibi dizeler kabul eder. Gercek PostgreSQL aktarimi oncesi bu kimliklerin UUIDv5 / UUIDv4 olarak tutarli donusturulmesi, oturum eslestirmelerinin de saklanmasi gerekir.
- PostgreSQL semasina henuz FastAPI ORM kodu baglanmadi. Uygulamanin SQLite `alarms`/`events` tablolari ve PostgreSQL mantiksal `alarms`/`http_events` tablolari farkli yapidadir. Alembic veya elle ETL adapteri olmadan otomatik gecis yapilamaz.
- Coklu calisma alanlarinin izolasyonu hem FK hem uygulama sorgularinda zorunlu filtreyle saglanmalidir. Bu tasarimda geriye uyumluluk nedeniyle bazi workspace_id sutunlari NULL olabilir; canli SaaS icin NOT NULL migrasyonu ve RLS siyaseti eklenmelidir.
- Model butunlugu: session / scenario run tutarliligi, pencere etiketi ve train-val-test sizintisi ayrica birim testlerle kontrol edilmelidir.
- Ticari tablolar API uzerinden etkin degildir; odeme ve e-posta servisi test edilmedi.
