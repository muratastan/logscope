"""Read local developer .env before importing services; avoid committing secrets."""
from pathlib import Path
import os
from urllib.parse import quote
ROOT = Path(__file__).resolve().parents[1]

def load_local_env():
    path = ROOT / '.env'
    if path.exists():
        for line in path.read_text(encoding='utf-8-sig').splitlines():
            line=line.strip()
            if not line or line.startswith('#') or '=' not in line: continue
            key,val=line.split('=',1)
            key=key.strip()
            val=val.strip().strip('"').strip("'")
            if key.isidentifier(): os.environ.setdefault(key,val)
    return path.exists()

def ensure_database_env():
    if os.getenv('LOGSCOPE_USE_POSTGRES','0')=='1' and 'LOGSCOPE_DATABASE_URL' not in os.environ:
        pwd=os.getenv('LOGSCOPE_DB_PASSWORD','')
        if not pwd or pwd.startswith('change_this_'):
            raise RuntimeError('.env içindeki LOGSCOPE_DB_PASSWORD değerini değiştirin')
        os.environ['LOGSCOPE_DATABASE_URL'] = 'postgresql+psycopg://logscope_dev:'+quote(pwd,safe='')+'@127.0.0.1:5432/logscope'
