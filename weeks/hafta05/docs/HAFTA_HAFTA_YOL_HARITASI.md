# LogScope · 0-10. Hafta Geliştirme Planı

Bu plan doğrudan ders öneri formundaki İP0-İP10 sırasını takip eder. Etiketler **planlanan teslimlerdir**, otomatik tamamlandı sayılmazlar. Uygulama geliştirmeleri GitHub Issues ve iki kişilik PR incelemesiyle izlenmelidir.

| Hafta | İş paketi ve amaç | VS Code klasörleri | Tamamlanma kanıtı |
|---|---|---|---|
| 0 / Hazırlık | GitHub deposu, erişim, görev paylaşımı ve issue şablonu | `.github/`, `docs/` | GitHub erişimi, issue listesi |
| 1 / İP1 | Aktör/use-case, en az 3 hata dallı akış, sistem ve AI işlem hattı | `diagrams/` | Revizyon geçmişi olan draw.io dosyaları |
| 2 / İP2 | En az 6 Figma ekran, ER, veri sözlüğü ve anonim JSONL middleware | `frontend/`, `db/`, `django_demo/` | Figma prototipi, ER, middleware testi, 5 dk sunum |
| 3 / İP3 | Locust 8 senaryo, EDA, kronolojik bölünme, B0/B1 | `django_demo/loadtest/`, `backend/analysis.py`, `notebooks/` | Etiketli 120.000+ HTTP isteği, 1.200+ pencere, ilk deney ve 5 dk demo |
| 4 / İP4 | PostgreSQL migrations, rol tabanlı giriş, FastAPI CRUD, Swagger, .env | `db/`, `backend/` | Çalışan PostgreSQL, kontrollü yetki testleri, `/api/docs` |
| 5 / İP5 | React 6+ ekranın API'ye bağlantısı, K-Means/DBSCAN/IF karşılaştırması | `frontend/`, `backend/analysis.py` | Bütün ekran akışları ve ara demo |
| 6 / İP6 | PrefixSpan, DBSCAN eğitim çekirdeği uzaklığı, B2 ablation | `backend/analysis.py`, `tests/` | B1/B1+D/B1+S/B2 kıyas ve kalibrasyon raporu |
| 7 / İP7 | Django log → pencere → skor → açıklama → alarm MVP | `django_demo/`, `backend/`, `frontend/` | Öngörülmeyen JSONL dosyasıyla uçtan uca kabul testi |
| 8 / İP8 | Docker Compose, arka plan analiz işçisi, sürümleme ve canlı demo | `docker-compose.yml`, `backend/`, `docs/` | Tek komutla yerel kurulum; canlı link (güvenlikten sonra) |
| 9 / İP9 | Locust 20 kullanıcı, pytest, girdi/şema/gizlilik testi | `tests/`, `django_demo/loadtest/` | 20 kullanıcı, en az 10 dk, 1000+ API isteği, p95 ölçümü |
| 10 / İP10 | F1/FPR/PR eğrisi, karışıklık matrisi, ablation, rapor, video ve v1.0 | `docs/`, `reports/`, `tests/` | 15 dk sunum, tekrar üretilebilir sonuçlar |

## Bilimsel ve işlevsel sabitler

- Sekiz trafik senaryosu: dört normal (durağan trafik, saatlik artış, kampanya, rota çeşitliliği), dört sapma (5xx, gecikme, başarısız giriş, seyrek rota).
- Pencere özellikleri: dakika/rota isteği, 4xx/5xx, p50/p95 süre, rota çeşitliliği ve istek aralığı.
- Kronolojik **%60 eğitim / %20 doğrulama / %20 test**. Model ve eşik testte öğrenilmez; senaryo kimliği model girdisi değildir.
- M1: K-Means ve DBSCAN, M2: Isolation Forest, M3: PrefixSpan, M4: birleşik karar. B0, B1, B1+D, B1+S, B2 sabit testte kıyaslanır.
- **F1 >= 0,80, normal FPR <= %5, 20 kullanıcıyla API p95 < 800 ms, panel p95 <= 15 sn** önceden kazanılmış sonuç değil hedeflerdir.
- 5 tohum × 8 senaryo, %95 bootstrap belirsizlik aralığı hedefi.
- Gizlilik: IP/parola/token/çerez/gövde/hassas query kaydetmeyin.

## Şu an neler devralındı?

- 19 ekranlık React/HTML kodu ile FastAPI demo API'si vardır; gerçek Figma piksel denetimi ve React derlemesi bu paket hazırlanırken doğrulanamamıştır.
- `backend/analysis.py` M1–M4 için kod içerir; sentetik simülasyon sonuçları gerçek Locust trafiğiyle karıştırılmamalıdır.
- 27 tabloluk tasarım ve draw.io seti vardır; PostgreSQL'in canlı migrasyon doğrulaması yapılacaktır.
- Django trafik uygulamasına HTML şablonları, erişim log middleware'i ve oturum sürekliliği testi eklendi.

## Önerilen ilk GitHub Issues

- [ ] [W0] Depo erişimi / görev paylaşımı / dal kuralları
- [ ] [W1] Şekil 1 yön okları ve 3 hata dallı akışı birlikte gözden geçirme
- [ ] [W2] Django JSONL middleware birim testleri
- [ ] [W2] Draw.io / veri sözlüğü / PostgreSQL sözleşmesi uyumu
- [ ] [W3] 8 Locust senaryosunu farklı seed'lerle ayrı ayrı etiketleme
- [ ] [W4] canonical `http_events` ve `ui_events` kayıtlarını tek ORM/migration altında birleştirme
- [ ] [W5] 19 React ekranını gerçek Figma üzerinden görsel karşılaştırma ve kullanıcı testleri
