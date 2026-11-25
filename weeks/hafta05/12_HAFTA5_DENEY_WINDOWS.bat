@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (echo Once kurulum yapin. & pause & exit /b 1)
echo Bu komut HTTP degil, cevrim disi sentetik 5 seed uzerinde model karsilastirmasi yapar.
.venv\Scripts\python.exe -m scripts.week3_5_report
pause
