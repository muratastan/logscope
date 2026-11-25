"""Start controlled Django traffic generator; never bind test endpoints to public hosts."""
import os,sys,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.local_env import load_local_env

def main():
    load_local_env()
    os.environ.setdefault('LOGSCOPE_JSONL_PATH',str(ROOT/'django_demo'/'generated_access.jsonl'))
    django=ROOT/'django_demo'
    subprocess.run([sys.executable,str(django/'manage.py'),'migrate','--noinput'],cwd=django,check=True)
    subprocess.run([sys.executable,str(django/'manage.py'),'runserver','127.0.0.1:8001','--noreload'],cwd=django,check=True)
if __name__ == '__main__': main()
