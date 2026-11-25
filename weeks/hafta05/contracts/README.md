# Hafta 2 — Log sözleşmesi

`logscope-event-v1.schema.json` kontrollü Django middleware tarafından JSONL şeklinde yazılan anonim HTTP olayının izinli alanlarını tanımlar. API'nin `valid_event` denetimiyle uyumludur.

- `event_uid`: tekrarları yakalamak için tekil kayıt kimliği.
- `occurred_at`: ofsetli UTC ISO-8601 tarih-saat.
- `http_method`, `route_template`: ham URL veya query yerine rota şablonu.
- `status_code`, `duration_ms`: durum ve gecikme.
- `session_ref`: **sentetik** oturum kimliği; gerçek oturum çerezi değildir.
- `schema_version`: `1.0`.

**Yasak alanlar:** IP, `Authorization`, parola, cookie, query, gövde, gerçek hesap ID'si. Hatalı satırlar analiz dışında kalır; yalnız reddedilen sayı raporlanır.

Senaryo etiketleri/seed/ayrım bilgisi **ayrı** `scenario_manifest.csv` içinde saklanır; bunların hiçbiri ML özelliklerine girmez.
