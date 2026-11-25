@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (echo Once 00_KURULUM_WINDOWS.bat calistirin. & pause & exit /b 1)
.venv\Scripts\python.exe scripts\run_locust.py
pause
