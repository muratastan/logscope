# logscope
230291021 Murat Astan 230291033 Elif Feyza Ünal


LogScope 🔍

LogScope, Django tabanlı web uygulamalarında HTTP erişim loglarını (istek hacmi, rota bilgisi ve oturum örüntüleri) bağlam duyarlı olarak analiz eden, anomali tespiti ve açıklanabilir alarmlar üreten bir araştırma prototipidir.
Geleneksel yöntemlerin aksine, sadece istek sayısındaki artışa (hacme) odaklanmaz; trafik yoğunluğunun zamanı, ziyaret edilen rotalar ve kullanıcıların sayfa geçiş sıraları gibi bağlamsal özellikleri birleştirerek yanlış alarm oranını düşürmeyi hedefler.

🎨 Tasarım ve Arayüz (Figma)

Projenin SaaS ürün sitesi ve etkileşimli analitik panel tasarımlarına aşağıdaki bağlantıdan ulaşabilirsiniz:
👉 [Figma Tasarım Linki](https://www.figma.com/design/kIRsA8TcwvZBXdt3IeBIWB/LogScope-%7C-SaaS-%C3%9Cr%C3%BCn-Sitesi-ve-Etkile%C5%9Fimli-Panel-Tasar%C4%B1m%C4%B1?node-id=0-1&p=f)

🚀 Temel Özellikler & İsterler

• Güvenli & Anonim Loglama: OWASP ilkelerine uygun olarak ham IP, şifre, çerez, token veya hassas sorgu parametreleri kaydedilmeden JSONL formatında veri üretimi.
• Bağlam Duyarlı Analiz (M1 - M2 - M3):
	• M1 (Trafik Profili): K-Means ve DBSCAN ile dakika ve rota düzeyinde trafik yoğunluğu profilleme.
	• M2 (Anomali Skoru): Çok değişkenli pencereler üzerinde Isolation Forest ile sapma tespiti.
	• M3 (Sıralı Örüntü): PrefixSpan algoritması ile normal kullanıcı oturum içi geçiş rotalarının takibi.
• M4 Hibrit Karar Katmanı: Üç farklı analitik sinyalin doğrulama evresinde kalibre edilmiş eşiklerle birleştirilmesi.
• Açıklanabilir Analitik Panel: Üretilen alarmların zamanını, tetikleyici rotayı ve karara etki eden öznitelikleri gerekçeleriyle gösteren web arayüzü.

🎯 Hedeflenen Başarım Ölçütleri

Proje, deneysel bir prototip olup başarımı aşağıdaki sıkı metriklerle test edilmektedir:

Ölçüt Türü	Hedef Değer	Açıklama
Anomali Başarımı (F1)	≥ 0.80	Test kümesindeki anomali sınıfı F1 skoru
Yanlış Alarm Oranı (FPR)	≤ %5	Normal trafikte üretilen hatalı alarm oranı
API Yanıt Süresi (p95)	< 800 ms	20 eşzamanlı kullanıcı yükü altında
Panel Güncelleme Gecikmesi	≤ 15 sn	Pencere kapanışı ile panel yansıması arası süre
Test Kapsamı	≥ %70	Temel yazılım modüllerinin test kapsama oranı


🛠️ Teknoloji Yığını

• Backend: Django (Log Üretimi & Middleware), FastAPI (Analitik API Servisi)
• Frontend: React
• Veri Tabanı: PostgreSQL
• Veri Bilimi & ML: Python, Pandas, Scikit-Learn, Spmf/PrefixSpan araçları
• Test & Yük Dağıtımı: Pytest, Locust
• Altyapı: Docker & Docker Compose
