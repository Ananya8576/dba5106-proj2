# DBA5106 Project 2: dataset selection

Dataset screening for **Project 2, Version 2 (with data)**: a classification project presented in at most 6 slides. The brief is in [`Project 2.pdf`](Project%202.pdf).

The aim is a **semiconductor-related use case**. The notebook runs the same checks on every candidate dataset, mapped to what the slides grade, so the choice rests on evidence from the real data.

**Decision: D2, WM-811K wafer maps, Edge-Loc vs Loc.** The cleaned MixedWM38 Scratch task (K) is the semiconductor alternative, and Steel Plates (E) is the non-semiconductor fallback.

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
| `EDA/Project2_Dataset_EDA.ipynb` | Screening notebook: per-dataset checks, the scorecard, the MixedWM38 artefact check, and the final ranking (last cell). Its saved outputs are the round 3 local run. |
| `EDA/output.csv` | Scorecard export from the **first** local run (A–J only, without row labels). The current scorecard is in the notebook. |

## Datasets screened
| # | Dataset | Source | Verdict from the run |
|---|---|---|---|
| A | AI4I 2020 predictive maintenance | Kaggle `shivamb/machine-predictive-maintenance-classification` | Rank 4. Synthetic, 3.4% positive |
| B | Semiconductor wafer defect (synthetic) | Kaggle `meruvakodandasuraj/semiconductor-wafer-defect-classification-dataset` | Excluded: 7 positives |
| C | MachineHack wafer anomalies | Kaggle `arbazkhan971/anomaly-detection` | Excluded: 1,558 anonymous features, heavy cleaning |
| D | WM-811K wafer maps, any pattern vs none | Kaggle `qingyi/wm811k-wafer-map` | Rank 7. Near-perfect (AUC 0.995) |
| **D2** | **WM-811K, Edge-Loc vs Loc** | same | **Rank 1** |
| E | Steel plates faults, Bumps vs rest | Kaggle `uciml/faulty-steel-plates` | Rank 3 |
| F | Machine failure (sensors) | Kaggle `umerrtx/machine-failure-prediction-using-sensor-data` | Rank 6. Glassbox beats blackbox |
| G | Predicting manufacturing defects | Kaggle `rabieelkharoua/predicting-manufacturing-defects-dataset` | Rank 5. Synthetic; 4% threshold saving |
| H | APS failure at Scania trucks | Kaggle `uciml/aps-failure-at-scania-trucks-data-set` | Excluded: anonymous, missing data, 1.7% positive |
| I | SECOM | Kaggle `paresh2047/uci-semcom` | Excluded: anonymous, missing data, 21 validation positives |
| J | Singapore rain tomorrow | data.gov.sg `d_03bb2eb67ad645d0188342fa74ad7066` | Excluded: weak signal (AUC 0.62), 16% missing |
| K | MixedWM38 mixed-type wafer maps, Scratch vs not | Kaggle `co1d7era/mixedtype-wafer-defect-datasets` | Rank 2, **cleaned version only** |
| L | Semiconductor sensor data (simulated) | Kaggle `programmer3/semiconductor-sensor-data-for-predictive-quality` | Not assessed: Kaggle returned 403 |

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

## Final ranking (round 3 local run on the real datasets)
| Rank | Dataset | Evidence | Main risk |
|---|---|---|---|
| **1** | **D2 · WM-811K Edge-Loc vs Loc** (semiconductor, real) | All checks pass except preprocessing. 1,038 validation positives (AUC ± 0.005). Glassbox 0.963 vs blackbox 0.974; the gap (+0.011, sd 0.002) is stable. Best threshold 0.26 ≈ cost-ratio threshold 0.25. The L2 glassbox is clearly worse calibrated (ECE 0.10 vs 0.027). SHAP top `largest_cluster_radius` (44%), physically meaningful. | The small gap makes the decision "choose the glassbox". Needs the 2 GB legacy pickle and feature extraction. |
| **2** | **K · MixedWM38 Scratch, cleaned** (semiconductor) | The artefact check confirmed `n_dies` is a shortcut: Scratch wafers have 2,061–2,065 dies (sd 0.6), others 1,843–2,234 (sd 21.7). The 1,024 duplicate rows are 97.7% Scratch. After deduplicating and dropping `n_dies`: glassbox 0.617 vs blackbox 0.876, the largest gap of any candidate. | Calibration, noise, threshold and SHAP not yet rerun on the cleaned data. The 50% prevalence is artificial (GAN balancing). A 0.617 logistic is a weak glassbox: try a shallow tree, EBM or FIGS. |
| **3** | **E · Steel plates, Bumps vs rest** (real, not semiconductor) | No cleaning, no missing data. Glassbox 0.839 vs blackbox 0.923 (+0.085, sd 0.017). Threshold saving 77%. SHAP spread out (top feature 11%). | Not semiconductor. Correlated pairs (use LASSO). About 8 validation positives per calibration bin. |
| 4 | A · AI4I | Gap +0.077 (sd 0.015); a glassbox with physics features reaches 0.914. | Synthetic, 3.4% positive, 27 contradictory labels, heavily used on Kaggle. |
| 5 | G · Manufacturing defects | No flags. Gap +0.071. | Threshold saving 4%, synthetic, defects are the 84% majority. |
| 6 | F · Machine failure | Clean. | The glassbox beats the blackbox (the blackbox wins in 4% of draws); `VOC` carries 42% of SHAP. |
| 7 | D · WM-811K, any pattern vs none | Stable. | Near-perfect (0.995). Superseded by D2. |

The flag-count summary in the notebook puts G first. The ranking above also weighs the model-decision story, the threshold story, real vs synthetic data, and semiconductor relevance. The full reasoning is in the last cell of the notebook.

## How to run
```bash
pip install kagglehub pandas numpy scikit-learn scipy matplotlib shap requests
```

1. Put a Kaggle API token in `~/.kaggle/kaggle.json`, or download datasets by hand and set the matching `*_DIR` environment variable (for example `STEEL_DIR`, `WM_DIR`, `MIXED_DIR`). The full list is in `LOCAL_DIRS` in the setup cell.
2. Run all cells. A dataset that fails to load is skipped, and the scorecard is built from whatever loaded.
3. WM-811K needs several GB of RAM to load the full pickle.

## Next steps
1. Fix the business setting and cost ratio (FN:FP) for D2 before tuning anything. For example: misrouting an Edge-Loc wafer to the interior-defect team vs the reverse.
2. Build the modelling pipeline for D2 in a new notebook, reusing the held-out test split (same `SEED`). Keep the explorations few and deliberate to avoid overfitting the validation set (the slides call this the "optimizer's curse"), and look at the test split once.
3. Optional: if K is still of interest, rerun the extra checks (calibration, noise, threshold, SHAP) on the cleaned K data before comparing it with D2.
4. Fill in Kaggle usability ratings and public notebook counts in the `KAGGLE_META` table.
