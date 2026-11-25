@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (echo Once 00_KURULUM_WINDOWS.bat calistirin. & pause & exit /b 1)
.venv\Scripts\python.exe -m pytest -q tests
if errorlevel 1 (echo Python testleri basarisiz. & pause & exit /b 1)
.venv\Scripts\python.exe -m scripts.week2_5_audit
if errorlevel 1 (echo Dosya kontrolu basarisiz. & pause & exit /b 1)
pushd frontend
call npm run check:jsx
if errorlevel 1 (popd & pause & exit /b 1)
call npm run check:routes
popd
echo Tam otomatik derleme icin: cd frontend ^&^& npm install ^&^& npm run build
pause
