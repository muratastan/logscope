@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (echo Once kurulum yapin. & pause & exit /b 1)
echo UYARI: Bu islem sadece yerel Django 127.0.0.1:8001 icindir.
echo 8 senaryo x 5 seed x 34 dk = yaklasik 22 saat 40 dk kontrollu test.
echo LOGSCOPE_ENABLE_ANOMALY_ENDPOINTS=1 olmalidir.
echo Tamamlama kesilirse tekrar baslatilabilir. 
set /p ANSWER=Devam icin EVET yazin: 
if /I not "%ANSWER%"=="EVET" (echo Iptal edildi. & pause & exit /b 1)
.venv\Scripts\python.exe -m scripts.run_locust_matrix --minutes-per-case 34 --users 20
pause
