@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (echo Once kurulum yapin. & pause & exit /b 1)
.venv\Scripts\python.exe -m scripts.prepare_locust_dataset --manifest reports\hafta3\live_locust\locust_runs_manifest.csv --out reports\hafta3\live_locust_prepared
if errorlevel 1 (echo Gercek HTTP matrisi eksik. & pause & exit /b 1)
.venv\Scripts\python.exe -m scripts.verify_week3_acceptance --manifest reports\hafta3\live_locust_prepared\scenario_manifest.csv
pause
