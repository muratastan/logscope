"""Restore the full 146435-record *offline simulation* dataset, without network access."""
from pathlib import Path
import gzip
import hashlib
import shutil
import sys

ROOT=Path(__file__).resolve().parents[1]
TARGET=ROOT/'02_OFFLINE_Veri'/'logscope_ana_5tohum_OFFLINE_SIMULASYON.jsonl'
SOURCE=TARGET.with_suffix('.jsonl.gz')
EXPECTED_SHA256='f3bde1f0893c8fe81ef586c7455bc4919a4ea5389724ea0515ccaead45ee46e2'

def main():
    if not SOURCE.is_file():
        print('Missing compressed offline dataset:',SOURCE,file=sys.stderr);return 2
    if TARGET.is_file() and hashlib.sha256(TARGET.read_bytes()).hexdigest()==EXPECTED_SHA256:
        print('Already restored and hash verified:',TARGET);return 0
    with gzip.open(SOURCE,'rb') as inp,TARGET.open('wb') as out:shutil.copyfileobj(inp,out)
    observed=hashlib.sha256(TARGET.read_bytes()).hexdigest()
    if observed!=EXPECTED_SHA256:
        TARGET.unlink(missing_ok=True)
        print('SHA256 mismatch after decompression',file=sys.stderr);return 3
    print('Restored offline simulated JSONL:',TARGET,'SHA256:',observed)
    return 0

if __name__=='__main__':raise SystemExit(main())
