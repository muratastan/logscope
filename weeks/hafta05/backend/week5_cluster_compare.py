"""Leakage-safe train/validation/test comparison: K-Means, DBSCAN, IF.

Uses *simulated aggregate windows*, not actual Django/Locust request data.
Labels are used only to select normal training windows and score held-out test.
No scenario/seed/label enters the feature vector. DBSCAN is never refit on TEST.
"""
from __future__ import annotations
from dataclasses import asdict
import math
import numpy as np
from sklearn.cluster import KMeans, DBSCAN
from sklearn.ensemble import IsolationForest
from sklearn.metrics import silhouette_score, average_precision_score, confusion_matrix
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import RobustScaler
from backend.analysis import synthetic_windows, _ecdf


def compare(seed=42,n_windows=1200,requests_per_window=102):
    windows=synthetic_windows(n_windows,requests_per_window,seed)
    X=np.asarray([w.feature_vector() for w in windows],float)
    y=np.asarray([w.label for w in windows],int)
    i=int(.6*len(X));j=int(.8*len(X))
    tr=X[:i][y[:i]==0]
    sc=RobustScaler().fit(tr)
    Z=sc.transform(X);ztr=sc.transform(tr)
    # Train-only silhouette criterion for K-Means k=2..6
    candidates=[]
    for k in range(2,7):
        m=KMeans(n_clusters=k,n_init=10,random_state=seed).fit(ztr)
        s=float(silhouette_score(ztr,m.labels_)) if len(set(m.labels_))>=2 else -1
        candidates.append((k,s,m))
    k, sil, km=max(candidates,key=lambda c:c[1])
    dist_k=np.min(np.linalg.norm(Z[:,None,:]-km.cluster_centers_[None,:,:],axis=2),axis=1)
    train_dk=np.min(np.linalg.norm(ztr[:,None,:]-km.cluster_centers_[None,:,:],axis=2),axis=1)
    # Fit eps from training-nearest-neighbour distance, train DBSCAN ONCE
    neigh=NearestNeighbors(n_neighbors=5).fit(ztr)
    radius=neigh.kneighbors(ztr)[0][:,-1]
    eps=max(1e-4,float(np.quantile(radius,.8)))
    db=DBSCAN(eps=eps,min_samples=5).fit(ztr)
    core=ztr[db.core_sample_indices_]
    if not len(core):core=ztr
    core_neigh=NearestNeighbors(n_neighbors=1).fit(core)
    db_dist=core_neigh.kneighbors(Z)[0][:,0]
    train_dd=core_neigh.kneighbors(ztr)[0][:,0]
    score_k=_ecdf(train_dk,dist_k)
    score_db=_ecdf(train_dd,db_dist)
    # Baseline comparison with IF, learned on normal train only
    forest=IsolationForest(n_estimators=130,random_state=seed,n_jobs=1).fit(ztr)
    train_if=-forest.score_samples(ztr)
    score_if=_ecdf(train_if,-forest.score_samples(Z))
    # B0: robust z-score of *volume*, matching project form
    counts=np.asarray([np.log1p(w.request_count) for w in windows])
    train_counts=counts[:i][y[:i]==0]
    median=float(np.median(train_counts))
    mad=max(1e-5,1.4826*float(np.median(np.abs(train_counts-median))))
    score_b0=np.abs(counts-median)/mad
    conditions={'B0_robust_volume_z':score_b0,'KMeans':score_k,'DBSCAN_core':score_db,'B1_IsolationForest':score_if,
                'B1_plus_D':.72*score_if+.28*(.65*score_k+.35*score_db)}
    results={}
    for key,score in conditions.items():
        normal_val=(y[i:j]==0)
        threshold=float(np.quantile(score[i:j][normal_val],.95,method='higher'))
        pred=(score[j:]>threshold).astype(int)
        cm=confusion_matrix(y[j:],pred,labels=[0,1])
        tn,fp,fn,tp=map(int,cm.ravel())
        prec=tp/max(1,tp+fp);rec=tp/max(1,tp+fn)
        f1=2*prec*rec/max(1e-12,prec+rec)
        results[key]={'precision':round(prec,4),'recall':round(rec,4),'f1':round(f1,4),
                      'normal_fpr':round(fp/max(1,fp+tn),4),'pr_auc':round(float(average_precision_score(y[j:],score[j:])),4),
                      'tn':tn,'fp':fp,'fn':fn,'tp':tp,'threshold':round(threshold,5)}
    return {'seed':seed,'dataset':'statistically simulated aggregate windows; not live Django/Locust',
            'windows':n_windows,'total_requests':sum(w.request_count for w in windows),
            'split':{'train':i,'validation':j-i,'test':len(X)-j},
            'kmeans':{'selected_k':k,'train_silhouette':round(sil,4),'candidates':{str(v[0]):round(v[1],4) for v in candidates}},
            'dbscan':{'eps':round(eps,5),'min_samples':5,'train_core_samples':len(db.core_sample_indices_),
                      'train_noise_ratio':round(float(np.mean(db.labels_<0)),4),'refit_on_test':False},
            'model_features':['log_count','rate_4xx','rate_5xx','log_p50_ms','log_p95_ms','session_ratio','route_diversity','interval_sec','rare_route_ratio','login_failure_ratio'],
            'results':results}
