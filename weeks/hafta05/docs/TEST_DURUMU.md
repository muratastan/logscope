# Test ve doğrulama durumu — 2–5. haftalar

- `python -m pytest -q tests`: **25 test geçti** (SQLite API, güvenlik, araştırma, veri sözleşmesi, canlı manifest hazırlayıcı küçük test).
- `python -m scripts.week2_5_audit`: **tüm statik teslim denetimleri geçti** (`reports/hafta2_5/static_audit.json`).
- `cd frontend && npm run check:jsx`: 8 JS/JSX dosyası, 0 parse hatası.
- `cd frontend && npm run check:routes`: 19 ekranın kaynak rota envanteri geçerli.
- 142.726 sentetik anonim JSONL olayı geçici SQLite API'ye yüklenip analiz edildi (1.200 pencere, 5 keşifsel alarm). Ayrıntı: `reports/hafta4/e2e_local_smoke.json`.
- **Bu ortamda yapılamayan:** React npm bağımlılık yükleme / Vite build / tarayıcı görsel QA, PostgreSQL canlı migration ve canonical import, Django/Locust gerçek 40 deneme matrisi, Figma piksel düzeyi doğrulama. GitHub Actions `.github/workflows/hafta2_5_ci.yml` bu doğrulamalar için taslak sağlar; henüz çalıştırılmış bir CI sonucu yoktur.
- Çevrim dışı W3/W5 F1 ve FPR raporu gerçek HTTP deneyi değildir. Bu ayrım `docs/hafta2_5/HAFTA2_5_TESLIM.md` içinde açıklanır.
