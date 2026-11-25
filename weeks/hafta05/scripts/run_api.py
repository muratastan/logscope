"""Run the existing FastAPI research prototype locally on 127.0.0.1:8000."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.local_env import load_local_env,ensure_database_env

def main():
    load_local_env();ensure_database_env()
    import uvicorn
    uvicorn.run('backend.fullstack:app',host='127.0.0.1',port=8000,reload=False,log_level='info')
if __name__ == '__main__': main()
