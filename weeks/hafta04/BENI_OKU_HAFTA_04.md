# LogScope İP4 — Teslim özeti

Bu klasör yalnızca 4. hafta kodları, testleri, PostgreSQL şeması, raporu ve sunumunu içerir.

**18 Kasım 2026 kullanıcı yerel terminal kanıtı:** `real_postgres_api_acceptance.json` PASS, 27 tablo, 41 FK, üç migration SHA-256 eşleşmesi, FastAPI CRUD/auth/Swagger kontrolleri PASS. Ayrı pytest sonucu 6/6 PASS. SQLite kısa HTTP 9/9 PASS fakat PostgreSQL yerine geçmez.

Çalıştırma adımları artık `.bat` dosyalarında değil, kökteki `README.md` içindedir.

Orijinal rapor dosyası kullanıcının bilgisayarında `reports/hafta4/real_postgres_api_acceptance.json` konumunda üretilmiştir. Buraya eklenen `real_postgres_api_acceptance_terminal_kopyasi.json` kullanıcının sohbet içinde paylaştığı çıktıdan alınmıştır; doğrudan dosya kopyası değildir.

**Sınır:** Yerel kabul PASS, üretim güvenliği kanıtı değil; 27 kanonik tablo ile operasyonel `public.ui_*` tabloları tek ORM katmanında birleştirilmiş değildir.
