@echo off
cd /d "%~dp0"
py -3 -m venv .venv
if errorlevel 1 (echo Python 3 gerekli. & pause & exit /b 1)
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
if not exist .env (copy .env.example .env)
echo.
echo .env dosyasindaki parolalari degistiriniz.
echo VS Code ile logscope.code-workspace dosyasini aciniz.
pause
