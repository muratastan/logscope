# LogScope - 5. hafta | GitHub ve Windows kurulum rehberi

**Gercek GitHub deposu:** https://github.com/muratastan/logscope (main). Mevcut `weeks/hafta03` ve `weeks/hafta04` klasorlerine dokunmayin. Bu ZIP direkt `weeks/hafta05/...` yapiya acilir.

## 1. Windows 10/11 gereksinimleri
- Python 3.11 veya 3.12 (kurulumda PATH'e ekleyin)
- Node.js 22.12+ veya 20.19+ (npm dahil)
- Git ve Visual Studio Code (Python, Pylance eklentileri)
- PostgreSQL icin Docker Desktop istege bagli. Ilk demo varsayilan SQLite ile acilir.

Kontrol icin VS Code PowerShell: `py -3 --version`, `node -v`, `npm -v`, `git --version`.

## 2. Depoyu bilgisayara indir ve hafta 5 klasorunu ekle
Bos klasorde PowerShell acin:

```powershell
git clone https://github.com/muratastan/logscope.git
cd logscope
git switch -c hafta05-react-api
```

Bu ZIP'i **`logscope` depo kokune** cikartin. `weeks/hafta05/README.md`, `weeks/hafta05/frontend/`, `weeks/hafta05/backend/` gorunmeli. ZIP klasorunun kendisini `weeks/hafta05` icine tekrar koymayin.

## 3. Projeyi VS Code'da calistir
- `File > Open Folder` ile `logscope/weeks/hafta05` klasorunu acin (`logscope.code-workspace` da acilabilir).
- Ilk sefer `00_KURULUM_WINDOWS.bat` dosyasini calistirin; bu `.venv` ve Python gereksinimlerini kurar, `.env.example` -> `.env` kopyalar.
- `.env` dosyasi icindeki demo parolasini **kendi parolanizla degistirin**; GitHub'a gondermeyin.
- Birinci terminalde `02_FASTAPI_WINDOWS.bat` -> API `http://127.0.0.1:8000/api/docs`.
- Ikinci terminalde `03_REACT_WINDOWS.bat` -> React `http://127.0.0.1:5173/#/login`.
- Ilk `03_REACT_WINDOWS.bat` calismasinda `npm install` ile Node gereksinimleri indirilir. Ilk kurulum internet gerektirir.
- Giris maili `demo@logscope.local`, sifre `.env` icinde `LOGSCOPE_DEMO_PASSWORD` degeri.
- Genel Bakis -> Hafta 5 Ara Demo Akisi: Giris -> Genel Bakis -> Trafik -> Model Merkezi -> Alarm Merkezi -> Alarm Detayi.
- Alarm Detayi'nda inceleme notu kaydedip sayfayi yenileyerek `GET /api/alarms/{id}` ve `POST /api/alarms/{id}/review` islemlerini kontrol edin.
- Model Merkezi tablosu **offline** deney raporunu API'den okur; gercek HTTP basarisi olarak sunmayin.

Eger `.bat` acilmiyorsa asagidaki komutlari 5. hafta proje kokunde **ayri** PowerShell terminallerinde calistirin:

```powershell
# Terminal 1
.\.venv\Scripts\python.exe scripts\run_api.py
```
```powershell
# Terminal 2
cd frontend
npm install
npm run dev
```

### API baglantisi yoksa
`http://127.0.0.1:8000/api/docs` acilmiyorsa FastAPI terminalini kontrol edin; React'in Vite proxy ayari `frontend/vite.config.js` icinde `/api -> http://127.0.0.1:8000`.

## 4. Test
5. hafta kokunde `24_HAFTA5_ENTEGRASYON_TEST_WINDOWS.bat` dosyasini calistirin. Ardindan mutlaka:

```powershell
cd frontend
npm install
npm run build
```

Bu teslimde 14/14 ilgili Python testi ve kaynak duzeyinde 19/19 rota, 9/9 JSX/JS kontrolu gecti; **gercek npm build ve tarayici kabul testi bu ortamda tamamlanmadi** (node_modules/Vite kurulu degildi). Basari olarak isaretlemeden kendi PC'nizde yapin.

## 5. GitHub'a gonder (depo ana klasorunde)

```powershell
git status --short
git add weeks/hafta05
git status --short
git commit -m "Hafta 5 React ekranlari ve FastAPI entegrasyonunu ekle"
git push -u origin hafta05-react-api
```

GitHub'da `Compare & pull request` tusuyla `hafta05-react-api` -> `main` PR olusturup Murat ile inceleyin, sonra birlestirin. **ZIP'i degil, acilmis kaynak kodlari yukleyin.** `.env`, `.venv`, `node_modules`, veritabani ve tokenlari kesinlikle push etmeyin. `git status --short` bunu kontrol eder. Dosya/yol hatasi durumunda PR'yi birlestirmeyin.

## 6. Hafta 5 kaynaktaki kabul kosullari
- React en az 6 sayfa API ile baglansin.
- K-Means, DBSCAN, Isolation Forest deneyleri ve model ekraninda kaynak etiketli metrikler gorunsun.
- Giriş, genel bakis, trafik, modeller, alarm listesi ve alarm detayi 5 dk ara demo ile gosterilsin.
- Canli PostgreSQL, tam React build, gerçek Locust trafik testleri ayrica dogrulanacak, su anda tamamlanmis sayilmaz.
