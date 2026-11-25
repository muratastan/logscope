"""Run Locust UI, explicitly restricted to the local Django demo endpoint."""
import os,sys,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.local_env import load_local_env

def main():
    load_local_env()
    target='http://127.0.0.1:8001'
    subprocess.run([sys.executable,'-m','locust','-f',str(ROOT/'django_demo'/'loadtest'/'locustfile.py'),'--host',target,'--web-host','127.0.0.1'],cwd=ROOT,check=True)
if __name__ == '__main__': main()
