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

## End-to-end check
Four checkpoints, in the order the work was done. Every number is from `project/Project2_Classification.ipynb` unless it says "screening", which means `EDA/Project2_Dataset_EDA.ipynb`.

### Checkpoint 1: dataset and data sanity
**Why this dataset.** 13 candidates were screened with the same checks (see "Dataset selection" below). WM-811K Edge-Loc vs Loc was the only semiconductor candidate that passed everything except preprocessing.

| Brief's guidance | Check | Result | Verdict |
|---|---|---|---|
| High-usability Kaggle dataset | Kaggle page | Rating could not be read (the API needs a login) | **Unverified: check by hand** |
| Avoid large datasets | Rows used | 8,782 wafers, 10 features, 1 MB table. The source file is 811,457 maps, 2 GB | **Flag**: large source, small working set |
| Avoid missing data | Missing cells | 0 | Pass |
| Avoid data cleaning | Duplicates, conflicting labels, constant columns | 55 duplicate feature rows (0.6%), none with conflicting labels; no constant columns. Nothing dropped or imputed | Pass, but **flag**: the maps needed feature extraction |
| Avoid severe imbalance | Class balance | 59.1% Edge-Loc; 1,038 Edge-Loc wafers in validation | Pass |
| Not almost perfect | Untuned baselines (screening) | AUC 0.963 and 0.974. "Defect vs none" on the same data was 0.995, so the question was changed | Pass |
| No leakage | Single-feature AUC (screening); lots | Strongest single feature 0.892. 5,008 lots, so splits are by lot | Pass |
| Features that can be explained | Feature names | 10 physical features (fail rate by zone, cluster size and position) | Pass |

Splits: 60 / 20 / 20 **by lot**, stratified. Train 5,268 wafers, validation 1,756, test 1,758, each 59.1% Edge-Loc.

### Checkpoint 2: models, what was tried, and the decision
| | L2 loss | Surrogate loss (log loss) |
|---|---|---|
| **Glassbox:** L1-penalised linear model on standardised features | LASSO regression on the 0/1 label | L1 logistic regression |
| **Blackbox:** gradient-boosted trees (scikit-learn `HistGradientBoosting`) | Squared error | Log loss |

**What was tried.** 24 configurations in total, 6 per model, each model tuned separately by 5-fold cross-validated AUC inside the training split (folds by lot):
- Glassbox: penalty strength, 6 values.
- Blackbox: tree depth (2, 3, 5) × number of trees (100, 300), learning rate 0.1.

| Model | Train loss | Chosen setting | Training AUC | Validation AUC (95% CI) |
|---|---|---|---|---|
| Glassbox | L2 | alpha = 0.0003 | 0.960 | 0.958 (0.947–0.968) |
| Glassbox | Log loss | C = 10 | 0.969 | **0.966** (0.957–0.974) |
| Blackbox | L2 | depth 3, 300 trees | 0.988 | 0.966 (0.954–0.975) |
| Blackbox | Log loss | depth 5, 300 trees | 1.000 | **0.972** (0.963–0.980) |

**Judgement checks behind the decision**
1. **L2 vs log loss.** Log loss wins for both: +0.008 for the glassbox (CI +0.003 to +0.014) and +0.007 for the blackbox (CI +0.003 to +0.011).
2. **Glassbox vs blackbox.** The blackbox's validation AUC is 0.006 higher (CI +0.0001 to +0.012), so it only just clears zero.
3. **Does that AUC gain lower the cost?** No. At each model's best threshold the evaluation loss is 0.143 for the glassbox and 0.149 for the blackbox.
4. **Rule set before looking at validation:** choose the blackbox only if its AUC is distinguishably higher and it lowers the evaluation loss by at least 10%.
5. **Cost-ratio sensitivity.** The glassbox is the cheaper model for ratios 3 to 8; the blackbox is marginally cheaper at 1–2 and 9–10.

**Decision: the glassbox, L1 logistic regression trained with log loss.**

**Was it the best decision?** It is defensible, but the data doesn't show it is the cheaper model. In a post-hoc audit on test, the blackbox scores 0.158 against the glassbox's 0.181 (8 fewer missed Edge-Loc wafers, the same 178 false alarms). The difference is −0.023 (95% CI −0.051 to +0.007), which isn't distinguishable from zero. We did not switch after seeing test. On a strict reading of "compare using validation AUC", the blackbox ranks first; our choice adds the evaluation loss and interpretability to that comparison.

### Checkpoint 3: losses, metrics and calibration
**Losses, as the brief asks**
- **Train loss:** L2 vs log loss for both model types (checkpoint 2).
- **Evaluation loss:** (5·FN + FP) / n, from the context: a missed edge excursion vs an unnecessary tool hold. It deviates from misclassification, which would weigh both errors equally.
- **Comparison:** on validation AUC, not training loss. Training AUC is shown only to make the point: the blackbox reaches 1.000 on training data.

**Threshold for the chosen model (validation)**

| Threshold on the raw score | Missed Edge-Loc | False alarms | Accuracy | Evaluation loss |
|---|---|---|---|---|
| 0.5 (default) | 49 | 99 | 91.6% | 0.196 |
| 0.28 (minimises the evaluation loss) | 18 | 161 | 89.8% | **0.143** |

