# LogScope Ana Veri Kartı – 5 tohumlu offline veri

**Kim hazırladı:** LogScope ders projesi geliştirme sürecinde oluşturulan kod.  
**Kaynak:** İstatistiksel trafik simülasyonu (Django/Locust HTTP'si değil).  
**Sürüm:** LogScope-main-offline-v1.  
**Zaman:** Tamamı simüle edilmiş 1.200 farklı UTC dakika; gerçek 20 saatlik ölçüm yapılmadı.

**Boyut:** 146.435 anonim HTTP olay satırı, 1.200 dakika, 8 senaryo, 5 tohum (11, 23, 42, 71, 97).  
**Veri ayrımı:** 720 eğitim, 240 doğrulama, 240 test penceresi; tohumlar ayrık 3/1/1.  
**Kişisel veri:** IP, gerçek çerez, parola, token, gövde, ham query string içermez. `session_ref` sentetik oturum tanımlayıcısıdır.  
**Etiketler:** JSONL içinde değil, ayrı `logscope_ana_dakika_etiketleri.csv` dosyasındadır.  
**Öznitelikler:** 10 sayısal trafik/yanıt süresi/rota/oturum özelliği `logscope_ana_1200_pencere_ozellikleri.csv` içinde.

## Dosyalar

- `logscope_ana_5tohum_OFFLINE_SIMULASYON.jsonl`: ana olaylar.
- `logscope_ana_dakika_etiketleri.csv`: dakika etiketleri ve bölünmeler.
- `logscope_ana_1200_pencere_ozellikleri.csv`: hesaplanan özellikler (etiketsiz).
- `tohum_senaryo_ozeti.csv`: tohum ve bölünme sayıları.
- `veri_karti_ve_kabul_ozeti.json`: köken, sayımlar, SHA-256.
- `ANA_VERI_SETI_KABUL_RAPORU.json`: bağımsız veri doğrulama.

**Kabul:** Hacim ve şema açısından offline koşulları geçse de önerideki gerçek Django/Locust 120.000 HTTP isteği ve gerçek 1.200 dakika şartı henüz karşılanmadı. Akademik veya sunum metinlerinde bu ayrım korunmalıdır.
