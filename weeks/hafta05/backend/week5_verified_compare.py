"""Reproducible Week 3 and Week 5 controlled *offline* research comparison.

B0 single-volume, B0 multivariate Robust Z, M1 K-Means/DBSCAN, M2 IF.
Training uses labeled-normal training windows only (semi-supervised novelty),
thresholds use labeled-normal validation only. Held-out test is strictly read
for metrics. Source data is simulated; do NOT claim live HTTP performance.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans, DBSCAN
from sklearn.ensemble import IsolationForest
from sklearn.metrics import (average_precision_score, confusion_matrix,
                             precision_recall_fscore_support, balanced_accuracy_score,
                             matthews_corrcoef, silhouette_score)
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import RobustScaler

FEATURES = (
    "log_request_count", "rate_4xx", "rate_5xx", "log_p50_ms",
    "log_p95_ms", "unique_sessions_per_event", "route_diversity",
    "avg_request_interval_s", "rare_route_ratio", "failed_login_rate",
)
VOLUME = "log_request_count"
MODELS = ("B0_volume", "B0_multivariate", "M1_KMeans", "M1_DBSCAN", "B1_IsolationForest")


@dataclass(frozen=True)
class Prepared:
    X: np.ndarray
    y: np.ndarray
    split: np.ndarray
    scenario: np.ndarray
    minute: np.ndarray
    feature_names: tuple[str, ...]
    dataset_kind: str


def load_external_minutes(features_path, labels_path):
    """Validate source minute grain and supplied, frozen block splits."""
    f = pd.read_csv(features_path)
    m = pd.read_csv(labels_path)
    if f.minute_start_utc.duplicated().any() or m.minute_start_utc.duplicated().any():
        raise ValueError("One row per minute required; duplicate minutes found")
    if not set(FEATURES).issubset(f.columns):
        raise ValueError("Required feature columns missing")
    need = {"minute_start_utc", "scenario_code", "ground_truth", "split", "seed", "ambiguous"}
    if not need.issubset(m.columns):
        raise ValueError("Missing manifest metadata")
    df = f.merge(m, on="minute_start_utc", how="outer", validate="one_to_one", indicator=True)
    if (df._merge != "both").any():
        raise ValueError("Features and manifest have unmatched minute timestamps")
    df = df.sort_values("minute_start_utc").reset_index(drop=True)
    if df["ambiguous"].astype(str).str.lower().isin(["true", "1"]).any():
        raise ValueError("Ambiguous windows must be handled explicitly before evaluation")
    if not set(df.ground_truth.unique()) <= {"normal", "anomaly"}:
        raise ValueError("Unexpected labels")
    if set(df.split) != {"train", "validation", "test"}:
        raise ValueError("A frozen train/validation/test split is required")
    if df.groupby("seed")["split"].nunique().max() != 1:
        raise ValueError("One simulation seed crosses partitions")
    if not (df.split.iloc[:sum(df.split=="train")] == "train").all():
        raise ValueError("Train not chronological")
    x = df.loc[:, FEATURES].to_numpy(dtype=float)
    if not np.isfinite(x).all():
        raise ValueError("Nonfinite features")
    return Prepared(x, df.ground_truth.eq("anomaly").to_numpy(dtype=int),
                    df.split.to_numpy(dtype=str), df.scenario_code.to_numpy(dtype=str),
                    df.minute_start_utc.to_numpy(dtype=str), FEATURES,
                    "offline_statistical_simulation_not_live_http")


def prepare_generated(seed, n_windows=1200):
    from backend.analysis import synthetic_windows
    windows = synthetic_windows(n_windows, 102, seed)
    x = np.asarray([w.feature_vector() for w in windows], dtype=float)
    i, j = int(.6 * len(x)), int(.8 * len(x))
    return Prepared(x, np.asarray([w.label for w in windows], dtype=int),
                    np.asarray(["train"]*i + ["validation"]*(j-i) + ["test"]*(len(x)-j)),
                    np.asarray([w.scenario for w in windows], dtype=str),
                    np.asarray([str(w.index) for w in windows], dtype=str), FEATURES,
                    "repeated_offline_statistical_simulation_not_live_http")


def _robust_center_scale(z):
    center = np.median(z, axis=0)
    mad = 1.4826 * np.median(np.abs(z - center), axis=0)
    q1, q3 = np.percentile(z, [25, 75], axis=0)
    iqr = (q3-q1) / 1.349
    sd = np.std(z, axis=0)
    # Fixed 0.01 floor in the scaled feature's original units for dimensions
    # with no normal variance: this prevents zero division and unbounded scores.
    scale = np.where(mad>1e-8, mad, np.where(iqr>1e-8,iqr,
                  np.where(sd>1e-8,sd, 0.01)))
    return center, scale


def _calc_scores(p:Prepared, random_state=42):
    X, y, split = p.X, p.y, p.split
    train = (split=="train") & (y==0)
    if train.sum()<35 or ((split=="validation") & (y==0)).sum()<15:
        raise ValueError("Not enough normal train/calibration windows")
    Xnormal = X[train]
    center, scale = _robust_center_scale(Xnormal)
    robust_scores = np.max(np.abs((X-center)/scale),axis=1)
    vcol=p.feature_names.index(VOLUME)
    vol_scores=np.abs((X[:,vcol]-center[vcol])/scale[vcol])
    scaler=RobustScaler(quantile_range=(10,90)).fit(Xnormal)
    Z = scaler.transform(X)
    Znormal = scaler.transform(Xnormal)
    if not np.isfinite(Z).all():
        raise ValueError("Nonfinite scaled values")
    forest=IsolationForest(n_estimators=250, max_samples=min(256,len(Znormal)),
                           contamination="auto",random_state=random_state,n_jobs=1).fit(Znormal)
    if_scores=-forest.score_samples(Z)
    possible=[]
    for k in (2,3,4,5):
        km=KMeans(n_clusters=k,random_state=random_state,n_init=10).fit(Znormal)
        label_count=np.unique(km.labels_).size
        quality=silhouette_score(Znormal,km.labels_) if 1<label_count<len(Znormal) else -1.
        possible.append((quality,k,km))
    sil,k,km=max(possible,key=lambda x:x[0])
    km_scores=np.min(np.linalg.norm(Z[:,None,:]-km.cluster_centers_[None,:,:],axis=2),axis=1)
    neigh=NearestNeighbors(n_neighbors=6).fit(Znormal)
    kdist=neigh.kneighbors(Znormal)[0][:,-1]
    eps=max(float(np.quantile(kdist,.9)),1e-6)
    db=DBSCAN(eps=eps,min_samples=5).fit(Znormal)
    core=Znormal[db.core_sample_indices_]
    if core.size==0:
        raise RuntimeError("DBSCAN found no core samples; do not fake a fit")
    core_nn=NearestNeighbors(n_neighbors=1).fit(core)
    db_scores=core_nn.kneighbors(Z)[0][:,0]
    audit={"train_normal_rows":int(train.sum()),"fit_from_normal_training_only":True,
           "kmeans_k":int(k),"kmeans_train_silhouette":round(float(sil),4),
           "dbscan_eps":round(eps,5),"dbscan_core_count":int(len(core)),
           "dbscan_train_noise_fraction":round(float(np.mean(db.labels_<0)),4),
           "no_test_refit":True,"feature_names":list(p.feature_names),
           "if_estimators":250,"if_max_samples":min(256,len(Znormal)),
           "robust_z_clipped":False}
    return dict(zip(MODELS,[vol_scores,robust_scores,km_scores,db_scores,if_scores])),audit


def metrics(y,pred,scores):
    tn,fp,fn,tp=map(int,confusion_matrix(y,pred,labels=[0,1]).ravel())
    prec,rec,f1,_=precision_recall_fscore_support(y,pred,average="binary",zero_division=0)
    return {"tn":tn,"fp":fp,"fn":fn,"tp":tp,
            "precision":round(float(prec),5),"recall":round(float(rec),5),"f1":round(float(f1),5),
            "fpr":round(float(fp/max(tn+fp,1)),5),
            "balanced_accuracy":round(float(balanced_accuracy_score(y,pred)),5),
            "mcc":round(float(matthews_corrcoef(y,pred)),5),
            "average_precision":round(float(average_precision_score(y,scores)),5)}


def evaluate(p:Prepared, random_state=42, fpr_targets=(.05,.10)):
    scores,audit=_calc_scores(p,random_state=random_state)
    normal_val=(p.split=="validation") & (p.y==0)
    test=p.split=="test"
    if test.sum()<20 or len(set(p.y[test]))!=2:
        raise ValueError("Need normal and anomalous held-out windows")
    rows=[];family=[];thresholds={}
    for target in fpr_targets:
        for name,all_scores in scores.items():
            cutoff=float(np.quantile(all_scores[normal_val],1-target,method="higher"))
            pred=all_scores[test]>cutoff
            m=metrics(p.y[test],pred.astype(int),all_scores[test])
            rows.append({"source":p.dataset_kind,"fpr_target":target,"model":name,
                         "threshold":cutoff,"n_test":int(test.sum()),
                         "test_attack_fraction":float(p.y[test].mean()),**m})
            thresholds[f"{name}_{target}"]=cutoff
            if target==.05:
                for fam in sorted(set(p.scenario[test][p.y[test]==1])):
                    member=test & (p.scenario==fam) & (p.y==1)
                    family.append({"model":name,"scenario":fam,"attacks":int(member.sum()),
                                   "detected":int(np.sum(all_scores[member]>cutoff)),
                                   "recall":round(float(np.mean(all_scores[member]>cutoff)),5)})
    audit.update({"source":p.dataset_kind,"train_windows":int((p.split=="train").sum()),
                  "validation_windows":int((p.split=="validation").sum()),
                  "test_windows":int(test.sum()),"normal_validation_count":int(normal_val.sum()),
                  "normal_test_count":int(np.sum(test & (p.y==0))),
                  "attack_test_count":int(np.sum(test & (p.y==1))),
                  "feature_names":list(p.feature_names),
                  "threshold_fitted_from_normal_validation_only":True,
                  "labels_not_used_as_model_features":True,"thresholds":thresholds})
    return pd.DataFrame(rows),pd.DataFrame(family),audit


def check_test_invariance(p:Prepared):
    """Score fitting and calibration must not depend on test rows/labels."""
    s,a=_calc_scores(p)
    q=Prepared(p.X.copy(),p.y.copy(),p.split.copy(),p.scenario.copy(),p.minute.copy(),p.feature_names,p.dataset_kind)
    ix=np.flatnonzero(q.split=="test")
    q.X[ix]=q.X[ix]+np.random.default_rng(55).normal(100,1,size=q.X[ix].shape)
    q.y[ix]=1-q.y[ix]
    t,b=_calc_scores(q)
    assert a==b
    for model in MODELS:
        assert np.allclose(s[model][p.split!="test"],t[model][q.split!="test"])
    return True


def save_reports(output_dir, primary, rep, family, primary_audit, rep_audit, ablation):
    output=Path(output_dir);output.mkdir(parents=True,exist_ok=True)
    primary.to_csv(output/"holdout_seed97_metrics.csv",index=False)
    rep.to_csv(output/"five_seed_repeat_metrics.csv",index=False)
    family.to_csv(output/"holdout_attack_family_recall.csv",index=False)
    ablation.to_csv(output/"ablation_no_rare_route.csv",index=False)
    summaries=rep.groupby(["model","fpr_target"],sort=False).agg(
        f1_mean=("f1","mean"),f1_std=("f1","std"),recall_mean=("recall","mean"),
        fpr_mean=("fpr","mean"),balanced_accuracy_mean=("balanced_accuracy","mean")
    ).reset_index()
    summaries.to_csv(output/"five_seed_summary.csv",index=False)
    (output/"audit.json").write_text(json.dumps({"primary":primary_audit,"replicates":rep_audit,
        "truth":"OFFLINE SIMULATION ONLY; no live Locust or real-world HTTP accuracy verified",
        "data_warning":"Simulation generator makes unusual-route ratios high across many attack scenarios; ablation included",
        "selection":"Model choices and thresholds fixed before reading test labels; no test-based model selection",
        "deployment_performance":"NOT MEASURED"},ensure_ascii=True,indent=2),encoding="utf-8")
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    display=primary[primary.fpr_target==.05].copy()
    fig,ax=plt.subplots(figsize=(9,4.5))
    xx=np.arange(len(display))
    ax.bar(xx-.18,display.f1.to_numpy()*100,width=.36,label="F1 score")
    ax.bar(xx+.18,display.recall.to_numpy()*100,width=.36,label="Attack recall")
    ax.set_xticks(xx,display.model.str.replace("_"," "),rotation=20,ha="right")
    ax.set_ylim(0,105);ax.set_ylabel("Held-out metric (%)")
    ax.set_title("Offline simulation: fixed held-out seed (not real HTTP)")
    ax.legend();fig.tight_layout();fig.savefig(output/"01_holdout_f1_recall.png",dpi=145);plt.close(fig)
    fig,ax=plt.subplots(figsize=(8,4))
    width=.35
    order=["B0_volume","B0_multivariate","M1_KMeans","M1_DBSCAN","B1_IsolationForest"]
    sub=summaries[summaries.fpr_target==.05].set_index("model").loc[order]
    ax.bar(np.arange(len(order)),sub.f1_mean*100,yerr=sub.f1_std*100,capsize=3)
    ax.set_xticks(np.arange(len(order)),[s.replace("_"," ") for s in order],rotation=20,ha="right")
    ax.set_ylim(0,105);ax.set_ylabel("Mean F1 +/- SD across five simulated seeds (%)")
    ax.set_title("Week 5: KMeans, DBSCAN, Isolation Forest and Robust Z")
    fig.tight_layout();fig.savefig(output/"02_five_seed_comparison.png",dpi=145);plt.close(fig)
    report={"dataset":"OFFLINE synthetic minute aggregates (not live requests)",
       "primary":{"split":"train=seeds 11/23/42, validation=71, test=97",
          "test_windows":int(primary.iloc[0].n_test),"fixed_fpr_target":.05,
          "results":[{k:(float(v) if isinstance(v,(float,np.floating)) else int(v) if isinstance(v,(int,np.integer)) else v) for k,v in d.items()} for d in display.to_dict(orient="records")]},
       "five_repeats":"five separate offline statistical simulations; results below are not independent field samples",
       "summary":[{k:(float(v) if isinstance(v,(float,np.floating)) else v) for k,v in row.items()} for row in summaries[summaries.fpr_target==.05].to_dict(orient="records")],
       "no_live_locust":True,"no_real_http_f1":True}
    (output/"week5_api_summary.json").write_text(json.dumps(report,indent=2,ensure_ascii=True),encoding="utf-8")
    return report
