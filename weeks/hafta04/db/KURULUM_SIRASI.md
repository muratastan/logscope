# PostgreSQL migration sırası

PostgreSQL 16 ve Docker Desktop açık olmalıdır. `weeks/hafta04` kökünden:

```powershell
.\.venv\Scripts\python.exe -m scripts.setup_local_env
docker compose up -d --wait postgres
.\.venv\Scripts\python.exe -m scripts.apply_postgres_migrations
```

Bu mekanizma sırayla `01_research_core.sql`, `02_product_extensions.sql` ve `03_demo_plan_seed.sql` dosyalarını çalıştırır; `public.logscope_schema_migrations` tablosunda SHA-256'larını kaydeder. Aynı migration tekrar uygulanırken checksum eşleşmesi doğrulanır.

**Yerel kullanıcı deneyi (18.11.2026):** 27 kanonik tablo, 41 FK ve migration checksums PASS. Bu, `public.ui_*` operasyonel tablolarıyla tek ORM eşlemesi yapılmış olduğu anlamına gelmez.
