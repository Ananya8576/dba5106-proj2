# DBA5106 Project 2: wafer defect routing (classification)

**Project 2, Version 2 (with data)**: a classification project presented in at most 6 slides. The brief is in [`Project 2.pdf`](Project%202.pdf).

**The project.** A fab wafer shows a local cluster of failing dies. Is it **Edge-Loc** (a tool's edge process is drifting, so hold the tool) or **Loc** (a one-off particle)? A missed Edge-Loc is assumed to cost 5 times an unnecessary tool hold. Data: WM-811K wafer maps (Kaggle `qingyi/wm811k-wafer-map`), 8,782 labelled wafers, 10 engineered features.

## What the project has to show
Classification project
- Find your dataset. For example, find a high-usability dataset on Kaggle. 
- The evaluation loss shall deviate from the misclassification loss. The deviation shall come from the context.
- Interpretability and performance.
- You must implement at least one glassbox and at least one blackbox model.
- Each model shall have two versions (train loss): L2 loss vs. other surrogate losses.
- Compare all of them using validation AUC (not training loss) and make a decision.
- For the chosen model, select the threshold that minimizes the evaluation loss.
- Calibration: is your model calibrated? If not, how can you improve its calibration?
- SHAP: Even if you decide to use a glassbox model, you still need to apply tree SHAP to one tree-based blackbox model. The interpretability part must contain both local and global SHAP.

## Results
From `project/Project2_Classification.ipynb`, run on the real data.

| Requirement | What we did | Result |
|---|---|---|
| Evaluation loss from the context | (5·FN + FP) / n: a missed edge excursion vs an unnecessary tool hold | Sensitivity shown for ratios 1–10 |
| Glassbox and blackbox | L1-penalised linear model; gradient-boosted trees | |
| L2 vs surrogate loss, tuned separately | Squared error vs log loss; 4 searches, 24 configurations, by cross-validation inside the training split | Log loss wins for both (+0.008 and +0.007 AUC) |
| Compare on validation AUC, decide | Glassbox 0.958 (L2), 0.966 (log loss); blackbox 0.966 (L2), 0.972 (log loss) | **Chosen: glassbox, log loss.** The blackbox's AUC is 0.006 higher, but its evaluation loss is not lower (0.149 vs 0.143) |
| Threshold minimising the evaluation loss | 0.28 on the raw score (0.22 after calibration) | 27% lower loss than a 0.5 threshold on validation |
| Calibration | ECE 0.031; isotonic regression fitted on out-of-fold training scores | ECE about 0.02, AUC unchanged |
| Tree SHAP, global and local | On the log-loss gradient-boosted trees; local plots shown next to the wafer maps | `largest_cluster_radius` dominates |
| Final test (used once) | Frozen model, calibrator and threshold | AUC 0.958 (95% CI 0.946–0.969); loss 0.181 per wafer, 56% below holding every wafer |

**What sets it apart:** our own physical features instead of a CNN; a harder question than the near-perfect "defect vs none"; splits by lot; hyperparameters tuned inside train so validation answers one question; lot-bootstrap intervals on every comparison; calibration tied to the theoretical threshold; local SHAP next to the wafer map.

## Flags
These are the places where the project departs from the brief or is weaker than it looks. The notebook's last section has the full list.

1. **Kaggle usability rating not verified.** Kaggle's API needs a login. Check the rating on the dataset page before presenting.
2. **The source dataset is large** (811,457 maps, 2 GB), against "avoid large datasets". We model an 8,782-wafer subset saved as a 1 MB table.
3. **Feature extraction is preprocessing**, against "avoid data cleaning". It's deliberate; no rows were dropped or imputed.
4. **The 5:1 cost ratio is our assumption.** The dataset has no cost data.
5. **The glassbox's coefficients are hard to read.** Cross-validation chose the weakest penalty in the grid, all 10 features stay, and correlated features get large opposite-sign coefficients.
6. **Test is worse than validation** (loss 0.181 vs 0.143), as expected when the model and threshold are picked on validation.
7. **On test the blackbox's AUC lead is larger** (0.968 vs 0.959). We did not revisit the choice after seeing the test split.
8. **Labels are engineers' judgements.** The costliest mistake looks like a labelling error.

## Repository layout
| Path | What it is |
|---|---|
| `Project 2.pdf` | Project brief (lecture slides) |
| `project/Project2_Classification.ipynb` | **The project**: all requirements, with outputs |
| `project/SLIDES.md` | Outline for the 6 slides, with the numbers and figures to use |
| `project/figures/` | Figures saved by the notebook |
| `project/build_features.py` | Builds the feature table and wafer maps from the Kaggle file |
| `project/data/` | The feature table (8,782 wafers) and their wafer maps |
| `project/results_summary.json` | Key results, written by the notebook |
| `EDA/Project2_Dataset_EDA.ipynb` | Dataset screening: 13 candidates, the same checks on each, and the ranking |
| `EDA/output.csv` | Scorecard export from the first screening run (A–J only) |

## How to run the project
```bash
pip install pandas numpy scikit-learn scipy matplotlib shap
```
```bash
cd project && jupyter nbconvert --to notebook --execute --inplace Project2_Classification.ipynb
```
The notebook reads `project/data/`, so it doesn't need Kaggle. To rebuild that data from the source file (needs `kagglehub` and several GB of RAM):
```bash
python project/build_features.py
```

# Dataset selection
The dataset was chosen by screening 13 candidates in `EDA/Project2_Dataset_EDA.ipynb`. That screening used random splits; the project notebook splits by lot.

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

## How to run the screening notebook
```bash
pip install kagglehub pandas numpy scikit-learn scipy matplotlib shap requests
```

1. Put a Kaggle API token in `~/.kaggle/kaggle.json`, or download datasets by hand and set the matching `*_DIR` environment variable (for example `STEEL_DIR`, `WM_DIR`, `MIXED_DIR`). The full list is in `LOCAL_DIRS` in the setup cell.
2. Run all cells. A dataset that fails to load is skipped, and the scorecard is built from whatever loaded.
3. WM-811K needs several GB of RAM to load the full pickle.

## Next steps
1. Check the Kaggle usability rating for `qingyi/wm811k-wafer-map`.
2. Build the 6 slides from `project/SLIDES.md`.
3. Decide how to defend the 5:1 cost ratio in the Q&A, or replace it with a figure you can source.
