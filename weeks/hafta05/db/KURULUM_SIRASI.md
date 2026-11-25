## PostgreSQL kurulum

1. PostgreSQL 15+ icinde bos bir veritabani olusturun.
2. `psql -v ON_ERROR_STOP=1 -d logscope -f 01_research_core.sql`
3. `psql -v ON_ERROR_STOP=1 -d logscope -f 02_product_extensions.sql`

Ilk 13 tablo arastirma cekirdegi; 14 sonraki tablo ticari/uygulama tasarim katmanidir.
SQL calistirma bu ortamda PostgreSQL sunucusu olmadigi icin dogrulanmadi.

Gizlilik: ham IP, token, parola (hash disinda), cookie, body ve ham URL query parametreleri saklanmamalidir.
