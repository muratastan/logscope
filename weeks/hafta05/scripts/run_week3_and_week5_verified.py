"""Generate Week 3/5 reproducible research metrics from supplied offline data."""
from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd
from backend.week5_verified_compare import (
    load_external_minutes, prepare_generated, evaluate, check_test_invariance, save_reports,
)


def main(argv=None):
    parser=argparse.ArgumentParser()
    parser.add_argument('--features',default='datasets/ana/logscope_ana_1200_pencere_ozellikleri.csv')
    parser.add_argument('--labels',default='datasets/ana/logscope_ana_dakika_etiketleri.csv')
    parser.add_argument('--out',default='reports/hafta5/iyilestirilmis_karsilastirma')
    args=parser.parse_args(argv)
    p=load_external_minutes(args.features,args.labels)
    if not check_test_invariance(p):
        raise RuntimeError('Test invariance check failed')
    primary,family,audit=evaluate(p,random_state=42)
    seed_rows=[];audits=[]
    for seed in (11,23,42,71,97):
        q=prepare_generated(seed)
        results,_,info=evaluate(q,random_state=seed)
        results.insert(0,'seed',seed)
        seed_rows.append(results)
        audits.append({'seed':seed,**info})
    repeats=pd.concat(seed_rows,ignore_index=True)
    keep=[i for i,n in enumerate(p.feature_names) if n!='rare_route_ratio']
    ablated=type(p)(p.X[:,keep],p.y,p.split,p.scenario,p.minute,tuple(p.feature_names[i] for i in keep),p.dataset_kind)
    ablation,_,_=evaluate(ablated)
    summary=save_reports(args.out,primary,repeats,family,audit,audits,ablation)
    print(pd.DataFrame(summary['primary']['results'])[['model','f1','recall','fpr','balanced_accuracy']].to_string(index=False))
    print('Saved to',Path(args.out).resolve())
    return summary


if __name__=='__main__':
    main()
