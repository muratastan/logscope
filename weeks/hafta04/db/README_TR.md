# LogScope PostgreSQL araştırma ve ürün şeması

- `01_research_core.sql`: 13 araştırma tablosu
- `02_product_extensions.sql`: 14 ürün/SaaS tablosu
- `03_demo_plan_seed.sql`: geliştirme amaçlı başlangıç kayıtları

Yerel kabul sonucunda `logscope` içinde **27 tablo ve 41 FK** doğrulanmıştır (kullanıcının 18.11.2026 tarihli terminal çıktısı). Migration'lar `scripts.apply_postgres_migrations` betiğiyle checksum kontrollü uygulanır.

**Önemli mimari sınır:** FastAPI'nin `public.ui_*` tabloları operasyonel uygulama katmanıdır. Bu operasyonel model, `logscope.*` içindeki 27 kanonik tablo ile henüz tam ORM eşlemesinde birleştirilmiş değildir.

Kurulum için `KURULUM_SIRASI.md` ve üst klasördeki `README.md` dosyalarına bakın. Gizlilik: ham IP, parola, token, cookie, body veya hassas sorgu bilgilerini depolamayın.
