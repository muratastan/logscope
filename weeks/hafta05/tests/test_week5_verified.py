"""Week 3/5 pipeline and React-exposed research result checks."""
import numpy as np
import pandas as pd
from fastapi.testclient import TestClient
from backend.week5_verified_compare import (load_external_minutes, evaluate,
    check_test_invariance, prepare_generated, MODELS)
from backend.fullstack import app


def _files():
    from pathlib import Path
    p=Path(__file__).resolve().parents[1]/'datasets'/'ana'
    return p/'logscope_ana_1200_pencere_ozellikleri.csv',p/'logscope_ana_dakika_etiketleri.csv'


def test_frozen_seed_splits_and_no_meta_features():
    p=load_external_minutes(*_files())
    assert p.X.shape==(1200,10)
    assert list(map(int,[(p.split==x).sum() for x in ('train','validation','test')]))==[720,240,240]
    assert all(x not in p.feature_names for x in ('scenario_code','seed','ground_truth','split'))
    assert check_test_invariance(p)


def test_week5_results_and_thresholds():
    p=load_external_minutes(*_files())
    table,families,audit=evaluate(p)
    assert set(table.model)==set(MODELS)
    assert set(table.fpr_target)=={.05,.1}
    assert len(table)==10
    assert table.n_test.eq(240).all()
    assert table.tp.le(120).all()
    assert audit['train_normal_rows']==360
    assert table.loc[table.model=='B0_volume','f1'].eq(0).all()
    assert len(families)==20
    assert families.attacks.eq(30).all()


def test_label_swaps_in_test_do_not_affect_training():
    p=prepare_generated(42)
    assert check_test_invariance(p)


def test_research_endpoint_is_readonly_and_requires_session():
    c=TestClient(app)
    assert c.get('/api/research/week5').status_code==401
    r=c.post('/api/login',json={'email':'demo@logscope.local','password':'Demo2026!'})
    assert r.status_code==200,r.text
    payload=c.get('/api/research/week5')
    assert payload.status_code==200,payload.text
    j=payload.json()
    assert j['no_live_locust'] is True
    assert j['primary']['test_windows']==240
    assert len(j['primary']['results'])==5
