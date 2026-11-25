import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path
from local_env import load_local_env
ROOT=Path(__file__).resolve().parents[1]
load_local_env()
print('Python:',sys.version.split()[0])
for program in ['node','npm','docker']:
    print(program+':',shutil.which(program) or 'kurulu değil')
for module in ['django','fastapi','uvicorn','sqlalchemy','sklearn','locust','psycopg']:
    print(module+':','kurulu' if importlib.util.find_spec(module) else 'kurulu değil')
print('env:', 'var (GIT ile paylaşma)' if (ROOT/'.env').exists() else 'yok; .env.example kopyala')
