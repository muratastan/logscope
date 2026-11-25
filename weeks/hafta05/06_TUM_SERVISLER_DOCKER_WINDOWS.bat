@echo off
cd /d "%~dp0"
if not exist ".env" copy ".env.example" ".env"
echo .env dosyasindaki ornek parolalari degistirdiniz mi?
echo Servisler: PostgreSQL, FastAPI, Django ve React.
docker compose up --build
pause
