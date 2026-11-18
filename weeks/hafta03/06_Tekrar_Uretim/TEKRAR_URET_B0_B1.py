"""Week 3 source-backed reproducibility helper; no new HTTP tests claimed."""
from pathlib import Path
import sys, json
base=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(base/'05_Gercek_Locust'))
from backend.research_training import train_and_report
out=base/'06_Tekrar_Uretim'/'yeniden_hesaplanan'
model=base/'06_Tekrar_Uretim'/'gecici_modeller'
rep=train_and_report(str(base/'02_OFFLINE_Veri'/'logscope_ana_5tohum_OFFLINE_SIMULASYON.jsonl'),str(base/'02_OFFLINE_Veri'/'logscope_ana_dakika_etiketleri.csv'),str(out),str(model),seed=42)
summary={'origin':'OFFLINE_SIMULATION_NOT_REAL_HTTP','test_only':{m:rep['results_test_only'][m] for m in ('B0','B1')}}
(out/'B0_B1_ozet_yeniden.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(summary,ensure_ascii=False,indent=2))
