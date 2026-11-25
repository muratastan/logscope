"""Week 3/5 repeatable experiment and EDA report generator.
Five SEED-based aggregate simulations, bootstrap CIs across seeds. Not Locust.
"""
from __future__ import annotations
import csv
import json
from pathlib import Path
from collections import Counter
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from backend.week5_cluster_compare import compare
from backend.analysis import synthetic_windows

SEEDS=[11,23,42,71,97]

def run(outdir='reports/hafta3',detail_dir='reports/hafta5'):
    p=Path(outdir);p.mkdir(parents=True,exist_ok=True)
    q=Path(detail_dir);q.mkdir(parents=True,exist_ok=True)
    rows=[];details=[]
    for seed in SEEDS:
        res=compare(seed=seed)
        details.append(res)
        for k,v in res['results'].items(): rows.append({'seed':seed,'model':k,**v})
    with (q/'model_comparison_by_seed.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    (q/'cluster_fit_diagnostics.json').write_text(json.dumps(details,ensure_ascii=False,indent=2),encoding='utf-8')
    rng=np.random.default_rng(2026)
    summary={}
    for model in details[0]['results']:
        metrics=[d['results'][model]['f1'] for d in details]
        fprs=[d['results'][model]['normal_fpr'] for d in details]
        draws=rng.choice(metrics,size=(4000,len(metrics)),replace=True).mean(axis=1)
        summary[model]={'f1_mean':round(float(np.mean(metrics)),4),'f1_bootstrap_95_ci_seed_level':[round(float(v),4) for v in np.quantile(draws,[.025,.975])],
                        'fpr_mean':round(float(np.mean(fprs)),4),'seeds':SEEDS}
    result={'source':'offline synthetic aggregate simulation, NOT Django/Locust HTTP data',
            'model_results':summary,'iterations':5,'seeds':SEEDS,'windows_per_seed':1200,
            'temporal_split':'60/20/20 ordered within each seed; train/validation/test held separate',
            'caveat':'CI resamples five independent seed runs, not a patient/population confidence interval. Not a test of live service performance.'}
    (p/'baseline_summary_5seeds.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    # EDA on one representative statistical simulation (seed 42)
    ws=synthetic_windows(1200,102,42)
    values=np.array([w.request_count for w in ws]);fives=np.array([w.count_5xx for w in ws]);fours=np.array([w.count_4xx for w in ws]);
    plt.figure(figsize=(12,3.8));plt.plot(np.arange(len(values)),values,lw=1.2,label='HTTP istegi / dakika');plt.axvline(720,linestyle='--',alpha=.7);plt.axvline(960,linestyle='--',alpha=.7);plt.xlabel('Kronolojik dakika');plt.ylabel('Istek sayisi');plt.title('Simule trafik ve kronolojik egitim / dogrulama / test');plt.tight_layout();plt.savefig(p/'01_trafik_zaman_serisi.png',dpi=170);plt.close()
    groups=Counter(w.scenario for w in ws); names=list(groups); counts=[groups[k] for k in names]
    plt.figure(figsize=(10.6,4.2));plt.barh(names,counts);plt.xlabel('1 dakikalik pencere sayisi');plt.title('Sekiz sentetik senaryonun dagilimi');plt.tight_layout();plt.savefig(p/'02_senaryo_dagilimi.png',dpi=170);plt.close()
    plt.figure(figsize=(7.5,4));plt.hist(values,bins=35);plt.xlabel('Istek/dakika');plt.ylabel('Pencere');plt.title('Istek hacmi dagilimi');plt.tight_layout();plt.savefig(p/'03_istek_hacmi_histogram.png',dpi=170);plt.close()
    v=[summary[m]['f1_mean'] for m in summary];names=list(summary)
    plt.figure(figsize=(9,4.2));plt.bar(names,v);plt.ylim(0,1);plt.ylabel('F1 skoru');plt.title('5 sentetik tekrarin ortalama test F1 karsilastirmasi');plt.xticks(rotation=30,ha='right');plt.tight_layout();plt.savefig(q/'04_yontem_karsilastirma_f1.png',dpi=170);plt.close()
    print(json.dumps(result,ensure_ascii=False,indent=2));return result

if __name__=='__main__':run()
