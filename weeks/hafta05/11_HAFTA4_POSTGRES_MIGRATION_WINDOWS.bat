@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (echo Once kurulum yapin. & pause & exit /b 1)
if not exist .env (echo .env dosyasi yok. & pause & exit /b 1)
echo PostgreSQL Docker Desktop ile baslatilmali; .env LOGSCOPE_USE_POSTGRES=1 olmali.
.venv\Scripts\python.exe -m scripts.apply_postgres_migrations
if errorlevel 1 (echo Migration basarisiz. & pause & exit /b 1)
echo Migration basarili. Canli veri yukleme icin docs/HAFTA2_5_TESLIM.md dosyasina bakin.
pause
