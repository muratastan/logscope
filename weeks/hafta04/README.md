# LogScope · Hafta 4 / İP4

**Kapsam:** PostgreSQL migration, rol tabanlı oturum açma, FastAPI CRUD, Swagger/OpenAPI ve `.env.example`. Bu klasör **sadece 4. haftadır**; daha önce GitHub'a eklenen diyagramlar tekrarlanmamıştır.

## Yerel kabul sonucu (18.11.2026)

Kullanıcının kendi Windows bilgisayarında paylaştığı terminal sonucuna göre:

- PostgreSQL 16 Docker konteyneri `healthy`.
- `logscope` şemasında **27 kanonik tablo, 41 FK** ve checksum'ı eşleşen 3 migration dosyası doğrulandı.
- FastAPI canlı PostgreSQL API kabulü: **`passed: true`**. Sağlık, Swagger, OpenAPI, yetkisiz erişim, demo girişi, oturum/rol, alarm, ekip, trafik, entegrasyon oluşturma/okuma ve logout kontrolleri geçti.
- İlgili `pytest` çalıştırması: **6 passed, 1 deprecation warning**.
- SQLite üzerinden ayrı kısa gerçek HTTP denemesi: **9/9 başarılı**, fakat SQLite PostgreSQL kanıtı değildir.

Bu sonuçlar **yerel test kanıtıdır**, üretim güvenliğinin onayı değildir. `backend/fullstack.py` içindeki operasyonel `public.ui_*` tabloları, `logscope.*` kanonik araştırma tablolarından ayrıdır; tüm iş akışı tek ORM modeliyle birleştirilmiş değildir.

## Çalıştırma — doğrudan terminal komutları, `.bat` yok

Windows PowerShell üzerinde, bulunduğun dizin `weeks/hafta04` olacak biçimde:

**1. Kurulum ve birim testleri:**

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m scripts.setup_local_env
.\.venv\Scripts\python.exe -m pytest -q tests/test_week4_security.py tests/test_week4_complete_integration_crud.py
```

Python 3.12 yüklüyse ilk komutta `py -3.12` kullanabilirsin. `.env` yalnızca kendi bilgisayarında oluşur; GitHub'a yükleme.

**2. Gerçek PostgreSQL ve SQL migration:**

```powershell
docker compose up -d --wait postgres
.\.venv\Scripts\python.exe -m scripts.apply_postgres_migrations
docker compose exec -T postgres psql -U logscope_dev -d logscope -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='logscope' AND table_type='BASE TABLE'"
```

**3. FastAPI (bu terminal açık kalsın):**

```powershell
.\.venv\Scripts\python.exe -m scripts.run_api
```

Swagger: <http://127.0.0.1:8000/api/docs>

**4. İkinci PowerShell terminalinde gerçek PostgreSQL kabul testi:**

```powershell
.\.venv\Scripts\python.exe -m scripts.week4_live_acceptance --api http://127.0.0.1:8000
```

`reports/hafta4/real_postgres_api_acceptance.json` dosyasında `passed: true` beklenir. SQLite denemesi gerektiğinde, tek komut: `.\.venv\Scripts\python.exe -m scripts.week4_http_smoke_sqlite` (PostgreSQL kanıtı değildir).

## Dosyalar ve teslim

- `backend/`: FastAPI uygulaması ve kendi bağımlılıkları.
- `db/`: araştırma ve ürün SQL şemaları ile migration kaynakları.
- `scripts/`: PostgreSQL kurulum, API başlatma ve doğrulama Python betikleri.
- `tests/`: yetkilendirme ve CRUD testleri.
- `reports/hafta4/`: mevcut SQLite sonuçları ve **kullanıcının gönderdiği terminal JSON'unun kopyası**; orijinal canlı raporunu kullanıcı bilgisayarından ayrıca eklemek en doğru kanıttır.
- `teslim/Hafta_04/`: Word raporu, PowerPoint ve sunum notları.

**Güvenlik:** `.env`, `.venv`, gerçek parolalar, cookie, token, ham loglar ve yerel SQLite veritabanlarını GitHub'a yükleme. `docker-compose.yml` yalnızca PostgreSQL'i Docker ile çalıştırır; FastAPI bu öğretim demosunda bilgisayarda başlatılır.

**GitHub:** Bu klasörü `weeks/hafta04/` konumunda tut ve kendi haftasının PR'ıyla birleştir.
