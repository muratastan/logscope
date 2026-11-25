@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
 echo Once 00_KURULUM_WINDOWS.bat calistirin.
 pause
 exit /b 1
)
.venv\Scripts\python.exe -m pytest -q tests\test_week5_verified.py tests\test_fullstack.py
if errorlevel 1 (pause & exit /b 1)
cd frontend
node scripts\check-routes.mjs
if errorlevel 1 (pause & exit /b 1)
node scripts\check-jsx.mjs
if errorlevel 1 (pause & exit /b 1)
echo Frontend uretim derlemesi: npm install ve npm run build ayri dogrulanmalidir.
pause
