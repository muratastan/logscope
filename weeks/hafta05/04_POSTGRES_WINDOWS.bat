@echo off
cd /d "%~dp0"
if not exist .env (copy .env.example .env & echo .env parolalarini degistirin & pause & exit /b 1)
docker compose up -d postgres
pause
