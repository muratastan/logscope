# LogScope FastAPI runtime

Run from project root:

```
python -m pip install -r backend/requirements.txt
python -m uvicorn backend.fullstack:app --host 127.0.0.1 --port 8000
```

`fullstack.py` is the new REST implementation. `server.py` is an older demonstration server retained as reference and **should not** be started with the new React frontend.

- `backend/analysis.py`: controlled synthetic M1-M4 research experiments, chronological splitting, B0/B1/B1+D/B1+S/B2 metrics.
- `/api/ingested/analyze`: scores *uploaded* permitted JSONL minute windows with M1-M4, but without labels it does NOT compute F1.
- Model experiment results and alarms are stored. Demo traffic graphs start from explicit synthetic examples.
- Database defaults to SQLite (file). Set `LOGSCOPE_DATABASE_URL=postgresql+psycopg://...` to enable PostgreSQL.
- Operational runtime writes separate `ui_*` tables. Canonical academic 27-table schema in `db/` is NOT yet integrated into runtime ORM.
- Local demo login is `demo@logscope.local`, password `Demo2026!` unless set by environment. Do not expose publicly without production hardening.
