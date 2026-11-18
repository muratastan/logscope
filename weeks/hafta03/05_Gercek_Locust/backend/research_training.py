"""Week 6: fit/evaluate a *label-isolated* log anomaly research pipeline.

Input must be privacy-allowlisted JSONL with separate minute-label CSV.
This reads observed HTTP events (including offline *simulated* ones); it never
creates traffic, infers ground truth, or treats test labels as training inputs.
All normalization / KMeans / DBSCAN / IsolationForest / PrefixSpan fitting uses
NORMAL TRAIN minutes only; model thresholds use NORMAL VALIDATION only; held-out
TEST is never used in fitting, preprocessing, or model choice.

Joblib artifacts are Python pickles: load ONLY the artifacts you generated.
Do not call model results a production intrusion detection or attack verdict.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
import csv
import json
import math
import time

import joblib
import numpy as np
from sklearn.cluster import KMeans, DBSCAN
from sklearn.ensemble import IsolationForest
from sklearn.metrics import average_precision_score, confusion_matrix, silhouette_score
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import RobustScaler

from .analysis import prefixspan, subsequence
from .event_contract import valid_event
from .research_pg import read_manifest

FEATURES = (
    'log_request_count', 'rate_4xx', 'rate_5xx', 'log_p50_ms',
    'log_p95_ms', 'unique_sessions_per_event', 'route_diversity',
    'avg_request_interval_s', 'rare_route_ratio', 'failed_login_rate',
)
CONDITIONS = ('B0', 'B1', 'B1+D', 'B1+S', 'B2')


def _parse_time(value):
    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if dt.utcoffset() is None:
        raise ValueError('Timezone required')
    return dt.astimezone(timezone.utc)


def load_events(events_path, manifest_path=None):
    """Stream/validate events. Return per-minute observations and optional truth.

    A single manifest minute is the unit of data splitting/evaluation, not an
    individual HTTP request. Events and sessions cannot cross split boundaries.
    """
    labels = read_manifest(manifest_path) if manifest_path else None
    buckets = defaultdict(list)
    seen = set()
    rejected = 0
    missing_manifest = 0
    session_splits = defaultdict(set)
    for line in Path(events_path).open(encoding='utf-8-sig'):
        if not line.strip():
            continue
        try:
            event = valid_event(json.loads(line))
        except json.JSONDecodeError:
            event = None
        if event is None:
            rejected += 1
            continue
        if event['uid'] in seen:
            raise ValueError(f"Duplicate event UID: {event['uid']}")
        seen.add(event['uid'])
        at = _parse_time(event['occurred_at'])
        minute = at.replace(second=0, microsecond=0)
        if labels is not None and minute not in labels:
            missing_manifest += 1
            continue
        if labels is not None and event.get('session_ref'):
            label = labels[minute]
            if label['split'] != 'excluded':
                session_splits[event['session_ref']].add(label['split'])
        buckets[minute].append((at, event))
    if missing_manifest:
        raise ValueError(f'{missing_manifest} valid events do not have minute labels; aborting instead of silently discarding')
    if not buckets:
        raise ValueError('No usable log events')
    conflicts = [s for s, split in session_splits.items() if len(split) > 1]
    if conflicts:
        raise ValueError(f'{len(conflicts)} session identifiers cross train/validation/test; dataset leakage')
    if labels is not None:
        absent = set(labels) - set(buckets)
        if absent:
            raise ValueError(f'{len(absent)} manifest minutes have no HTTP events')
        for minute, row in labels.items():
            if int(row['request_count']) != len(buckets[minute]):
                raise ValueError(f'Manifest/event count mismatch at {minute}')
    return buckets, labels, {'events':len(seen)-missing_manifest, 'rejected_events':rejected,
                              'minutes':len(buckets), 'cross_split_sessions':len(conflicts)}


def _sequence(route_items):
    # Sequence truncation is deterministic; no session token is a model feature.
    return tuple(item[1] for item in sorted(route_items)[:32])


def build_windows(buckets, labels=None, common_routes=None):
    """Recompute features from the raw events, with only train-normal route priors."""
    if common_routes is None:
        if labels is None:
            raise ValueError('A fitted route reference is required for label-free inference')
        normal_routes = Counter()
        for minute, entries in buckets.items():
            if labels[minute]['split']=='train' and labels[minute]['ground_truth']=='normal':
                normal_routes.update(event['route'] for _,event in entries)
        n=sum(normal_routes.values())
        if not n:
            raise ValueError('Normal training events missing; cannot fit a novelty detector')
        common_routes={route for route,count in normal_routes.items() if count/n>=.025}
        if not common_routes:
            common_routes={normal_routes.most_common(1)[0][0]}
    common_routes=set(common_routes)
    rows=[];features=[]
    for minute in sorted(buckets):
        group=sorted(buckets[minute],key=lambda p:p[0])
        count=len(group)
        durations=np.array([event['duration_ms'] for _,event in group],dtype=float)
        statuses=[event['status'] for _,event in group]
        routes=[event['route'] for _,event in group]
        interval=[(b[0]-a[0]).total_seconds()*1000 for a,b in zip(group,group[1:])]
        sessions=defaultdict(list)
        for at, event in group:
            if event.get('session_ref'):
                sessions[event['session_ref']].append((at,event['route']))
        seq=[_sequence(route_items) for route_items in sessions.values() if len(route_items)>=2]
        failures=sum(route.startswith('/auth/login/') and 400<=status<500 for route,status in zip(routes,statuses))
        fours=sum(400<=s<500 for s in statuses)
        fives=sum(500<=s<600 for s in statuses)
        p50=float(np.median(durations));p95=float(np.percentile(durations,95))
        avg_interval=float(np.mean(interval)) if interval else 60000/count
        rare=sum(route not in common_routes for route in routes)/count
        x=(math.log1p(count),fours/count,fives/count,math.log1p(p50),math.log1p(p95),
           len(sessions)/count,len(set(routes)),avg_interval/1000,rare,failures/count)
        meta=labels.get(minute) if labels is not None else None
        rows.append({'minute':minute.isoformat().replace('+00:00','Z'),
                     'split':meta['split'] if meta else 'unlabeled',
                     'label':int(meta['ground_truth']=='anomaly') if meta and meta['split']!='excluded' else None,
                     'scenario':meta['scenario_code'] if meta else None,
                     'seed':int(meta['seed']) if meta else None,
                     'requests':count,'sequences':seq})
        features.append(x)
    return rows,np.asarray(features,dtype=float),sorted(common_routes)


def _ecdf(sorted_reference, scores):
    ref=np.asarray(sorted_reference,dtype=float)
    return np.searchsorted(ref, scores, side='right')/len(ref)


def _top_patterns(rows,train_normal_index):
    sequences=[sequence for i in train_normal_index for sequence in rows[i]['sequences']]
    patterns=prefixspan(sequences,min_support=.04,max_length=3,limit=120)
    return [p for p in patterns if len(p['sequence'])>=2][:35],len(sequences)


def _sequence_scores(rows,patterns):
    score=np.full(len(rows),np.nan,dtype=float)
    if not patterns:
        return score
    maximum=max(p['support_count'] for p in patterns)
    candidates=[(tuple(p['sequence']),p['support_count']/maximum) for p in patterns]
    for i,row in enumerate(rows):
        if not row['sequences']:
            continue
        penalties=[]
        for seq in row['sequences']:
            best=max((strength for pattern,strength in candidates if subsequence(pattern,seq)),default=0.0)
            penalties.append(1-best)
        score[i]=float(np.mean(penalties))
    return score


def fit(rows,X,random_seed=42):
    train=np.array([i for i,r in enumerate(rows) if r['split']=='train' and r['label']==0],dtype=int)
    val=np.array([i for i,r in enumerate(rows) if r['split']=='validation' and r['label']==0],dtype=int)
    test=np.array([i for i,r in enumerate(rows) if r['split']=='test'],dtype=int)
    if len(train)<15 or len(val)<8 or len(test)<8:
        raise ValueError('Need >=15 normal TRAIN, >=8 normal VALIDATION, and >=8 TEST minutes')
    if {rows[i]['label'] for i in test}!={0,1}:
        raise ValueError('Test split must contain normal and anomaly windows for F1/FPR comparison')
    scaler=RobustScaler().fit(X[train])
    z=scaler.transform(X)
    normal=z[train]
    choices=[]
    for k in range(2,min(6,len(train)-1)+1):
        model=KMeans(n_clusters=k,n_init=10,random_state=random_seed).fit(normal)
        n_clusters=len(np.unique(model.labels_))
        silhouette=(float(silhouette_score(normal,model.labels_,sample_size=min(700,len(normal)),random_state=random_seed))
                    if 1<n_clusters<len(normal) else -1.)
        choices.append((silhouette,k,model))
    _,selected_k,km=max(choices,key=lambda t:(t[0],-t[1]))
    d_k=np.min(np.linalg.norm(z[:,None,:]-km.cluster_centers_[None,:,:],axis=2),axis=1)
    d_k_ref=np.sort(d_k[train])
    k_nn=NearestNeighbors(n_neighbors=min(5,len(train))).fit(normal)
    radius=k_nn.kneighbors(normal)[0][:,-1]
    eps=max(1e-4,float(np.quantile(radius,.8)))
    db=DBSCAN(eps=eps,min_samples=min(5,len(train))).fit(normal)
    core=normal[db.core_sample_indices_]
    fallback=not len(core)
    core_nn=NearestNeighbors(n_neighbors=1).fit(core if len(core) else normal)
    d_db=core_nn.kneighbors(z)[0][:,0]
    d_db_ref=np.sort(d_db[train])
    forest=IsolationForest(n_estimators=140,random_state=random_seed,n_jobs=1,contamination='auto').fit(normal)
    d_if=-forest.score_samples(z)
    d_if_ref=np.sort(d_if[train])
    patterns,train_sequences=_top_patterns(rows,train)
    m3=_sequence_scores(rows,patterns)
    fitted={
       'version':'week6-v1','features':FEATURES,'scaler':scaler,'kmeans':km,'dbscan':db,
       'core_nn':core_nn,'forest':forest,'train_k_dist':d_k_ref,'train_db_dist':d_db_ref,
       'train_if_scores':d_if_ref,'patterns':patterns,
       'baseline_log_count_median':float(np.median(X[train,0])),
       'baseline_log_count_mad':max(.1,float(1.4826*np.median(np.abs(X[train,0]-np.median(X[train,0]))))),
       'random_seed':random_seed,'selected_k':selected_k,'dbscan_eps':eps,
       'dbscan_noise_ratio':float(np.mean(db.labels_<0)),
       'dbscan_no_core_fallback':bool(fallback),
       'train_normal_windows':len(train),'val_normal_windows':len(val),
       'train_sequence_groups':train_sequences,
    }
    signals=_compute_signals(fitted,X,rows,precalc=(d_k,d_db,d_if,m3))
    thresholds={}
    for name,score in signals['conditions'].items():
        reference=score[val]
        thresholds[name]=float(np.quantile(reference,.95,method='higher'))
    fitted['thresholds']=thresholds
    return fitted,signals


def _compute_signals(model,X,rows,precalc=None):
    if precalc is None:
        z=model['scaler'].transform(X)
        km=model['kmeans']
        kd=np.min(np.linalg.norm(z[:,None,:]-km.cluster_centers_[None,:,:],axis=2),axis=1)
        dd=model['core_nn'].kneighbors(z)[0][:,0]
        novelty=-model['forest'].score_samples(z)
        m3=_sequence_scores(rows,model['patterns'])
    else:
        kd,dd,novelty,m3=precalc
    m1=.65*_ecdf(model['train_k_dist'],kd)+.35*_ecdf(model['train_db_dist'],dd)
    m2=_ecdf(model['train_if_scores'],novelty)
    m3_available=np.isfinite(m3)
    m3_filled=np.nan_to_num(m3,nan=0.0)
    # If no usable session pattern: REMOVE M3 and renormalize existing weights.
    b1s=(.72*m2+.28*m3_filled)/np.where(m3_available,1.,.72)
    b2=(.50*m2+.30*m1+.20*m3_filled)/np.where(m3_available,1.,.80)
    baseline=np.abs(X[:,0]-model['baseline_log_count_median'])/model['baseline_log_count_mad']
    conditions={'B0':baseline,'B1':m2,'B1+D':.72*m2+.28*m1,'B1+S':b1s,'B2':b2}
    return {'m1':m1,'m2':m2,'m3':m3,'m3_available':m3_available,'conditions':conditions}


def _stats(y,pred,score):
    tn,fp,fn,tp=map(int,confusion_matrix(y,pred,labels=[0,1]).ravel())
    precision=tp/max(1,tp+fp)
    recall=tp/max(1,tp+fn)
    f1=2*precision*recall/max(1e-12,precision+recall)
    return {'precision':round(precision,4),'recall':round(recall,4),'f1':round(f1,4),
            'normal_fpr':round(fp/max(1,fp+tn),4),
            'average_precision':round(float(average_precision_score(y,score)),4),
            'tn':tn,'fp':fp,'fn':fn,'tp':tp,'alerts':int(pred.sum())}


def _bootstrap_intervals(y,pred,seed=42,iterations=250,block_size=5):
    """Exploratory moving-block bootstrap of held-out time windows (not seed CI)."""
    rng=np.random.default_rng(seed)
    n=len(y);blocks=np.arange(max(1,n-block_size+1))
    f1=[];fpr=[]
    for _ in range(iterations):
        starts=rng.choice(blocks,size=math.ceil(n/block_size),replace=True)
        indices=np.concatenate([np.arange(s,min(s+block_size,n)) for s in starts])[:n]
        yy=y[indices];pp=pred[indices]
        tp=int(np.sum((yy==1)&(pp==1)));fp=int(np.sum((yy==0)&(pp==1)))
        fn=int(np.sum((yy==1)&(pp==0)));tn=int(np.sum((yy==0)&(pp==0)))
        precision=tp/max(1,tp+fp);recall=tp/max(1,tp+fn)
        f1.append(2*precision*recall/max(1e-12,precision+recall))
        fpr.append(fp/max(1,fp+tn))
    return {'f1_95ci':[round(float(v),4) for v in np.quantile(f1,[.025,.975])],
            'normal_fpr_95ci':[round(float(v),4) for v in np.quantile(fpr,[.025,.975])]}


def evaluate(rows,signals,model):
    indices=[i for i,row in enumerate(rows) if row['split']=='test']
    y=np.array([rows[i]['label'] for i in indices],dtype=int)
    summary={};predictions=[]
    for name,score in signals['conditions'].items():
        ss=score[indices];threshold=model['thresholds'][name]
        pred=(ss>threshold).astype(int)
        stats=_stats(y,pred,ss)
        stats['threshold']=round(threshold,6)
        stats['bootstrap_exploratory']=_bootstrap_intervals(y,pred,seed=model['random_seed'])
        summary[name]=stats
    baseline=summary['B1']['f1'];hybrid=summary['B2']['f1']
    for i in indices:
        sample=rows[i]
        result={'minute_start_utc':sample['minute'], 'scenario_code':sample['scenario'],
                'ground_truth':int(sample['label']), 'requests':sample['requests'],
                'm1':round(float(signals['m1'][i]),5), 'm2':round(float(signals['m2'][i]),5),
                'm3':round(float(signals['m3'][i]),5) if signals['m3_available'][i] else None,
                'm3_available':bool(signals['m3_available'][i])}
        for name,score in signals['conditions'].items():
            result[name+'_score']=round(float(score[i]),5)
            result[name+'_alert']=int(score[i]>model['thresholds'][name])
        predictions.append(result)
    return summary,predictions,{'B2_minus_B1_F1':round(hybrid-baseline,4),
                                'B2_better_than_B1_F1':bool(hybrid>baseline),
                                'B2_meets_target_F1_080':bool(hybrid>=.80),
                                'B2_meets_target_normal_FPR_005':bool(summary['B2']['normal_fpr']<=.05)}


def scenario_breakdown(predictions):
    """Held-out performance for each predefined scenario, NEVER used to tune.

    The scenario is an external label, not a model feature. For a one-class
    subset, report detection rate (anomaly) or false alarm rate (normal), not
    an ill-defined per-scenario precision/F1.
    """
    groups=defaultdict(list)
    for row in predictions:
        groups[row['scenario_code']].append(row)
    details={}
    for scenario in sorted(groups):
        items=groups[scenario]
        truth={r['ground_truth'] for r in items}
        if len(truth)!=1:
            raise ValueError('Scenario ground truth conflict in held-out predictions')
        anomaly=next(iter(truth))==1
        models={}
        for code in CONDITIONS:
            positives=sum(int(r[code+'_alert']) for r in items)
            models[code]={
                'alerts':positives,
                'detection_rate' if anomaly else 'false_alarm_rate':round(positives/len(items),4),
            }
        details[scenario]={
            'ground_truth':'anomaly' if anomaly else 'normal',
            'test_windows':len(items),
            'm3_coverage':round(sum(int(r['m3_available']) for r in items)/len(items),4),
            'conditions':models,
        }
    return details


def write_evaluation_figures(rows,signals,model,results,output):
    """Inspect held-out anomalies and model tradeoffs without claiming success."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from sklearn.metrics import precision_recall_curve
    output=Path(output)
    names=list(CONDITIONS)
    f1=[results[name]['f1'] for name in names]
    fig,ax=plt.subplots(figsize=(9,4.3))
    ax.bar(names,f1)
    ax.axhline(.8,linestyle='--',linewidth=1.5,label='Öneri F1 hedefi (0.80)')
    ax.set_ylim(0,1);ax.set_title('Hafta 6 · JSONL / test kümesi · F1 karşılaştırması')
    ax.set_ylabel('Test F1');ax.legend();fig.tight_layout()
    fig.savefig(output/'06_ablation_f1.png',dpi=160);plt.close(fig)

    m=results['B2'];matrix=np.array([[m['tn'],m['fp']],[m['fn'],m['tp']]])
    fig,ax=plt.subplots(figsize=(6,5))
    im=ax.imshow(matrix,cmap='Greys')
    for y in range(2):
        for x in range(2):
            ax.text(x,y,str(matrix[y,x]),ha='center',va='center',fontweight='bold',
                    color='white' if matrix[y,x]>matrix.max()*.55 else 'black',fontsize=15)
    ax.set_xticks([0,1],['Normal','Anomali'])
    ax.set_yticks([0,1],['Normal','Anomali'])
    ax.set_xlabel('B2 tahmin');ax.set_ylabel('Gerçek etiket (kontrollü senaryo)')
    ax.set_title('B2 · Sadece tutulan test pencereleri')
    fig.colorbar(im,ax=ax,shrink=.8);fig.tight_layout()
    fig.savefig(output/'07_B2_karisiklik_matrisi.png',dpi=160);plt.close(fig)

    test=[i for i,row in enumerate(rows) if row['split']=='test']
    y=np.array([rows[i]['label'] for i in test],dtype=int)
    fig,ax=plt.subplots(figsize=(8,5))
    for name in names:
        precision,recall,_=precision_recall_curve(y,signals['conditions'][name][test])
        ax.step(recall,precision,where='post',label=f'{name} · AP={results[name]["average_precision"]:.3f}')
    ax.set_xlim(0,1);ax.set_ylim(0,1.02)
    ax.set_xlabel('Recall');ax.set_ylabel('Precision')
    ax.set_title('Etiketli test pencereleri · Precision / Recall eğrisi')
    ax.legend(loc='lower left');fig.tight_layout()
    fig.savefig(output/'08_test_precision_recall.png',dpi=160);plt.close(fig)
    return ['06_ablation_f1.png','07_B2_karisiklik_matrisi.png','08_test_precision_recall.png']

