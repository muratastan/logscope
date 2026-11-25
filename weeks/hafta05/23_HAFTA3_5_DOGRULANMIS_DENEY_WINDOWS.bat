@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
  echo Python sanal ortam bulunamadi. Once 00_KURULUM_WINDOWS.bat calistirin.
  pause
  exit /b 1
)
echo Simulasyon kaynakli 3. ve 5. hafta B0, M1, B1 karsilastirmasi...
.venv\Scripts\python.exe -m scripts.run_week3_and_week5_verified
if errorlevel 1 (
  echo DENEY BASARISIZ - hata kaydini inceleyin.
  pause
  exit /b 1
)
echo RAPOR: reports\hafta5\iyilestirilmis_karsilastirma
pause
