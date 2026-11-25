"""Local-only canonical PostgreSQL import from labeled JSONL + CSV manifest.
Never exposes labels to model training features.
"""
import argparse
import json
import os
from backend.research_pg import import_postgres,preview_import

if __name__=='__main__':
    from scripts.local_env import load_local_env, ensure_database_env
    load_local_env();ensure_database_env()
    p=argparse.ArgumentParser()
    p.add_argument('--jsonl',required=True)
    p.add_argument('--manifest',required=True)
    p.add_argument('--workspace-id',type=int)
    p.add_argument('--dry-run',action='store_true')
    a=p.parse_args()
    if a.dry_run:
        summary,_,_,_=preview_import(a.jsonl,a.manifest)
    else:
        try:import psycopg
        except ImportError:raise SystemExit('psycopg yok. Kurulum: pip install "psycopg[binary]>=3.1,<4"')
        url=os.getenv('LOGSCOPE_DATABASE_URL','')
        if not url.startswith('postgresql'):raise SystemExit('LOGSCOPE_DATABASE_URL PostgreSQL olmalı')
        url=url.replace('postgresql+psycopg://','postgresql://')
        with psycopg.connect(url) as connection:
            summary=import_postgres(connection,a.jsonl,a.manifest,a.workspace_id)
    print(json.dumps(summary,ensure_ascii=False,indent=2))
