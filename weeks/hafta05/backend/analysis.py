"""Reproducible LogScope M1-M4 synthetic experiment.

M1: K-Means centroid distance and DBSCAN core-neighbour novelty.
M2: Isolation Forest trained only on normal TRAIN windows.
M3: PrefixSpan frequent session patterns, learned only on TRAIN windows.
M4: fixed-weight transparent combination calibrated on VALIDATION normal data.
No label, split, scenario name, or synthetic seed enters a feature vector.

This is a research demonstrator, not a certified attack detector.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from collections import Counter
import math
import time
import random
from typing import Iterator

import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans, DBSCAN
from sklearn.neighbors import NearestNeighbors
from sklearn.ensemble import IsolationForest
from sklearn.metrics import precision_recall_fscore_support, average_precision_score

SCENARIOS = [
    'normal_steady', 'normal_hourly_rise', 'normal_campaign', 'normal_route_mix',
    'anomaly_5xx', 'anomaly_latency', 'anomaly_login_fail', 'anomaly_rare_route'
]
ROUTES = ['/','/catalog/','/search/','/items/{id}/','/forms/checkout/','/auth/login/','/admin/export/']
NORMAL_SEQUENCES = [('/','/catalog/','/items/{id}/'),('/','/search/','/items/{id}/'),('/auth/login/','/catalog/','/items/{id}/'),('/','/catalog/','/forms/checkout/')]

@dataclass
class Window:
    index:int
    scenario:str
    label:int
    request_count:int
    count_4xx:int
    count_5xx:int
    p50_ms:float
    p95_ms:float
    distinct_sessions:int
    route_diversity:int
    avg_interval_ms:float
    rare_route_ratio:float
    login_failure_ratio:float
    sequences:list[tuple[str,...]]

    def feature_vector(self):
        n=max(self.request_count,1)
        return [math.log1p(self.request_count),self.count_4xx/n,self.count_5xx/n,
                math.log1p(self.p50_ms),math.log1p(self.p95_ms),
                self.distinct_sessions/n,self.route_diversity,self.avg_interval_ms/1000,
                self.rare_route_ratio,self.login_failure_ratio]


def synthetic_windows(n_windows=1200, requests_per_window=100, seed=42)->list[Window]:
    """Create 8 clearly labelled traffic patterns; 60/20/20 *chronological* blocks.
    Each window uses fresh synthetic sessions; no session identity crosses a split.
    The function describes simulated events statistically. It does not claim that
    Django/Locust generated real HTTP requests.
    """
    if n_windows < 120 or requests_per_window < 10:
        raise ValueError('Use at least 120 windows and 10 requests per window')
    rng=random.Random(seed)
    rows=[]
    # All eight conditions occur in all splits, while each session is unique to a window.
    for i in range(n_windows):
        # deterministic interleaving, not used as model feature
        scenario=SCENARIOS[(i*5+(i//8)) % len(SCENARIOS)]
        # The simple permutation above covers each class in every long time interval.
        label=int(scenario.startswith('anomaly'))
        noise=lambda scale: rng.uniform(-scale,scale)
        count=max(10,requests_per_window+int(noise(18)))
        if scenario=='normal_campaign':count=int(count*1.85)
        elif scenario=='normal_hourly_rise':count=int(count*(1.0 + .45*(1+math.sin(i/45))/2))
        elif scenario=='anomaly_5xx':count=int(count*1.15)
        elif scenario=='anomaly_login_fail':count=int(count*1.10)
        if scenario=='anomaly_5xx':five=int(count*rng.uniform(.18,.41))
        else:five=int(count*rng.uniform(0,.027))
        four=int(count*rng.uniform(0.01,.065))
        if scenario=='anomaly_login_fail':four=int(count*rng.uniform(.3,.55))
        p50=rng.uniform(70,150)
        p95=p50*rng.uniform(1.3,2.2)
        if scenario=='anomaly_latency':p95+=rng.uniform(600,1150);p50+=rng.uniform(200,320)
        rare=rng.uniform(0,.02) if scenario!='anomaly_rare_route' else rng.uniform(.48,.83)
        login_fail=.0 if scenario!='anomaly_login_fail' else four/count
        route_div=4+(1 if scenario=='normal_route_mix' else 0)+(2 if scenario=='anomaly_rare_route' else 0)
        sessions=max(3,int(count/rng.uniform(9,20)))
        sequences=[]
        for j in range(sessions):
            if scenario=='anomaly_rare_route' and j%3!=0:
                seq=('/','/admin/export/','/auth/login/')
            elif scenario=='anomaly_login_fail' and j%3!=0:
                seq=('/auth/login/','/auth/login/','/auth/login/')
            else:
                seq=rng.choice(NORMAL_SEQUENCES)
            sequences.append(seq)
        rows.append(Window(i,scenario,label,count,four,five,round(p50,2),round(p95,2),sessions,route_div,
                           round(60000/count,2),round(rare,3),round(login_fail,3),sequences))
    return rows


def subsequence(pattern:tuple[str,...], seq:tuple[str,...])->bool:
    it=iter(seq)
    return all(any(x==wanted for x in it) for wanted in pattern)


def prefixspan(sequences:list[tuple[str,...]],min_support=0.035,max_length=3,limit=150):
    """PrefixSpan: projected DB pattern-growth with sequence-level support.
    A sequence counts at most once per frequent pattern. This is a small reference
    implementation for classroom-sized data, not an optimized big-data miner.
    """
    if not sequences:return []
    threshold=max(2,math.ceil(len(sequences)*min_support))
    # project each session to the suffix after first matching element
    projected=[(seq,0) for seq in sequences]
    results=[]
    def grow(pattern,db):
        if len(pattern)>=max_length or len(results)>=limit:return
        counts=Counter()
        for seq,start in db:
            counts.update(set(seq[start:]))
        for symbol,count in sorted(counts.items(),key=lambda z:(-z[1],z[0])):
            if count<threshold or len(results)>=limit:continue
            nxt=pattern+(symbol,)
            results.append({'sequence':list(nxt),'support_count':count,'relative_support':round(count/len(sequences),4)})
            child=[]
            for seq,start in db:
                try:
                    idx=seq.index(symbol,start)
                except ValueError:
                    continue
                child.append((seq,idx+1))
            grow(nxt,child)
    grow(tuple(),projected)
    return sorted(results,key=lambda r:(-r['support_count'],-len(r['sequence']),r['sequence']))


def _ecdf(reference,values):
    ref=np.sort(np.asarray(reference,dtype=float))
    return np.searchsorted(ref,np.asarray(values),side='right')/max(1,len(ref))

def _metrics(y,pred,scores):
    precision,recall,f1,_=precision_recall_fscore_support(y,pred,average='binary',zero_division=0)
    neg=(np.asarray(y)==0)
    fpr=float(np.mean(np.asarray(pred)[neg])) if neg.any() else 0.0
    result={'precision':round(float(precision),4),'recall':round(float(recall),4),'f1':round(float(f1),4),'normal_fpr':round(fpr,4),
            'alarms':int(np.sum(pred)),'test_windows':len(y)}
    try: result['pr_auc']=round(float(average_precision_score(y,scores)),4)
    except ValueError: result['pr_auc']=None
    return result


def run_experiment(n_windows=1200, requests_per_window=100, seed=42):
    started=time.perf_counter()
    windows=synthetic_windows(n_windows,requests_per_window,seed)
    X=np.array([x.feature_vector() for x in windows],dtype=float)
    y=np.array([x.label for x in windows],dtype=int)
    train_end=int(.6*len(windows));valid_end=int(.8*len(windows))
    train_slice=slice(0,train_end);valid_slice=slice(train_end,valid_end);test_slice=slice(valid_end,len(windows))
    train_normal=X[train_slice][y[train_slice]==0]
    if len(train_normal)<15:raise RuntimeError('Not enough normal training windows')
    scaler=StandardScaler().fit(train_normal)
    Z=scaler.transform(X);norm_z=scaler.transform(train_normal)
    # M1: two independent cluster-derived distances
    kmeans=KMeans(n_clusters=3,random_state=seed,n_init=10).fit(norm_z)
    kd=np.min(np.linalg.norm(Z[:,None,:]-kmeans.cluster_centers_[None,:,:],axis=2),axis=1)
    kd_ref=np.min(np.linalg.norm(norm_z[:,None,:]-kmeans.cluster_centers_[None,:,:],axis=2),axis=1)
    k_nn=NearestNeighbors(n_neighbors=min(5,len(norm_z))).fit(norm_z)
    train_dist=k_nn.kneighbors(norm_z)[0][:,-1]
    eps=max(.001,float(np.quantile(train_dist,.8)))
    dbscan=DBSCAN(eps=eps,min_samples=5).fit(norm_z)
    core=norm_z[dbscan.core_sample_indices_]
    if len(core)==0:core=norm_z
    core_nn=NearestNeighbors(n_neighbors=1).fit(core)
    dd=core_nn.kneighbors(Z)[0][:,0]
    dd_ref=core_nn.kneighbors(norm_z)[0][:,0]
    m1=np.clip(.65*_ecdf(kd_ref,kd)+.35*_ecdf(dd_ref,dd),0,1)
    # M2: novelty score from isolation forest (learns only normal train)
    isolation=IsolationForest(n_estimators=130,contamination='auto',random_state=seed,n_jobs=1).fit(norm_z)
    novelty=-isolation.score_samples(Z)
    m2=_ecdf(-isolation.score_samples(norm_z),novelty)
    # M3: prefixspan normal session patterns only from training
    train_sequences=[s for w in windows[:train_end] if w.label==0 for s in w.sequences]
    patterns=prefixspan(train_sequences,min_support=.045,max_length=3)
    patterns=[p for p in patterns if len(p['sequence'])>=2]
    pat_top=patterns[:50]
    normalized_max=max((p['support_count'] for p in pat_top),default=1)
    m3=[]
    for w in windows:
        penalties=[]
        for seq in w.sequences:
            best=max((p['support_count']/normalized_max for p in pat_top if subsequence(tuple(p['sequence']),seq)),default=0)
            penalties.append(1-best)
        m3.append(float(np.mean(penalties)) if penalties else 0.0)
    m3=np.asarray(m3)
    # Fixed weights; calibration only on validation-normal subset.
    conditions={
      'B0':np.maximum(X[:,1]*1.75,X[:,2]*4.0),
      'B1':m2,
      'B1+D':.72*m2+.28*m1,
      'B1+S':.72*m2+.28*m3,
      'B2':.50*m2+.30*m1+.20*m3,
    }
    val_normal=(y[valid_slice]==0)
    out={}
    for name,score in conditions.items():
        normal_scores=score[valid_slice][val_normal]
        threshold=float(np.quantile(normal_scores,.95,method='higher')) if len(normal_scores) else .95
        test_scores=score[test_slice]
        prediction=(test_scores>threshold).astype(int)
        out[name]={**_metrics(y[test_slice],prediction,test_scores),'threshold':round(threshold,5)}
    elapsed=(time.perf_counter()-started)*1000
    anomaly_order=np.argsort(-conditions['B2'][test_slice])[:10]
    examples=[{'window_index':int(test_slice.start+i),'scenario':windows[test_slice.start+i].scenario,
               'actual_label':int(y[test_slice.start+i]),'combined_score':round(float(conditions['B2'][test_slice.start+i]),4),
               'm1':round(float(m1[test_slice.start+i]),4),'m2':round(float(m2[test_slice.start+i]),4),'m3':round(float(m3[test_slice.start+i]),4),
               'reason':'M2 sapması; trafik kümesi (M1) ve oturum yolu (M3) ile değerlendirilmiştir.'} for i in anomaly_order]
    return {
      'mode':'synthetic_research_experiment','trained':True,
      'conditions':out,'examples':examples,'learned_patterns':pat_top[:20],
      'data':{'total_http_requests':int(sum(w.request_count for w in windows)),
              'windows':len(windows),'train_windows':train_end,'validation_windows':valid_end-train_end,
              'test_windows':len(windows)-valid_end,'train_normal_windows':int(np.sum(y[:train_end]==0)),
              'scenarios':SCENARIOS,'seed':seed},
      'method':{'m1':'StandardScaler, KMeans centroid distance, DBSCAN core distance',
                'm2':'IsolationForest on normal train only',
                'm3':'PrefixSpan (length 2-3, normal train sessions only)',
                'm4':'0.50*M2 + 0.30*M1 + 0.20*M3, threshold from validation normals',
                'split':'chronological 60/20/20 with unique synthetic sessions per minute'},
      'elapsed_ms':round(elapsed,1),
      'warning':'Simüle edilmiş deney sonuçlarıdır. Django/Locust yük testi veya gerçek trafik sonuçları değildir.'
    }


def analyze_ingested_events(records: list[dict], seed: int = 42):
    """Exploratory unsupervised M1-M4 run on ACTUAL accepted JSONL rows.

    No ground truth is present, hence this intentionally returns no F1,
    precision, recall, or false-positive rate. For statistically useful results,
    ask for >=30 distinct minute windows, rather than inventing scores.
    """
    from collections import defaultdict
    from datetime import datetime
    started = time.perf_counter()
    by_minute = defaultdict(list)
    for item in records:
        try:
            dt = datetime.fromisoformat(str(item['occurred_at']).replace('Z', '+00:00'))
            key = dt.astimezone(timezone.utc).replace(second=0, microsecond=0).isoformat()
            by_minute[key].append(item)
        except (KeyError, ValueError, TypeError):
            continue
    keys = sorted(by_minute)
    if len(keys) < 30:
        raise ValueError(f'En az 30 farklı dakikada kayıt gerekli; mevcut {len(keys)}. JSONL dosyalarını birden fazla dakikaya yayın.')
    if len(keys) > 2400:
        raise ValueError('Tek çalıştırmada en fazla 2.400 dakika işlenebilir')
    train_end = max(20, int(len(keys) * .6))
    validation_end = max(train_end + 1, int(len(keys) * .8))
    route_reference = Counter(str(e['route']) for k in keys[:train_end] for e in by_minute[k])
    total_train = sum(route_reference.values()) or 1
    common_routes = {p for p, n in route_reference.items() if n / total_train >= .025}
    rows = []
    sequences = []
    for key in keys:
        es = sorted(by_minute[key], key=lambda r: r['occurred_at'])
        durations = np.array([float(e['duration_ms']) for e in es])
        count = len(es)
        codes = [int(e['status']) for e in es]
        sessions = defaultdict(list)
        for e in es:
            if e.get('session_ref'):
                sessions[str(e['session_ref'])].append(str(e['route']))
        seq = [tuple(routes) for routes in sessions.values() if len(routes) >= 2]
        sequences.append(seq)
        rows.append({
            'minute': key, 'request_count': count,
            'count_4xx': sum(400 <= s < 500 for s in codes),
            'count_5xx': sum(s >= 500 for s in codes),
            'p50_ms': float(np.median(durations)),
            'p95_ms': float(np.percentile(durations, 95)),
            'sessions': len(sessions),
            'route_diversity': len(set(e['route'] for e in es)),
            'rare_ratio': sum(str(e['route']) not in common_routes for e in es) / count,
            'login_failure_ratio': sum(str(e['route']).startswith('/auth/login/') and int(e['status']) >= 400 for e in es) / count,
        })
    X = np.array([
        [math.log1p(row['request_count']), row['count_4xx'] / row['request_count'], row['count_5xx'] / row['request_count'],
         math.log1p(row['p50_ms']), math.log1p(row['p95_ms']), row['sessions'] / row['request_count'],
         row['route_diversity'], 60 / row['request_count'], row['rare_ratio'], row['login_failure_ratio']]
        for row in rows
    ], dtype=float)
    scaler = StandardScaler().fit(X[:train_end]); Z = scaler.transform(X)
    baseline = Z[:train_end]
    k = min(3, len(np.unique(baseline, axis=0)))
    km = KMeans(n_clusters=k, n_init=10, random_state=seed).fit(baseline)
    nearest_k = np.min(np.linalg.norm(Z[:, None, :] - km.cluster_centers_[None, :, :], axis=2), axis=1)
    k_ref = nearest_k[:train_end]
    neighbor = NearestNeighbors(n_neighbors=min(4, train_end)).fit(baseline)
    eps = max(.01, float(np.quantile(neighbor.kneighbors(baseline)[0][:, -1], .8)))
    cluster = DBSCAN(eps=eps, min_samples=3).fit(baseline)
    core = baseline[cluster.core_sample_indices_]
    if not len(core): core = baseline
    core_nn = NearestNeighbors(n_neighbors=1).fit(core)
    dists = core_nn.kneighbors(Z)[0][:, 0]
    m1 = np.clip(.65 * _ecdf(k_ref, nearest_k) + .35 * _ecdf(dists[:train_end], dists), 0, 1)
    iforest = IsolationForest(n_estimators=100, random_state=seed, contamination='auto', n_jobs=1).fit(baseline)
    raw = -iforest.score_samples(Z)
    m2 = _ecdf(raw[:train_end], raw)
    baseline_sessions = [sequence for item in sequences[:train_end] for sequence in item]
    patterns = prefixspan(baseline_sessions, min_support=.09, max_length=3, limit=70)
    good_patterns = [p for p in patterns if len(p['sequence']) >= 2][:35]
    strongest = max((p['support_count'] for p in good_patterns), default=1)
    m3 = []
    for seq_list in sequences:
        if not seq_list:
            m3.append(.0)
            continue
        novelty = [1 - max((p['support_count'] / strongest for p in good_patterns if subsequence(tuple(p['sequence']), seq)), default=0)
                   for seq in seq_list]
        m3.append(float(np.mean(novelty)))
    m3 = np.asarray(m3)
    combined = .5 * m2 + .3 * m1 + .2 * m3
    # Alert threshold uses only earlier (train+validation) observations, no labels.
    threshold = float(np.quantile(combined[train_end:validation_end], .95))
    alerts = []
    for i in range(validation_end, len(rows)):
        item = rows[i]
        score = float(combined[i])
        if score <= threshold: continue
        triggers = []
        if m2[i] >= .9: triggers.append('Isolation Forest sapması')
        if m1[i] >= .9: triggers.append('Yoğunluk/küme uzaklığı')
        if m3[i] >= .65: triggers.append('Nadir oturum örüntüsü')
        if not triggers: triggers.append('Birleşik bağlam puanı')
        alerts.append({
            'minute': item['minute'], 'count': item['request_count'],
            'score': round(score, 4), 'm1': round(float(m1[i]), 4),
            'm2': round(float(m2[i]), 4), 'm3': round(float(m3[i]), 4),
            'reason': ' + '.join(triggers),
        })
    return {
        'mode': 'ingested_unlabeled_analysis', 'is_synthetic': False,
        'data': {'events': len(records), 'minutes': len(rows),
                 'baseline_minutes': train_end, 'validation_minutes': validation_end - train_end,
                 'inspection_minutes': len(rows) - validation_end},
        'models': {'M1': 'KMeans ve DBSCAN', 'M2': 'IsolationForest',
                   'M3': 'PrefixSpan', 'M4': '0.50 M2 + 0.30 M1 + 0.20 M3'},
        'threshold': round(threshold, 4),
        'alarms': sorted(alerts, key=lambda x: -x['score'])[:100],
        'total_alerts': len(alerts),
        'frequent_patterns': good_patterns[:12],
        'elapsed_ms': round((time.perf_counter() - started) * 1000, 1),
        'warning': 'Etiketsiz yüklenen olaylar için keşifsel analizdir; F1 ve yanlış alarm oranı hesaplanamaz. Başlangıç bölümünü normal trafik olarak kabul etmek sınırlılıktır.'
    }
