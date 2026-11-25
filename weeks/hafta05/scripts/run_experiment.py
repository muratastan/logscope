"""Run controlled LogScope eight-scenario experiment and save inspectable JSON.
This synthesizes minute-level features, not actual HTTP packets.
"""
import sys
import json
from pathlib import Path
root=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(root))
from backend.analysis import run_experiment
result=run_experiment(1200,100,42)
output=root/'tests'/'LAST_EXPERIMENT_RESULT.json'
output.write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
print('Dataset:',result['data'])
for code,metric in result['conditions'].items():
    print(f'{code:5s}  F1={metric["f1"]:.4f}  Normal_FPR={metric["normal_fpr"]:.4f}  PR-AUC={metric["pr_auc"]:.4f}')
print('Output:',output)
