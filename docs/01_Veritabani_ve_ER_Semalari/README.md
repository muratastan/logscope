# 01 — Veritabanı ve ER Şemaları

**LogScope veritabanı tasarımına ait 39 JPG çizim** ve düzenlenebilir Draw.io kaynağı bu bölümde ayrı tutulur. 

| Alt bölüm | İçerik | Adet |
|---|---|---:|
| [Genel Chen ER](01_Genel_Chen_ER/) | Veritabanının genel görünümü, 27 tabloyu kapsayan çizimler | **2 JPG** |
| [Modül ER](02_Modul_ER/) | Veri üretimi, modeller, yetkiler, bildirimler, abonelik gibi modül görünümleri | **10 JPG** |
| [Tablo bazlı Chen ER](03_Tablo_Bazli_Chen_ER/) | Her tablo için ayrı varlık, öznitelik ve ilişki görünümü | **27 JPG** |
| [Draw.io kaynağı](04_Drawio_Kaynaklari/) | 27 tabloluk özgün, düzenlenebilir Chen ER çizimi | **1 `.drawio`** |

> **Notasyon ayrımı:** `16`–`20` numaralı ilk beş modül resmi PK/FK tablo-ER gösterimindedir; **klasik Chen ER** olarak adlandırılmamalıdır. `21` ve `49` genel Chen kaynak görünümleridir. Bunlar aynı konunun iki sunumu olduğundan ikisi de arşivlenmiştir.

## 01 — Genel Chen ER

1. [ER Chen - Tum 27 Tablo](01_Genel_Chen_ER/21_TEKNIK_ER_Chen_-_Tum_27_Tablo.jpg)
2. [00 TUM 27 TABLO](01_Genel_Chen_ER/49_ER_MODUL_00_TUM_27_TABLO.jpg)

## 02 — Modül ER

1. [ER - Veri Uretimi ve Oturumlar](02_Modul_ER/16_TEKNIK_ER_-_Veri_Uretimi_ve_Oturumlar.jpg)
2. [ER - Modeller Skorlar ve Alarmlar](02_Modul_ER/17_TEKNIK_ER_-_Modeller_Skorlar_ve_Alarmlar.jpg)
3. [ER - Kimlik ve Calisma Alani](02_Modul_ER/18_TEKNIK_ER_-_Kimlik_ve_Calisma_Alani.jpg)
4. [ER - Bildirimler Entegrasyonlar Raporlar](02_Modul_ER/19_TEKNIK_ER_-_Bildirimler_Entegrasyonlar_Raporlar.jpg)
5. [ER - Urun Paketi ve Fatura](02_Modul_ER/20_TEKNIK_ER_-_Urun_Paketi_ve_Fatura.jpg)
6. [01 Arastirma Veri Akisi](02_Modul_ER/50_ER_MODUL_01_Arastirma_Veri_Akisi.jpg)
7. [02 Modeller ve Alarmlar](02_Modul_ER/51_ER_MODUL_02_Modeller_ve_Alarmlar.jpg)
8. [03 Calisma Alani ve Erisim](02_Modul_ER/52_ER_MODUL_03_Calisma_Alani_ve_Erisim.jpg)
9. [04 SaaS Operasyonlari](02_Modul_ER/53_ER_MODUL_04_SaaS_Operasyonlari.jpg)
10. [05 Abonelik ve Fatura](02_Modul_ER/54_ER_MODUL_05_Abonelik_ve_Fatura.jpg)

## 03 — Tablo bazlı 27 Chen ER

1. [users](03_Tablo_Bazli_Chen_ER/22_ER_TABLO_users.jpg)
2. [scenario runs](03_Tablo_Bazli_Chen_ER/23_ER_TABLO_scenario_runs.jpg)
3. [ingestion batches](03_Tablo_Bazli_Chen_ER/24_ER_TABLO_ingestion_batches.jpg)
4. [synthetic sessions](03_Tablo_Bazli_Chen_ER/25_ER_TABLO_synthetic_sessions.jpg)
5. [http events](03_Tablo_Bazli_Chen_ER/26_ER_TABLO_http_events.jpg)
6. [traffic windows](03_Tablo_Bazli_Chen_ER/27_ER_TABLO_traffic_windows.jpg)
7. [model versions](03_Tablo_Bazli_Chen_ER/28_ER_TABLO_model_versions.jpg)
8. [learned patterns](03_Tablo_Bazli_Chen_ER/29_ER_TABLO_learned_patterns.jpg)
9. [model scores](03_Tablo_Bazli_Chen_ER/30_ER_TABLO_model_scores.jpg)
10. [alarms](03_Tablo_Bazli_Chen_ER/31_ER_TABLO_alarms.jpg)
11. [alarm signals](03_Tablo_Bazli_Chen_ER/32_ER_TABLO_alarm_signals.jpg)
12. [alarm reviews](03_Tablo_Bazli_Chen_ER/33_ER_TABLO_alarm_reviews.jpg)
13. [evaluation results](03_Tablo_Bazli_Chen_ER/34_ER_TABLO_evaluation_results.jpg)
14. [workspaces](03_Tablo_Bazli_Chen_ER/35_ER_TABLO_workspaces.jpg)
15. [workspace memberships](03_Tablo_Bazli_Chen_ER/36_ER_TABLO_workspace_memberships.jpg)
16. [user invitations](03_Tablo_Bazli_Chen_ER/37_ER_TABLO_user_invitations.jpg)
17. [password reset requests](03_Tablo_Bazli_Chen_ER/38_ER_TABLO_password_reset_requests.jpg)
18. [api credentials](03_Tablo_Bazli_Chen_ER/39_ER_TABLO_api_credentials.jpg)
19. [integrations](03_Tablo_Bazli_Chen_ER/40_ER_TABLO_integrations.jpg)
20. [onboarding progress](03_Tablo_Bazli_Chen_ER/41_ER_TABLO_onboarding_progress.jpg)
21. [notifications](03_Tablo_Bazli_Chen_ER/42_ER_TABLO_notifications.jpg)
22. [notification preferences](03_Tablo_Bazli_Chen_ER/43_ER_TABLO_notification_preferences.jpg)
23. [report exports](03_Tablo_Bazli_Chen_ER/44_ER_TABLO_report_exports.jpg)
24. [audit events](03_Tablo_Bazli_Chen_ER/45_ER_TABLO_audit_events.jpg)
25. [product plans](03_Tablo_Bazli_Chen_ER/46_ER_TABLO_product_plans.jpg)
26. [workspace subscriptions](03_Tablo_Bazli_Chen_ER/47_ER_TABLO_workspace_subscriptions.jpg)
27. [invoices](03_Tablo_Bazli_Chen_ER/48_ER_TABLO_invoices.jpg)

## Düzenlenebilir kaynak

- [LogScope_Orijinal_Chen_ER_27_Tablo.drawio](04_Drawio_Kaynaklari/LogScope_Orijinal_Chen_ER_27_Tablo.drawio)


Bu klasördeki çizimlerde yalnızca başlık/konu bakımından değil **farklı sunum düzeyleri** de bulunur. Ana raporda hepsini kullanmak zorunlu değildir.
