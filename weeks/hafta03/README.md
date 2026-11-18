# LogScope · Hafta 3 / İP3

**Kapsam:** 4 normal + 4 anormal Locust trafik senaryosu, JSONL loglama, EDA, kronolojik veri bölünmesi ve başlangıç B0/B1 anomali kıyası. Bu klasör **sadece 3. haftadır**; eski diyagramlar veya 4. hafta API kodları tekrar eklenmedi.

## Mevcut kanıtlar ve sınırlar

- Çevrimdışı **simüle** veri: 146.435 olay, 1.200 dakikalık pencere, 5 tohum ve 8 senaryo; bölünme 720/240/240.
- Çevrimdışı test: **B0 F1=0,0000, B1 F1=0,9417, B1 normal FPR=%5,83**. B1 hedef F1'i karşılarken FPR %5 hedefini geçmektedir.
- **Kısa gerçek HTTP demo:** Kullanıcının 18.11.2026'da paylaştığı terminal ekranına göre 8/8 Locust senaryosu başarıyla çalışmış ve 10.814 HTTP log kaydı üretilmiştir. Bu arşivde *orijinal canlı demo JSON/CSV kanıtları bulunmamaktadır*; bilgisayardaki gerçek raporun eklenmesi gerekir.
- **Tam deney açık:** 8×5=40 uzun koşu, en az 120.000 gerçek istek ve 1.200 gerçek pencere doğrulanmadı. Kısa demo tam deney yerine geçmez. Çevrimdışı model puanları canlı HTTP verisinde ölçülmüş değildir.

## Gereksinimler

Python 3.11/3.12, Windows PowerShell ya da macOS/Linux kabuğu, internet bağlantısıyla ilk Python paket kurulumu. Gerçek Locust yalnızca `http://127.0.0.1:8001` hedefinde çalışır; üretim ortamına trafik gönderilmez.

## Çalıştırma — terminal komutları (`.bat` gerekmez)

**1. Sanal ortam ve paketler (kökünüz `weeks/hafta03`):**

```powershell
cd 05_Gercek_Locust
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q tests/test_week3_integrity.py tests/test_week3_live_pipeline.py tests/test_live_run_integrity.py tests/test_live_scenario_truth.py
```

**2. Django terminali (05_Gercek_Locust klasöründe; bu pencere açık kalsın):**

```powershell
$env:LOGSCOPE_ENABLE_ANOMALY_ENDPOINTS = '1'
$env:LOGSCOPE_JSONL_PATH = (Join-Path (Get-Location).Path 'django_demo\generated_access.jsonl')
.\.venv\Scripts\python.exe django_demo\manage.py runserver 127.0.0.1:8001 --noreload
```

**3. Ayrı terminalde kısa Locust testi (aynı 05_Gercek_Locust klasöründe):**

```powershell
$env:LOGSCOPE_ENABLE_ANOMALY_ENDPOINTS = '1'
$env:LOGSCOPE_JSONL_PATH = (Join-Path (Get-Location).Path 'django_demo\generated_access.jsonl')
.\.venv\Scripts\python.exe -m scripts.run_quick_locust --seconds-per-case 25 --users 8 --seed 11 --out reports/hafta3/HIZLI_HTTP_DEMO
```

Beklenen makine çıktısı: `05_Gercek_Locust/reports/hafta3/HIZLI_HTTP_DEMO/HIZLI_HTTP_SONUC.json`. Bu dosya yerelde oluşur. Orijinal sonuçları gözden geçirip `kanitlar/hafta3/` altına kopyalayarak yayımlayın; ham HTTP JSONL'yi otomatik olarak GitHub'a eklemeyin.

**4. Kaynak simülasyonunu açıp B0/B1'i yeniden hesaplama (hafta03 kökünden):**

```powershell
py -3 tools/restore_offline_data.py
.\05_Gercek_Locust\.venv\Scripts\python.exe 06_Tekrar_Uretim/TEKRAR_URET_B0_B1.py
.\05_Gercek_Locust\.venv\Scripts\python.exe 03_EDA_Grafikler/EDA_YENIDEN_URET.py
```

Tam araştırma matrisi için `05_Gercek_Locust/scripts/run_locust_matrix.py` ve `scripts/verify_week3_acceptance.py` mevcuttur; 40 uzun koşu burada tamamlanmış olarak sunulmamaktadır.

## Kaynak dosyalar

- `02_OFFLINE_Veri/*.jsonl.gz`: tam çevrimdışı veri, **kayıpsız** sıkıştırılmıştır (GitHub tarayıcı limiti için). `tools/restore_offline_data.py` SHA-256 ile geri açar.
- `03_EDA_Grafikler/`: analiz kodu ve PNG çıktıları.
- `04_B0_B1_Sonuclar/`: CSV/JSON ölçümleri ve grafik.
- `05_Gercek_Locust/`: Django ve Locust Python kaynakları, veri kontrolü ve testler.
- `01_Rapor_ve_Sunum/`: düzenlenebilir Word ve PowerPoint teslimi.
- `kanitlar/hafta3/`: kullanıcı bilgisayarından kısa Locust özet raporu buraya eklenebilir.

**GitHub:** Bu klasör `weeks/hafta03/` yolu korunarak pushlanmalıdır. Ortam klasörleri (`.venv`), parolalar (`.env`) ve ham gerçek loglar pushlanmamalıdır.
