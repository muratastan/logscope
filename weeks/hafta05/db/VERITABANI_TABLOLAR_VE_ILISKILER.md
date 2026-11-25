# LogScope Veritabani Tasarimi - 27 Tablo

> Bu tasarim bir PostgreSQL 15+ semasidir. SQL dosyalarinin veritabaninda calistirilmasi bu ortamda test edilmemistir.

**Arastirma cekirdegi:** 13 tablo
**Urun / SaaS genisletmesi:** 14 tablo
**Toplam alan:** 225
**Yabanci anahtar iliskisi:** 41

| Tablo | Katman | Sutun | Amac |
|---|---|---:|---|
| `users` | Arastirma | 6 | Kimlik ve kimlik dogrulama |
| `scenario_runs` | Arastirma | 9 | Normal/anormal trafik senaryolari |
| `ingestion_batches` | Arastirma | 10 | Dosya aktarim surecleri |
| `synthetic_sessions` | Arastirma | 5 | Anonim oturumlar |
| `http_events` | Arastirma | 12 | Gizlilik filtreli HTTP olaylari |
| `traffic_windows` | Arastirma | 18 | 1 dakikalik zaman/rota ozellikleri |
| `model_versions` | Arastirma | 11 | Model ve esik surumleri |
| `learned_patterns` | Arastirma | 5 | PrefixSpan sik gecisleri |
| `model_scores` | Arastirma | 9 | Her pencere icin M1-M4 skor |
| `alarms` | Arastirma | 10 | Hibrit kararlardan alarm kayitlari |
| `alarm_signals` | Arastirma | 7 | Alarmi aciklayan model sinyalleri |
| `alarm_reviews` | Arastirma | 6 | Insan incelemesi ve notlar |
| `evaluation_results` | Arastirma | 14 | B0-B2 test sonuc metrikleri |
| `workspaces` | Urun | 7 | SaaS calisma alanlari |
| `workspace_memberships` | Urun | 4 | Kullanici/alan rolleri |
| `user_invitations` | Urun | 9 | Ekip davet akis tasarimi |
| `password_reset_requests` | Urun | 6 | Sifre sifirlama jeton hashleri |
| `api_credentials` | Urun | 9 | API anahtar ozeti (duz metin degil) |
| `integrations` | Urun | 9 | Django, API, Locust, JSONL konfigurasyonlari |
| `onboarding_progress` | Urun | 4 | Ilk kurulum adimlari |
| `notifications` | Urun | 10 | Alarm/veri sistem bildirimleri |
| `notification_preferences` | Urun | 5 | Kullanici bildirim tercihleri |
| `report_exports` | Urun | 10 | Rapor isleri ve artefakt referanslari |
| `audit_events` | Urun | 8 | Hareketlerin denetim izi |
| `product_plans` | Urun | 7 | Gelecekteki plan tanimlari |
| `workspace_subscriptions` | Urun | 7 | Gelecekteki abonelik durumu |
| `invoices` | Urun | 8 | Gelecekteki fatura metadata (odeme yok) |

## PK ve FK kurallari

- Ana tablolar icin `id` kimligi veya bilesik PK vardir.
- Her FK, PostgreSQL `REFERENCES` bagiyla gercek tablolara baglidir.
- `http_events.event_uid` benzersizdir; ayni olay ikinci kez eklenmemelidir.
- Zaman/rota penceresi 1 dakika ile sinirlanmistir.
- `dataset_split` egitim, dogrulama ve test olarak etiketlenir; model ozelliklerine etiket veya senaryo kimligi sokulmaz.
- Abonelik ve odeme ekranlari icin tablolar ticari tasarimdir, gercek para akisi aktif degildir.

## Gorece en kritik baglantilar

- `synthetic_sessions.scenario_run_id` -> `scenario_runs.id`
- `http_events.ingestion_batch_id` -> `ingestion_batches.id`
- `http_events.scenario_run_id` -> `scenario_runs.id`
- `http_events.synthetic_session_id` -> `synthetic_sessions.id`
- `traffic_windows.scenario_run_id` -> `scenario_runs.id`
- `learned_patterns.model_version_id` -> `model_versions.id`
- `model_scores.window_id` -> `traffic_windows.id`
- `model_scores.model_version_id` -> `model_versions.id`
- `alarms.window_id` -> `traffic_windows.id`
- `alarms.model_version_id` -> `model_versions.id`
- `alarm_signals.alarm_id` -> `alarms.id`
- `alarm_signals.model_version_id` -> `model_versions.id`
- `alarm_reviews.alarm_id` -> `alarms.id`
- `alarm_reviews.reviewer_user_id` -> `users.id`
- `evaluation_results.model_version_id` -> `model_versions.id`
- `workspaces.owner_user_id` -> `users.id`
- `workspace_memberships.workspace_id` -> `workspaces.id`
- `workspace_memberships.user_id` -> `users.id`
- `user_invitations.workspace_id` -> `workspaces.id`
- `user_invitations.inviter_id` -> `users.id`
- `password_reset_requests.user_id` -> `users.id`
- `api_credentials.workspace_id` -> `workspaces.id`
- `integrations.workspace_id` -> `workspaces.id`
- `onboarding_progress.workspace_id` -> `workspaces.id`
- `onboarding_progress.changed_by_user_id` -> `users.id`
- `notifications.workspace_id` -> `workspaces.id`
- `notifications.user_id` -> `users.id`
- `notifications.related_alarm_id` -> `alarms.id`
- `notification_preferences.workspace_id` -> `workspaces.id`
- `notification_preferences.user_id` -> `users.id`
- `report_exports.workspace_id` -> `workspaces.id`
- `report_exports.requested_by` -> `users.id`
- `audit_events.workspace_id` -> `workspaces.id`
- `audit_events.actor_user_id` -> `users.id`
- `workspace_subscriptions.workspace_id` -> `workspaces.id`
- `workspace_subscriptions.plan_id` -> `product_plans.id`
- `invoices.subscription_id` -> `workspace_subscriptions.id`
- `scenario_runs.workspace_id` -> `workspaces.id`
- `ingestion_batches.workspace_id` -> `workspaces.id`
- `model_versions.workspace_id` -> `workspaces.id`
- `alarms.workspace_id` -> `workspaces.id`
