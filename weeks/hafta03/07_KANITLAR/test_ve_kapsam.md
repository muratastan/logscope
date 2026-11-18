# Hafta 3 · Test ve kapsam

- Kaynakta 8 ilgili pytest testi başarılı.
- Kullanıcının 18.11.2026 tarihinde paylaştığı ekran çıktısına göre Django ile Locust kısa demosu **8/8 senaryo**, **10.814 HTTP log kaydı** üretmiştir. Bu arşive ham makine günlükleri taşınmamıştır.
- B0/B1 çevrimdışı test: B0 F1 0,0000; B1 F1 0,9417; B1 normal FPR %5,83. Bu ölçümler gerçek Locust trafiği üzerinde yapılmadı.
- Tam 8×5 matris / 120.000 gerçek HTTP isteği / 1.200 gerçek dakika **açıktır**.
- Orijinal kullanıcı bilgisayarı raporu `05_Gercek_Locust/reports/hafta3/HIZLI_HTTP_DEMO/HIZLI_HTTP_SONUC.json` dosyasından alınarak `kanitlar/hafta3/` altına eklenebilir; hassas bilgileri kontrol edin.
