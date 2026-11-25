# LogScope · VS Code'da Tek Proje / Başlangıç Deposu

**Fırat Üniversitesi — Yapay Zekâ ve Veri Mühendisliği Tasarımı**

Bu repo, dersteki öneri formunun Django → anonim JSONL → PostgreSQL → FastAPI → React ve M1–M4 mimarisini uygulamaya dökmek için hazırlanmıştır. Proje henüz müşteri ortamında kullanıma hazır değildir.

## VS Code'da ilk yapacağınız işler

1. ZIP'i çıkarıp **`logscope.code-workspace`** dosyasını açın.
2. `docs/KURULUM_WINDOWS_VSCODE.md` adımlarını izleyin.
3. **Önce Django**'yu `http://127.0.0.1:8001/` adresinde açın; katalog/arama/form HTML şablonlarını görün.
4. **Sonra FastAPI**'yi `http://127.0.0.1:8000/api/docs` adresinde açın.
5. **Sonra React**'i `http://127.0.0.1:5173/` adresinde açın. Menüden 19 ekranı gezin.
6. **Son olarak PostgreSQL**'i Docker ile başlatın; `LOGSCOPE_USE_POSTGRES=1` yaparak API'yi bağlayın.

## Dosya yapısı

```text
LogScope_VSCode_Projesi/
├── .vscode/                 VS Code görevleri, debugger ve eklenti önerileri
├── frontend/                React + JSX/HTML + CSS, 19 ürün ekranı
│   └── src/{pages,components,services}/
├── backend/                 FastAPI, SQLAlchemy, M1-M4 analiz kodu
│   ├── fullstack.py          API
│   └── analysis.py           ML deney ve yüklenmiş JSONL analizi
├── django_demo/             Kontrollü Django trafik üretim sitesi
│   ├── templates/            Gerçek HTML şablonları
│   ├── static/               CSS
│   ├── events/middleware.py  Anonim JSONL erişim kaydı
│   └── loadtest/locustfile.py 8 senaryo
├── db/                      PostgreSQL araştırma SQL'i ve veri sözlüğü
├── diagrams/drawio/         22 teknik diyagram, gruplar halinde
├── docs/                    Kaynak öneri, 10 haftalık plan, kurulum
├── ornek_veri/              Sentetik örnek JSONL
├── prototip/                Çevrimdışı açılabilen 19 ekran HTML demo
├── tests/                   API ve klasör testleri
├── scripts/                 Yerel servis başlatıcıları
├── docker-compose.yml      PostgreSQL ve isteğe bağlı API container
├── .env.example             Güvenli ayar şablonu
└── logscope.code-workspace  VS Code tek çalışma alanı
```

## Çalışan kısımlar ile planlananları ayırın

- **Mevcut:** 19 React sayfa bileşeni ve 19 ekranlık HTML demo; önceki yerel FastAPI+SQLite testleri; sentetik M1–M4 hesaplamaları; Django HTML şablonları ve mahremiyet filtreli JSONL middleware kaynak kodu.
- **Kurulum doğrulaması gereken:** React `npm run build`, Django/Locust canlı testleri, PostgreSQL Docker başlatma.
- **Henüz yapılmamış araştırma koşulları:** Gerçek Django/Locust ile 120.000 istek; 5 tohumlu kontrollü eğitim/test tekrarları; PostgreSQL canonical model–API tam entegrasyonu; p95 yük testleri; F1≥0.80 hedefinin sağlanması.

19 ekranın tıklama haritası: [docs/19_EKRAN_HARITASI.md](docs/19_EKRAN_HARITASI.md).

Detaylı haftalık yol haritası: **[docs/HAFTA_HAFTA_YOL_HARITASI.md](docs/HAFTA_HAFTA_YOL_HARITASI.md)**.

---

## Yeni: 2–5. hafta bütünleşik çalışma paketi

**Başlangıç:** `HAFTA2_5_KURULUM_VE_TESLIM_TR.md`.

**Kanıt ve sınırlar:** `docs/hafta2_5/HAFTA2_5_TESLIM.md`. W3 çevrim dışı veri `reports/hafta3/`, W5 yöntem karşılaştırması `reports/hafta5/`, SQLite API uçtan uca test özeti `reports/hafta4/e2e_local_smoke.json`.

**Test:** `08_HAFTA2_5_TEST_WINDOWS.bat`. Gerçek localhost Locust matrisi: `09_HAFTA3_LOCUST_WINDOWS.bat`, kabul raporu: `10_HAFTA3_ETIKET_KABUL_WINDOWS.bat`. Canonical PostgreSQL migration: `11_HAFTA4_POSTGRES_MIGRATION_WINDOWS.bat`.

**Kodun önemli ayrımı:** 27 tabloluk `logscope.*` **araştırma** PostgreSQL şeması ile `ui_*` **operasyonel API** şeması şu anda birlikte bulunur. `scripts/import_canonical_postgres.py` araştırma veri aktarımını yapar; bunlar henüz tek ORM altında birleştirilmedi. Başarım hedefleri doğrulanmış sonuç değildir.