Accuracy falls by 1.8 points and the cost falls by 27%. Minimising plain misclassification would put the threshold at 0.61.

**Other metrics reported:** for all four models on validation, average precision, Brier score, accuracy at 0.5 and the evaluation loss; for the chosen model, also recall, precision and the confusion matrix on validation and test.

**Calibration**
- **How it was checked:** reliability diagram, expected calibration error (ECE, 10 bins) and Brier score on validation, for all four models.
- **What was found:** the chosen glassbox is mildly off (ECE 0.031). It under-predicts between 0.2 and 0.5, where the threshold sits. The L2 glassbox is the worst (ECE 0.107), and the L2 models put 20–29% of scores outside 0–1.
- **What was done:** Platt scaling and isotonic regression, each fitted on out-of-fold training scores so validation stays clean. Isotonic was kept (lowest Brier score): ECE 0.031 → 0.021, AUC unchanged. Platt barely helps the logistic model (0.029) but works for the blackbox (0.034 → 0.013).
- **Link to the threshold:** on calibrated probabilities the best threshold is 0.22; decision theory gives 1/(1+5) = 0.167, which costs almost the same (0.148 vs 0.143).

**Test split, used once:** AUC 0.958 (95% CI 0.946–0.969), evaluation loss 0.181 per wafer (CI 0.143–0.223), accuracy 88.3%, recall 97.3%, precision 85.0%, ECE 0.019. Holding the tool for every wafer would cost 0.409.

### Checkpoint 4: tree SHAP and interpretability
The brief requires tree SHAP on a tree-based blackbox even when a glassbox is chosen. It was applied to the log-loss gradient-boosted trees with `shap.TreeExplainer`, on the validation split.

| Required | Shown | Figure |
|---|---|---|
| Global SHAP | Mean absolute SHAP per feature, and a plot of every wafer's SHAP values coloured by feature value | `project/figures/07_shap_global.png` |
| Local SHAP | Three wafers picked by rule (most confident Edge-Loc, most confident Loc, costliest mistake), each next to its wafer map | `project/figures/09_shap_local.png` |
| Extra | How the two top features move the prediction | `project/figures/08_shap_dependence.png` |

- **What the model relies on:** `largest_cluster_radius` (mean absolute SHAP 4.0), then `edge_fail_rate` (1.8) and `outer_ring_fail_rate` (0.9). That matches the question: is the cluster at the edge?
- **Correctness check:** each wafer's SHAP values plus the base value add up to the model's log-odds (largest gap 4e-11).
- **Costliest mistake:** a wafer labelled Edge-Loc whose cluster sits near the centre (radius 0.32). Both models call it Loc, so it may be a labelling error.
- **Limits:** the fail-rate features are correlated, so SHAP credit among them is unstable, and the glassbox's coefficients have large opposite signs (`fail_rate` −22, `edge_fail_rate` +13). The rank agreement between SHAP and the glassbox coefficients is only 0.43.

## What sets it apart
- Our own physical features instead of a CNN.
- A harder question than the near-perfect "defect vs none".
- Splits by lot.
- Hyperparameters tuned inside train, so validation answers one question.
- Lot-bootstrap intervals on every comparison.
- Calibration tied to the theoretical threshold.
- Local SHAP next to the wafer map.
- A post-hoc audit of our own model choice.

## Flags
These are the places where the project departs from the brief or is weaker than it looks.

1. **Kaggle usability rating not verified.** Check the rating on the dataset page before presenting.
2. **The source dataset is large** (811,457 maps, 2 GB), against "avoid large datasets".
3. **Feature extraction is preprocessing**, against "avoid data cleaning".
4. **The 5:1 cost ratio is our assumption.** The dataset has no cost data.
5. **The model decision is not a pure validation-AUC ranking.** The blackbox has the highest validation AUC; we chose the glassbox on evaluation loss and interpretability.
6. **On test the blackbox does better** (loss 0.158 vs 0.181, AUC 0.968 vs 0.958); the loss difference isn't distinguishable from zero.
7. **The glassbox's coefficients are hard to read.** Cross-validation chose the weakest penalty in the grid, so all 10 features stay.
8. **Test is worse than validation** (loss 0.181 vs 0.143), as expected when the model and threshold are picked on validation.
9. **Labels are engineers' judgements**, and some look wrong.

## Repository layout
| Path | What it is |
|---|---|
| `Project 2.pdf` | Project brief (lecture slides) |
| `project/Project2_Classification.ipynb` | **The project**: all requirements, with outputs |
| `slides/SLIDES.md` | Outline for the 6 slides, and the link to the deck |
| `slides/Project2_Wafer_Defect_Routing.pptx` | **The presentation**: six slides with speaker notes, built by `slides/build_pptx.js` |
| `slides/deck/` | The six slides as published |
| `slides/figures/` | Slide-sized figures, drawn by `slides/make_slide_figures.py` |
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
2. Rehearse with `slides/Project2_Wafer_Defect_Routing.pptx` and its speaker notes.
3. Decide how to defend the 5:1 cost ratio in the Q&A, or replace it with a figure you can source.
