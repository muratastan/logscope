# LogScope Week 3 and Week 5 - verified measured OFFLINE results

This report uses OFFLINE statistical simulation. It is NOT a live HTTP / Locust benchmark.

## Frozen held-out seed 97 (240 minutes; 120 normal, 120 attack)

| Algorithm | F1 | Recall | FPR | TP | FP | FN | TN |
|---|---:|---:|---:|---:|---:|---:|---:|
| B0_volume | 0.00% | 0.00% | 5.00% | 0 | 6 | 120 | 114 |
| B0_multivariate | 97.96% | 100.00% | 4.17% | 120 | 5 | 0 | 115 |
| M1_KMeans | 98.36% | 100.00% | 3.33% | 120 | 4 | 0 | 116 |
| M1_DBSCAN | 97.17% | 100.00% | 5.83% | 120 | 7 | 0 | 113 |
| B1_IsolationForest | 92.77% | 90.83% | 5.00% | 109 | 6 | 11 | 114 |

## Five repeated OFFLINE experiments (different synthetic generator)

**Do not confuse this with five real network traffic datasets or with the primary seed-based source.**

| Algorithm | Mean F1 | F1 sample SD | Mean FPR |
|---|---:|---:|---:|
| B0_volume | 0.00% | 0.00% | 5.67% |
| B0_multivariate | 98.56% | 0.89% | 0.00% |
| M1_KMeans | 97.48% | 0.33% | 5.17% |
| M1_DBSCAN | 96.09% | 1.40% | 8.17% |
| B1_IsolationForest | 23.98% | 7.44% | 6.17% |

## Ablation: remove rare_route_ratio from all methods

The simulator gives many anomalies a large rare-route ratio, a possible design artifact.

| Algorithm | F1 | Recall | FPR |
|---|---:|---:|---:|
| B0_volume | 0.00% | 0.00% | 5.00% |
| B0_multivariate | 89.19% | 82.50% | 2.50% |
| M1_KMeans | 84.26% | 75.83% | 4.17% |
| M1_DBSCAN | 86.11% | 77.50% | 2.50% |
| B1_IsolationForest | 72.45% | 59.17% | 4.17% |

## Conclusions and open acceptance

The primary simulation exhibits strong gains in multivariate robust Z and M1 clustering compared with volume-only B0. Across a different simulation generator, Isolation Forest F1 drops severely. This explicitly limits a generalization claim.
For Week 5, API authentication and React route/JSX checks are run. The full React production build, live PostgreSQL deployment and live Locust test are NOT yet verified.
Do not compare these window-level metrics to ModSec-WP HTTP request-level scores without a matched task and split.
