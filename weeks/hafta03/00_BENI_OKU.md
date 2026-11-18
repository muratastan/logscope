# LogScope | İP3 — 3. Hafta: Locust, EDA, Kronolojik Ayrım, B0/B1

**İş planındaki hedef:** 4 normal + 4 anormal Locust senaryosu, 5 farklı tohum, en az 120.000 GERÇEK HTTP isteği, en az 1.200 net bir dakikalık pencere, EDA, kronolojik train/validation/test, B0 (robust z-skor) ve B1 (Isolation Forest), 5 dk demo.

## İçerik
- `01_Rapor_ve_Sunum/`: Haftaya özel sonuç raporu ve kısa sunum.
- `02_OFFLINE_Veri/`: 146.435 adet **çevrimdışı sentetik olay** + ayrı etiket CSV + 1.200 özellik penceresi + veri kartı.
- `03_EDA_Grafikler/`: Gerçek kaynak CSV'den yeniden oluşturulmuş dört EDA grafiği.
- `04_B0_B1_Sonuclar/`: Test kümesi model sonuçları ve F1 grafiği, sadece B0/B1.
- `05_Gercek_Locust/`: 8 senaryoyu localhost Django'ya gönderecek Locust/Django kaynakları ve Windows komut dosyaları. **40 uzun test koşturulmadı**.
- `06_Tekrar_Uretim/`: Çevrimdışı B0/B1 hesaplarını mevcut araştırma kodundan yeniden üreten yardımcı betik. Paylaşılan araştırma motoru B1+D/B1+S/B2 de hesaplayabilir ama bu hafta yalnız B0/B1 raporlandı.

## Çevrimdışı veri ile gerçek HTTP kesinlikle karıştırılmamalı
Veri dosyası 5 tohum, 8 senaryo, 146.435 sentetik olay ve 1.200 dakikalık pencere içeriyor. Ayrım: 720 eğitim + 240 doğrulama + 240 test. Bu, Locust'un Django'ya gerçek HTTP istekleri gönderdiğinin kanıtı **değil**.

## B0/B1 ilk karşılaştırma (yalnız offline sentetik TEST)
- B0 robust z-skor: F1=0,0000, normal FPR=%5,00; testte gerçek anomalileri yakalayamadı.
- B1 Isolation Forest: F1=0,9417, normal FPR=%5,83; F1 hedefini sağlasa da normal yanlış alarm hedefi %5'i aşar.
- Bütün parametre öğrenmeleri yalnız eğitim, eşik seçimi doğrulama, son metrikler test üzerinden olmalıdır. Senaryo kodu/etiket model girdisi yapılmaz.

## Gerçek Locust testi nasıl tamamlanır?
1. `05_Gercek_Locust/01_KURULUM_WINDOWS.bat` ile Python/Django/Locust ortamını kur.
2. Bir terminalde `02_DJANGO_BASLAT_WINDOWS.bat` çalıştır. Yalnız **127.0.0.1** hedef kullanılmalı; sentetik hata/gecikme uçları herkese açık olmamalı.
3. Başka terminalde `03_LOCUST_8X5_WINDOWS.bat` ile 8×5 deney matrisini başlat; tahmini toplam 22 saat 40 dakika (34 dk × 40 koşu); kesilirse aynı klasörde devam edebilir.
4. `04_KABUL_VE_ETIKET_WINDOWS.bat` ile gerçekten oluşan HTTP olaylarını, 120k sayısını, 1200 pencereyi, senaryoları ve etiket bütünlüğünü doğrula.
5. **PASS raporu ve orijinal Locust CSV/manifest günlükleri oluşmadan gerçek HTTP gereği tamamlandı deme.**

## 5 dk demo planı
1. Problem ve 8 senaryo (40 sn)
2. Veri kartı ve 146.435 offline kayıt (50 sn)
3. EDA görselleri (90 sn)
4. Kronolojik ayrım ve sızıntı önleme (55 sn)
5. B0/B1 karşılaştırma ve dürüst sınırlılıklar (85 sn)
