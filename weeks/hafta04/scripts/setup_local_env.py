"""Generate a local-only .env without storing passwords in a shared archive."""
from pathlib import Path
import argparse
import os
import secrets

ROOT = Path(__file__).resolve().parents[1]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--force', action='store_true', help='Overwrite .env only when explicitly requested')
    args = ap.parse_args()
    path = ROOT / '.env'
    if path.exists() and not args.force:
        print(f'Keeping existing {path}. No credentials changed.')
        return 0
    content = '\n'.join([
        '# LogScope local classroom / research development only',
        'LOGSCOPE_DB_PASSWORD=' + secrets.token_urlsafe(24),
        'LOGSCOPE_DEMO_PASSWORD=' + secrets.token_urlsafe(24),
        'LOGSCOPE_DJANGO_SECRET=' + secrets.token_urlsafe(40),
        'LOGSCOPE_DEMO_MODE=1',
        'LOGSCOPE_HTTPS=0',
        'LOGSCOPE_USE_POSTGRES=1',
        'LOGSCOPE_ENABLE_ANOMALY_ENDPOINTS=1',
        'LOGSCOPE_ALLOWED_ORIGINS=http://127.0.0.1:5173,http://localhost:5173,http://127.0.0.1:8000,http://localhost:8000',
        '',
    ])
    path.write_text(content, encoding='utf-8')
    try: os.chmod(path, 0o600)
    except OSError: pass
    print('Created local .env for localhost Django and PostgreSQL.')
    print('Read LOGSCOPE_DEMO_PASSWORD from .env when logging into the local FastAPI demo.')
    print('IMPORTANT: .env is ignored by git; never upload it or paste the secrets into chat.')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
