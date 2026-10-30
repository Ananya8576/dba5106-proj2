# DBA5106 Project 2: dataset selection

Dataset screening for **Project 2, Version 2 (with data)**: a classification project presented in at most 6 slides. The brief is in [`Project 2.pdf`](Project%202.pdf).

The aim is a **semiconductor-related use case**. The notebook checks each candidate dataset against what the slides grade, so the choice is evidence-based.

## What the project has to show
- A classification task whose **evaluation loss deviates from misclassification**, with the threshold chosen to minimise that loss.
- At least one **glassbox** and one **blackbox** model, each trained with **L2 loss and a surrogate loss**, tuned separately.
- Models compared on **validation AUC** (not train loss), then a decision.
- **Calibration**: are the models calibrated, and can they be recalibrated?
- **Tree SHAP**, local and global, on a tree-based blackbox.
- Dataset guidance: avoid severe imbalance, large datasets, heavy cleaning and missing data; prefer high Kaggle usability; if the prediction is almost perfect, delete features to make it harder.

## Repository layout
| Path | What it is |
|---|---|
| `Project 2.pdf` | Project brief (lecture slides) |
| `EDA/Project2_Dataset_EDA.ipynb` | Screening notebook: the same checks on every candidate, a scorecard, and the ranking |
| `EDA/output.csv` | Scorecard export from a full local run |

## Datasets screened
| # | Dataset | Source | Notes |
|---|---|---|---|
| A | AI4I 2020 predictive maintenance | Kaggle `shivamb/machine-predictive-maintenance-classification` | Synthetic, 3.4% positive |
| B | Semiconductor wafer defect (synthetic) | Kaggle `meruvakodandasuraj/semiconductor-wafer-defect-classification-dataset` | **Excluded**: 7 positives |
| C | MachineHack wafer anomalies | Kaggle `arbazkhan971/anomaly-detection` | 1,558 anonymous features |
| D | WM-811K wafer maps, any pattern vs none | Kaggle `qingyi/wm811k-wafer-map` | Near-perfect (AUC 0.995) |
| D2 | WM-811K, Edge-Loc vs Loc | same | Harder pairwise task |
| E | Steel plates faults | Kaggle `uciml/faulty-steel-plates` | Real data, named features |
| F | Machine failure (sensors) | Kaggle `umerrtx/machine-failure-prediction-using-sensor-data` | Small; glassbox beats blackbox |
| G | Predicting manufacturing defects | Kaggle `rabieelkharoua/predicting-manufacturing-defects-dataset` | Synthetic; defects are the 84% majority |
| H | APS failure at Scania trucks | Kaggle `uciml/aps-failure-at-scania-trucks-data-set` | Official 10/500 cost; anonymous features, missing data |
| I | SECOM | Kaggle `paresh2047/uci-semcom` | Anonymous features, missing data |
| J | Singapore rain tomorrow | data.gov.sg `d_03bb2eb67ad645d0188342fa74ad7066` | Weak signal, 16% missing |
| K | MixedWM38 mixed-type wafer maps, Scratch vs not | Kaggle `co1d7era/mixedtype-wafer-defect-datasets` | Easy to load; partly GAN-generated |
| L | Semiconductor sensor data (simulated) | Kaggle `programmer3/semiconductor-sensor-data-for-predictive-quality` | Not loaded (Kaggle 403) |

The wafer-map datasets (D, D2, K) are turned into 10 named spatial features per wafer (zone fail rates, cluster size and radius, angular concentration), so tabular models and tree SHAP apply.

## Checks run on each dataset
1. Size, missing data, cleaning load (duplicates, conflicting labels, constant, ID and duplicate columns).
2. Class balance, and the number of positives expected in validation.
3. Leakage scan (single-feature AUC) and correlated feature pairs.
4. Untuned glassbox (logistic regression) vs blackbox (gradient boosting) CV AUC, plus a difficulty probe that drops the strongest features.
5. Whether the features are named, so SHAP has something to explain.
6. **L2 vs surrogate train loss** for both models.
7. **Calibration**: reliability diagram, Brier score, ECE, Platt scaling.
8. **Validation noise**: how much AUC and the model gap move on a validation-sized split.
9. **Evaluation loss**: expected-cost curve, best threshold vs 0.5.
10. **Tree SHAP** smoke test: global and local plots, and a flag when one feature dominates.

A 20% test split is held out before any check that uses labels. All the models are untuned, so these are feasibility signals, not results for the slides.

## Current ranking (from the round 2 local run)
| Rank | Dataset | Summary |
|---|---|---|
| **1** | **D2 · WM-811K Edge-Loc vs Loc** | Semiconductor, real fab data. Every check passes except preprocessing. About 1,038 validation positives, so the estimates are stable. Glassbox 0.963 vs blackbox 0.974. The best threshold (0.26) matches the cost ratio (0.25). The 2 GB legacy pickle needs preprocessing. |
| **2** | **K · MixedWM38, Scratch vs not** | Semiconductor and easy to load. The largest stable model gap (0.685 vs 0.917). However, `n_dies` is the top SHAP driver and is probably an artefact, and the data has duplicates and GAN-generated maps. Run the artefact check before choosing it. |
| **3** | **E · Steel plates, Bumps vs rest** | Non-semiconductor fallback. Real, clean data, a stable gap (+0.085), and SHAP spread over several features. |

The full reasoning is in the last cell of the notebook.

## How to run
```bash
pip install kagglehub pandas numpy scikit-learn scipy matplotlib shap requests
```

1. Put a Kaggle API token in `~/.kaggle/kaggle.json`, or download datasets by hand and set the matching `*_DIR` environment variable (for example `STEEL_DIR`, `WM_DIR`, `MIXED_DIR`). The full list is in `LOCAL_DIRS` in the setup cell.
2. Run all cells. A dataset that fails to load is skipped, and the scorecard is built from whatever loaded.
3. WM-811K needs several GB of RAM to load the full pickle.

## Next steps
1. Run the MixedWM38 artefact check (the cell after section K), then choose between D2 and K.
2. Fill in Kaggle usability ratings and public notebook counts in the `KAGGLE_META` table.
3. Fix the business setting and cost ratio (FN:FP) for the chosen dataset before tuning anything.
4. Build the modelling pipeline in a new notebook. Keep the explorations few and deliberate to avoid overfitting the validation set (the slides call this the "optimizer's curse"), and look at the test split once.
