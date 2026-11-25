"""Idempotent, checksum-checked schema initialization for PostgreSQL 15+."""
from pathlib import Path
import hashlib
import os

MIGRATIONS=['01_research_core.sql','02_product_extensions.sql','03_demo_plan_seed.sql']

def apply(connection,root=None):
    root=Path(root or Path(__file__).resolve().parents[1] / 'db')
    with connection.cursor() as cur:
        cur.execute('CREATE SCHEMA IF NOT EXISTS logscope')
        cur.execute('''CREATE TABLE IF NOT EXISTS public.logscope_schema_migrations(
            filename text PRIMARY KEY, sha256 char(64) NOT NULL, applied_at timestamptz NOT NULL DEFAULT now())''')
    connection.commit()
    applied=[]
    for filename in MIGRATIONS:
        source=(root/filename).read_text(encoding='utf-8')
        checksum=hashlib.sha256(source.encode()).hexdigest()
        with connection.cursor() as cur:
            cur.execute('SELECT sha256 FROM public.logscope_schema_migrations WHERE filename=%s',(filename,))
            found=cur.fetchone()
            if found:
                if found[0]!=checksum:raise ValueError(f'Migration drift: {filename}; do not silently overwrite applied migrations')
                applied.append((filename,'already-applied'))
                continue
        # These legacy files contain BEGIN/COMMIT; execute them outside psycopg's own transaction.
        # Explicitly fail on any SQL error, recording checksums only after success.
        connection.commit()
        connection.autocommit=True
        try:
            with connection.cursor() as cur:
                cur.execute(source,prepare=False)
                cur.execute('INSERT INTO public.logscope_schema_migrations(filename,sha256) VALUES(%s,%s)',(filename,checksum))
            applied.append((filename,'applied'))
        finally:connection.autocommit=False
    connection.commit()
    return applied

if __name__=='__main__':
    from scripts.local_env import load_local_env, ensure_database_env
    load_local_env();ensure_database_env()
    try:import psycopg
    except ImportError:raise SystemExit('psycopg missing: pip install "psycopg[binary]>=3.1,<4"')
    conn_url=os.environ.get('LOGSCOPE_DATABASE_URL','').replace('postgresql+psycopg://','postgresql://')
    if not conn_url.startswith('postgresql://'):raise SystemExit('Set PostgreSQL LOGSCOPE_DATABASE_URL')
    with psycopg.connect(conn_url) as conn:
        for fn,status in apply(conn):print(f'{fn}: {status}')
