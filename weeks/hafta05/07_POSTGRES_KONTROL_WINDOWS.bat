@echo off
cd /d "%~dp0"
docker compose exec postgres psql -U logscope_dev -d logscope -c "SELECT count(*) AS table_count FROM information_schema.tables WHERE table_schema='logscope' AND table_type='BASE TABLE';"
pause
