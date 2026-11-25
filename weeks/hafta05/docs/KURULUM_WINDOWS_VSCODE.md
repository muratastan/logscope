# Windows 10/11 + VS Code: Sıfırdan Başlangıç

## 1. Kurulacak araçlar

- Python 3.11 veya 3.12 (Python kurulumunda **Add Python to PATH** işaretleyin)
- VS Code + Python, Pylance, ESLint ve Prettier eklentileri
- Node.js **22.12+** (veya en az 20.19+) + npm (React/Vite 7 için)
- Docker Desktop + WSL2 (PostgreSQL için; ilk gün şart değil)
- Git (GitHub için)

## 2. Projeyi aç

ZIP'i klasöre çıkartın. **`logscope.code-workspace`** dosyasına çift tıklayın veya `code .` ile aynı klasörü açın.

VS Code **Terminal > New Terminal** bölümünde proje kökünde olduğunuzdan emin olun. Kodlar **tek kökte** kalmalıdır; Django, FastAPI ve React için ayrı VS Code projeleri oluşturmayın.

## 3. Python ve gizli ayarlar

PowerShell veya CMD (Windows):

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
Copy-Item .env.example .env
```

`.env` içindeki parolaları **kendi yerel parolalarınızla** değiştirin. Gerçek token/parola/kişisel veri GitHub'a gönderilmez. `.env` Git tarafından yok sayılır.

VS Code'da **Ctrl+Shift+P > Python: Select Interpreter > .venv** seçin.

## 4. Django ile ilk çalışan HTML sitesi

Terminal 1:

```powershell
.\.venv\Scripts\python.exe scripts\run_django.py
```

Tarayıcı: `http://127.0.0.1:8001/`. Ürün listesi, arama, ürün ayrıntısı, deneme formu ve sentetik giriş rotası arasında gezinin. JSONL verisi `django_demo/generated_access.jsonl` dosyasına yazılır.

Django testleri:

```powershell
cd django_demo
..\.venv\Scripts\python.exe manage.py test events
cd ..
```

## 5. FastAPI + React

Terminal 2:

```powershell
.\.venv\Scripts\python.exe scripts\run_api.py
```

API ve Swagger: `http://127.0.0.1:8000/api/docs`.

Terminal 3:

```powershell
cd frontend
npm install
npm run dev
```

Ürün sitesi: `http://127.0.0.1:5173/`. React `/api` istekleri FastAPI'ye otomatik yönlenir. `npm run build` ile React derlemesini yerel bilgisayarınızda doğrulayın. İlk aşamada FastAPI SQLite kullanır; bu bilinçli olarak hızlı başlangıç içindir.

## 6. PostgreSQL'i aç

`.env` içine kendi güçlü parolalarınızı yazdıktan sonra:

```powershell
docker compose up -d postgres
```

Docker Desktop üzerinden `logscope` veri tabanı görünür. FastAPI'yi PostgreSQL'e yönlendirmek için `.env` içinde `LOGSCOPE_USE_POSTGRES=1` yapın ve API'yi yeniden başlatın. Django ayrı log üretim sistemidir; JSONL kaydı FastAPI aracılığıyla PostgreSQL'e aktarılır.

**Not:** Canonical 27 tablo `db/` SQL dosyalarıyla oluşturulur; mevcut FastAPI demo ORM ise `ui_*` tablolarına yazar. İkisini eşitleyen tam migration 4. hafta geliştirmesi olarak takip edilecek. PostgreSQL kurulumunu test etmeden başarılı demeyin.

## 7. Locust (yalnız kontrollü localhost testinde)

`.env` içindeki `LOGSCOPE_ENABLE_ANOMALY_ENDPOINTS=1` değerini ayarlayıp Django'yu yeniden başlatın, sonra Terminal 4'te:

```powershell
.\.venv\Scripts\python.exe scripts\run_locust.py
```

Arayüz: `http://127.0.0.1:8089/`, hedef: `http://127.0.0.1:8001/`. **Asla gerçek müşteriye veya internetteki başka siteye yük testi göndermeyin.**

## 8. İlerleme ve test

```powershell
.\.venv\Scripts\python.exe scripts\check_structure.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_fullstack.py tests\test_layout.py
```

İlk GitHub commit'inden önce `git status` ile `.env`, log, .venv, sqlite dosyalarının eklenmediğini kontrol edin. Geniş kullanım için CSRF, rate limiting ve oturum güvenliği artırılmalıdır.
