# Django ve Locust deney ortamı

Yalnızca yerel geliştirme amacıyla tasarlanmıştır. Üretim ortamında açılmamalıdır.

1. `pip install -r requirements.txt`
2. Test anomalileri için (yalnız yerel): `set LOGSCOPE_ENABLE_ANOMALY_ENDPOINTS=1`
3. `python manage.py migrate --noinput`
4. `python manage.py runserver 127.0.0.1:8001`
5. Ayrı terminal: `locust -f loadtest/locustfile.py --host http://127.0.0.1:8001`
6. Locust arayüzünden sekiz isimli kullanıcı sınıfından birini seçin.

Çıktı: `generated_access.jsonl`; ham IP, token, parola, body, çerez veya query tutulmaz.

Not: Django/Locust bağımlılıkları bu geliştirme ortamında kurulu olmadığı için uçtan uca çalıştırılması henüz doğrulanmadı. Test senaryolarında `Anomaly5xx` gerçek 503 hata yanıtı üretir.