def train_and_report(events_path,manifest_path,report_dir,model_dir=None,seed=42):
    started=time.perf_counter()
    buckets,labels,audit=load_events(events_path,manifest_path)
    rows,X,common=build_windows(buckets,labels)
    model,signals=fit(rows,X,random_seed=seed)
    model['common_routes']=common
    metrics,predictions,comparison=evaluate(rows,signals,model)
    path=Path(report_dir);path.mkdir(parents=True,exist_ok=True)
    figures=write_evaluation_figures(rows,signals,model,metrics,path)
    split_counts=dict(Counter(row['split'] for row in rows))
    by_scenario=dict(Counter(row['scenario'] for row in rows if row['split']!='excluded'))
    origin='offline_statistical_simulation' if 'offline' in str(events_path).lower() else 'external_jsonl_origin_not_independently_proven'
    report={
      'dataset_origin':origin,
      'file_names':{'jsonl':Path(events_path).name,'manifest':Path(manifest_path).name},
      'data':{**audit,'split_minutes':split_counts,'scenarios':by_scenario,
              'normal_train_windows':model['train_normal_windows'],
              'normal_validation_windows':model['val_normal_windows'],
              'm3_coverage_test':round(float(np.mean([signals['m3_available'][i] for i,r in enumerate(rows) if r['split']=='test'])),4)},
      'feature_names':FEATURES,'figures':figures,
      'models':{'M1':'RobustScaler + train-only KMeans/DBSCAN core distance',
                'M2':'IsolationForest fitted to NORMAL train windows only',
                'M3':'PrefixSpan frequent sessions from NORMAL train windows only',
                'M4':'B0/B1/B1+D/B1+S/B2; validation-normal 95% thresholds',
                'kmeans_selected_k':model['selected_k'],
                'dbscan_eps':round(model['dbscan_eps'],5),
                'dbscan_noise_fraction_train':round(model['dbscan_noise_ratio'],4),
                'dbscan_no_core_fallback':model['dbscan_no_core_fallback'],
                'train_session_sequences':model['train_sequence_groups'],
                'frequent_patterns_found':len(model['patterns'])},
      'results_test_only':metrics,'scenario_breakdown_test_only':scenario_breakdown(predictions),'comparison':comparison,
      'protocol':'Splits from external minute manifest; train normal only; fit+scaler+route priors+PrefixSpan never see validation or test; thresholds only normal validation; fixed held-out test evaluation. Missing M3 is excluded and weights rescaled.',
      'limitations':['Synthetic scenarios are not evidence of attack detection on real users.',
                     'False positive rate / F1 targets are evaluated, not guaranteed.',
                     'Moving-block CIs measure exploratory within-test uncertainty, not uncertainty across independent datasets.',
                     'Single offline seed is NOT the required five Locust seeds; real HTTP matrix still needs execution.',
                     'Session identifiers are used only to form within-minute route sequences, never as numeric model features.',
                     'The 10 feature set does not explicitly encode hour-of-day; scheduling artefacts need independent testing.'],
      'elapsed_seconds':round(time.perf_counter()-started,2)
    }
    (path/'model_comparison.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    with (path/'heldout_predictions.csv').open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(predictions[0]),extrasaction='ignore');writer.writeheader();writer.writerows(predictions)
    if model_dir:
        model_path=Path(model_dir);model_path.mkdir(parents=True,exist_ok=True)
        # Model object contains no raw data, labels, user/session identifiers or file paths.
        joblib.dump(model,model_path/'research_week6.joblib',compress=3)
    return report


def predict_unlabeled(events_path,model_path,out_path):
    """Week 7 preview: inference using a FROZEN fitted model and thresholds."""
    model=joblib.load(model_path)  # never load an untrusted or downloaded joblib file
    if model.get('version')!='week6-v1':
        raise ValueError('Unsupported model artifact version')
    buckets,labels,audit=load_events(events_path)
    rows,X,_=build_windows(buckets,common_routes=model['common_routes'])
    signals=_compute_signals(model,X,rows)
    results=[]
    for i,row in enumerate(rows):
        signals_row={'minute_start_utc':row['minute'],'requests':row['requests'],
                     'm1':round(float(signals['m1'][i]),5),'m2':round(float(signals['m2'][i]),5),
                     'm3':round(float(signals['m3'][i]),5) if signals['m3_available'][i] else None,
                     'm3_available':bool(signals['m3_available'][i])}
        for name,series in signals['conditions'].items():
            signals_row[name+'_score']=round(float(series[i]),5)
            signals_row[name+'_alert']=int(series[i]>model['thresholds'][name])
        results.append(signals_row)
    expected_volume=math.expm1(model['baseline_log_count_median'])
    observed_volume=float(np.median([row['requests'] for row in rows]))
    volume_ratio=observed_volume/max(1.0,expected_volume)
    distribution_shift=not 0.5<=volume_ratio<=2.0
    all_alert_fraction=float(np.mean([r['B2_alert'] for r in results]))
    for result in results:
        result['volume_distribution_shift']=bool(distribution_shift)
    out=Path(out_path);out.parent.mkdir(parents=True,exist_ok=True)
    with out.open('w',encoding='utf-8',newline='') as file:
        writer=csv.DictWriter(file,fieldnames=list(results[0]));writer.writeheader();writer.writerows(results)
    return {'input_events':audit['events'],'minutes_scored':len(results),
            'B2_alerts':sum(r['B2_alert'] for r in results),'output':str(out),
            'training_median_requests_per_minute':round(expected_volume,2),
            'new_data_median_requests_per_minute':round(observed_volume,2),
            'relative_traffic_volume':round(volume_ratio,3),
            'distribution_shift_warning':bool(distribution_shift or all_alert_fraction>.75),
            'note':('WARNING: the incoming data differs materially from training or almost all minutes are flagged; '
                    'check traffic volume, routes and logging rules before interpreting alerts. '
                    'Do NOT treat these as independently verified attacks.' if distribution_shift or all_alert_fraction>.75
                    else 'Predictions are exploratory, not verified attacks or ground truth.')}


def score_persisted_events(records, trusted_model_file, model_origin='unverified_artifact'):
    """Run genuinely FROZEN M1-M4 scoring on SQLAlchemy ui_events rows.

    There is deliberately NO training, label or scenario input in this path.
    This is an analyst-aid signal only, not a confirmed hostile event.
    `trusted_model_file` must be selected server-side, never by a web client.
    """
    model=joblib.load(trusted_model_file)  # local trusted file ONLY
    if model.get('version')!='week6-v1':
        raise ValueError('Unexpected research model version')
    buckets=defaultdict(list)
    from collections import Counter
    for rec in records:
        at=_parse_time(rec['occurred_at'])
        safe_event={'uid':rec['uid'],'occurred_at':rec['occurred_at'],
                    'method':rec['method'],'route':rec['route'],
                    'status':int(rec['status']),'duration_ms':float(rec['duration_ms']),
                    'session_ref':rec.get('session_ref')}
        buckets[at.replace(second=0,microsecond=0)].append((at,safe_event))
    if not buckets:
        raise ValueError('Veritabanında puanlanacak anonim HTTP kaydı yok')
    rows,X,_=build_windows(buckets,common_routes=model['common_routes'])
    signals=_compute_signals(model,X,rows)
    shift_ratio=float(np.median([r['requests'] for r in rows]))/max(1.0,math.expm1(model['baseline_log_count_median']))
    shift=bool(not .5<=shift_ratio<=2.)
    per_window=[];alarms=[]
    for i,row in enumerate(rows):
        signal={name:round(float(score[i]),5) for name,score in signals['conditions'].items()}
        alert=signal['B2']>model['thresholds']['B2']
        preview=Counter(item['route'] for _,item in buckets[_parse_time(row['minute'])]).most_common(1)[0][0]
        item={'minute_start_utc':row['minute'],'requests':row['requests'],
              'representative_route':preview,'b2_score':signal['B2'],
              'b2_threshold':round(float(model['thresholds']['B2']),5),
              'm1':round(float(signals['m1'][i]),5),'m2':round(float(signals['m2'][i]),5),
              'm3':round(float(signals['m3'][i]),5) if signals['m3_available'][i] else None,
              'm3_available':bool(signals['m3_available'][i]),
              'is_anomaly_signal':bool(alert)}
        per_window.append(item)
        if alert:
            reasons=[]
            if item['m2']>=.9:reasons.append('Isolation Forest puanı yüksek')
            if item['m1']>=.9:reasons.append('Küme/yoğunluk profilinden uzak')
            if item['m3'] is not None and item['m3']>=.65:reasons.append('Oturum geçiş örüntüsü nadir')
            if not reasons:reasons.append('Birleşik B2 puanı doğrulama eşiğini aştı')
            item['reason']='; '.join(reasons)
            alarms.append(item)
    fraction=sum(item['is_anomaly_signal'] for item in per_window)/len(per_window)
    caution=bool(shift or fraction>.75)
    return {'mode':'frozen_model_unlabeled_inference','model_origin':model_origin,
            'input_provenance':'unverified_uploaded_jsonl',
            'data':{'events':len(records),'minutes':len(rows),'split':'none; frozen training, no refit',
                    'traffic_volume_ratio_vs_training':round(shift_ratio,3)},
            'total_alerts':len(alarms),
            'alarms':sorted(alarms,key=lambda row:row['b2_score'],reverse=True)[:100],
            'windows_scored':len(per_window),
            'shift_warning':caution,
            'note':('Distribution shift or unusually high alert volume detected. These alerts are UNVERIFIED and model retraining needs separate labeled data.' if caution
                    else 'Unverified research signals; this is NOT a confirmed attack diagnosis.'),
            'model_artifact_version':model['version']}
