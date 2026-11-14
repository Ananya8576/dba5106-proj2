# DBA5106 Project 2: two wafer-defect classifiers, compared

**Project 2, Version 2 (with data)**: a classification project presented in at most 6 slides. The brief is in [`Project 2.pdf`](Project%202.pdf).

**What this repository shows.** The same classification pipeline is run on two semiconductor datasets, and the two runs are compared step by step. The pipeline, the search grids, the cost ratio and the decision rule are identical, so any difference in the outcome comes from the data.

| | Run 1 | Run 2 |
|---|---|---|
| Question | Is this wafer's defect cluster **Edge-Loc** (hold the tool) or **Loc** (one-off particle)? | Does this wafer have a **scratch** among its defects? |
| Data | WM-811K, real fab wafer maps | MixedWM38, mixed-type wafer maps |
| Notebook | `project/Project2_Classification.ipynb` | `project/Project2_Classification_Scratch.ipynb` |
| Model chosen | **Glassbox** | **Blackbox** |

**Headline.** The same rule picks the glassbox on one dataset and the blackbox on the other. Where a linear model captures the signal (is the cluster at the edge?), the glassbox is enough. Where it can't (a thin line among other defects), the blackbox is worth its opacity.

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

## 1. Data used
| | Run 1: WM-811K, Edge-Loc vs Loc | Run 2: MixedWM38, Scratch vs not |
|---|---|---|
| Kaggle source | `qingyi/wm811k-wafer-map` | `co1d7era/mixedtype-wafer-defect-datasets` |
| What it is | 811,457 wafer maps from a real fab; 172,950 labelled by engineers with one pattern each | 38,015 wafer maps, all 52 × 52; each labelled with every pattern it contains (38 combinations of 8 patterns) |
| Real or synthetic | Real | Real, plus GAN-generated maps the authors added to balance the classes |
| Rows used | 8,782 wafers labelled Edge-Loc or Loc | 36,991 wafers (all, after dropping duplicate maps) |
| Positive class | Edge-Loc: 59.1% | Label includes Scratch: 48.7% (balanced by the authors, not a fab's real rate) |
| Features | 10 spatial features per map | The same features minus `n_dies`: 9 |
| Grouping | 5,008 lots | None in the dataset |
| Built by | `project/build_features.py` | `project/build_features_mixedwm38.py` |

**The features** are computed from each wafer map by the same function in both runs: fail rate overall and in four zones (centre, middle, edge, outer ring), number of failing clusters, size and radius of the largest cluster, how one-sided the failures are, and the die count.

**The evaluation loss** is the same in both: (5 × missed positives + 1 × false alarms) / wafers. A miss means a tool problem keeps damaging wafers; a false alarm means one unnecessary tool hold. The 5:1 ratio is our assumption.

## 2. Sanity checks
| Check | Run 1: WM-811K | Run 2: MixedWM38 |
|---|---|---|
| Missing cells | 0 | 0 |
| Exact duplicates | 55 duplicate feature rows (0.6%), none with conflicting labels; kept | 1,024 exact duplicate maps, 97.7% of them Scratch; **dropped** |
| Constant features | None | None |
| Shortcut features | None found: no single feature is suspiciously strong (best single-feature AUC 0.892 in the screening) | **`n_dies` gives the label away**: scratch wafers have 2,061–2,065 dies, the others 1,843–2,234. **Deleted** |
| Class balance | 59.1% positive | 48.7% positive (artificial) |
| Wafers per group | Median 1 per lot, up to 25 | No lots |
| Split | 60 / 20 / 20 **by lot**, stratified | 60 / 20 / 20 stratified random |
| Train / validation / test | 5,268 / 1,756 / 1,758 | 22,195 / 7,398 / 7,398 |
| Positives in validation | 1,038 | 3,600 |
| Cleaning done | None: no rows dropped or imputed | Duplicates dropped, one feature deleted |
| Mixed labels | One pattern per wafer | 29,000 wafers carry more than one pattern; 17,000 scratched wafers also carry another |

Both shortcut findings for run 2 came from the screening notebook. With them left in, run 2's screening AUC was 0.917; cleaned and tuned it is 0.881.

## 3. Models compared
The same four models in both runs. Within each row only the training loss changes.

| | L2 loss | Surrogate loss (log loss) |
|---|---|---|
| **Glassbox:** L1-penalised linear model on standardised features | LASSO regression on the 0/1 label | L1 logistic regression |
| **Blackbox:** gradient-boosted trees (scikit-learn `HistGradientBoosting`) | Squared error | Log loss |

**Tuning, identical in both runs.** Each model is tuned separately by 5-fold cross-validated AUC inside the training split: 6 penalty values for the glassbox, tree depth (2, 3, 5) × number of trees (100, 300) for the blackbox. That is 24 configurations per run. Validation is used only to compare the four tuned models and set the threshold. Test is used once.

**Settings chosen by cross-validation**

| Model | Run 1 | Run 2 |
|---|---|---|
| Glassbox, L2 | alpha = 0.0003 | alpha = 0.0003 |
| Glassbox, log loss | C = 10 | C = 10 |
| Blackbox, L2 | depth 3, 300 trees | depth 5, 300 trees |
| Blackbox, log loss | depth 5, 300 trees | depth 5, 300 trees |

**Decision rule, fixed before looking at validation, identical in both runs**
1. Within a model type, take the higher validation AUC; on a tie take log loss, because its output is a probability.
2. Between model types, choose the blackbox only if its validation AUC is distinguishably higher **and** it lowers the evaluation loss by at least 10%. Otherwise choose the glassbox.

## 4. Model comparison
**Validation AUC (95% interval)**

| Model | Train loss | Run 1 | Run 2 |
|---|---|---|---|
| Glassbox | L2 | 0.958 (0.947–0.968) | 0.597 (0.584–0.610) |
| Glassbox | Log loss | **0.966** (0.957–0.974) | **0.654** (0.641–0.666) |
| Blackbox | L2 | 0.966 (0.954–0.975) | 0.879 (0.871–0.886) |
| Blackbox | Log loss | **0.972** (0.963–0.980) | **0.881** (0.874–0.888) |

**Training AUC, to show why models are compared on validation**

| Model | Run 1: train → validation | Run 2: train → validation |
|---|---|---|
| Glassbox, log loss | 0.969 → 0.966 | 0.647 → 0.654 |
| Blackbox, log loss | 1.000 → 0.972 | 0.930 → 0.881 |

**The judgement checks**

| Check | Run 1 | Run 2 |
|---|---|---|
| Log loss − L2, glassbox | +0.008 (CI +0.003 to +0.014) | +0.057 (CI +0.050 to +0.064) |
| Log loss − L2, blackbox | +0.007 (CI +0.003 to +0.011) | +0.002 (CI −0.0005 to +0.005): a tie |
| L2 scores outside 0–1, glassbox / blackbox | 20% / 29% | 0% / 10% |
| Blackbox − glassbox AUC | +0.006 (CI +0.0001 to +0.012) | +0.227 (CI +0.215 to +0.241) |
| Evaluation loss at best threshold, glassbox / blackbox | 0.143 / 0.149 | 0.512 / 0.328 |
| Does the blackbox cut the cost by 10%? | No: it is 4% higher | Yes: 36% lower |
| **Model chosen** | **Glassbox, log loss** | **Blackbox, log loss** |
| Cost ratios (1 to 10) where the choice holds | 3 to 8 | All |

In run 2 the glassbox's best loss (0.512) equals the cost of holding the tool for every wafer (0.513), so it adds nothing.

## 5. Results comparison
**Threshold (validation)**

| | Run 1 | Run 2 |
|---|---|---|
| Threshold that minimises the evaluation loss (raw score) | 0.28 | 0.175 |
| Evaluation loss at 0.5 → at that threshold | 0.196 → 0.143 (−27%) | 0.595 → 0.328 (−45%) |
| Missed positives, 0.5 → tuned | 49 → 18 | 714 → 68 |
| False alarms, 0.5 → tuned | 99 → 161 | 835 → 2,088 |
| Accuracy, 0.5 → tuned | 91.6% → 89.8% | 79.1% → 70.9% |

In both runs accuracy falls while the cost falls, which is why the evaluation loss, not accuracy, drives the decision.

**Calibration (validation)**

| | Run 1 | Run 2 |
|---|---|---|
| Calibration error (ECE) of the chosen model | 0.031 | 0.013 |
| Fix kept (fitted on out-of-fold training scores) | Isotonic regression | Platt scaling |
| ECE after the fix; AUC | 0.021; unchanged | 0.009; unchanged |
| Worst-calibrated model of the four | Glassbox, L2 (0.107) | Glassbox, L2 (0.048) |
| Best threshold on calibrated probabilities vs theory (0.167) | 0.22 | 0.155 |

**Tree SHAP on the log-loss boosted trees (validation)**

| | Run 1 | Run 2 |
|---|---|---|
| Top features (mean absolute SHAP) | `largest_cluster_radius` 4.0, `edge_fail_rate` 1.8, `outer_ring_fail_rate` 0.9 | `edge_fail_rate` 1.2, `outer_ring_fail_rate` 1.0, `n_fail_clusters` 0.7 |
| Does it match the physics? | Yes: it asks whether the cluster is at the edge | No: no feature describes a line, and the model reads side effects |
| Most confident positive | Cluster at the edge (radius 0.93) | A Donut + Edge-Ring + Loc + Scratch wafer with no visible line |
| Costliest mistake | A wafer labelled Edge-Loc with its cluster near the centre: probably a labelling error | An Edge-Loc + Scratch wafer scored 0.013 |
| Agreement with the glassbox's coefficients (rank correlation) | 0.43 | −0.15 |

**Test split, used once**

| | Run 1 | Run 2 |
|---|---|---|
| AUC (95% CI) | 0.958 (0.946–0.969) | 0.882 (0.874–0.889) |
| Evaluation loss per wafer (95% CI) | 0.181 (0.143–0.223) | 0.330 (0.316–0.345) |
| Loss from holding every wafer | 0.409 | 0.513 |
| Saving against holding every wafer | 56% | 36% |
| Recall / precision / accuracy | 97.3% / 85.0% / 88.3% | 98.4% / 62.1% / 70.0% |
| Validation → test loss | 0.143 → 0.181 | 0.328 → 0.330 |
| Audit: the model not chosen, on test | Blackbox 0.158, slightly better (difference −0.023, CI −0.051 to +0.007) | Glassbox 0.513, far worse (difference +0.183, CI +0.168 to +0.197) |

The loss levels are not comparable between runs, because run 2's 49% positive rate is artificial. The patterns are.

**What the comparison shows**
- **The same rule gives opposite model choices**, for a reason that can be explained: a linear model captures "edge vs interior" but not "a thin line among other defects".
- **Log loss beats or ties L2 in every case.** It never loses, and the L2 versions give scores outside 0–1.
- **Tuning the threshold pays off in both runs**, and more where the model is weaker.
- **Better calibration puts the searched threshold closer to the theoretical one** (0.155 in run 2, 0.22 in run 1, against 0.167).
- **A larger validation split removes most of the gap between validation and test** (7,398 wafers in run 2 against 1,756 in run 1).
- **A high AUC does not mean the model has learned the right thing.** Run 2's SHAP shows it reads edge fail rates, not scratches.

## 6. Flags
These are the places where the work departs from the brief or is weaker than it looks.

**Both runs**
1. **Kaggle usability ratings not verified.** Kaggle's API needs a login. Check both dataset pages before presenting.
2. **The 5:1 cost ratio is our assumption.** Neither dataset has cost data.
3. **Feature extraction is preprocessing**, against the brief's "avoid data cleaning".
4. **The brief allows at most 6 slides.** There is one 6-slide deck per run, so presenting both in full would exceed it.

**Run 1 (WM-811K)**
5. **The source dataset is large** (811,457 maps, 2 GB), against "avoid large datasets". The run uses an 8,782-wafer subset.
6. **The model decision is not a pure validation-AUC ranking.** The blackbox has the highest validation AUC; the glassbox was chosen on evaluation loss and interpretability.
7. **On test the blackbox does slightly better** (loss 0.158 vs 0.181); the difference isn't distinguishable from zero.
8. **The glassbox's coefficients are hard to read.** All 10 features stay, and correlated ones get large opposite-sign coefficients.
9. **Test is worse than validation** (0.181 vs 0.143), as expected when the model and threshold are picked on validation.
10. **Labels are engineers' judgements**, and some look wrong.

**Run 2 (MixedWM38)**
11. **The model does not look at the scratch.** It has probably learned which mixes of patterns come with the Scratch label in this dataset, which would not transfer to a fab.
12. **The class balance is artificial**, partly from GAN-generated maps.
13. **One feature had to be deleted and 1,024 duplicates dropped** before the task was honest.
14. **The blackbox search ended at the edge of its grid** (depth 5, 300 trees). The grid was kept identical to run 1 for comparability.
15. **Random split, not by lot.** Near-duplicate generated maps could sit in different splits.

## 7. How the two datasets were chosen
Both come from screening 15 candidates in `EDA/Project2_Dataset_EDA.ipynb`, which runs the same checks on each. The two semiconductor datasets that ranked first and second became the two runs. The screening used untuned models and random splits; the project notebooks tune the models and, where lots exist, split by lot.

### Datasets screened
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
| K | MixedWM38 mixed-type wafer maps, Scratch vs not | Kaggle `co1d7era/mixedtype-wafer-defect-datasets` | Rank 2, **cleaned version only**. Modelled end to end as the comparison run |
| M | Semiconductor wafer fault detection | Kaggle `krishujeniya/semiconductor-wafer-fault-detection-dataset` | Excluded: all 1,537 labelled rows are SECOM rows (dataset I) |
| N | Wafer dataset (batch files) | Kaggle `himanshunayal/waferdataset` | Excluded: the same wafers as M, as raw batch files |
| L | Semiconductor sensor data (simulated) | Kaggle `programmer3/semiconductor-sensor-data-for-predictive-quality` | Not assessed: Kaggle returned 403 |

Round 4 also found four image datasets: three are pictures of the WM-811K wafers already in D (`vinishraghavke/wafer-defect-classification-dataset`, `sushnu/wm-811k-augmented-and-preprocessed-dataset`, `muhammedjunayed/wm811k-silicon-wafer-map-dataset-image`), and one is 625 SEM photographs in 12 classes (`cagrant/long-tailed-sem-wafer-defect-dataset`). None is tabular, so none is a candidate.

The wafer-map datasets (D, D2, K) are turned into 10 named spatial features per wafer (zone fail rates, cluster size and radius, angular concentration), so tabular models and tree SHAP apply.

### Checks run on each dataset
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

### Ranking from the screening
| Rank | Dataset | Evidence | Main risk |
|---|---|---|---|
| **1** | **D2 · WM-811K Edge-Loc vs Loc** (semiconductor, real) | All checks pass except preprocessing. 1,038 validation positives (AUC ± 0.005). Glassbox 0.963 vs blackbox 0.974; the gap (+0.011, sd 0.002) is stable. Best threshold 0.26 ≈ cost-ratio threshold 0.25. The L2 glassbox is clearly worse calibrated (ECE 0.10 vs 0.027). SHAP top `largest_cluster_radius` (44%), physically meaningful. | The small gap makes the decision "choose the glassbox". Needs the 2 GB legacy pickle and feature extraction. |
| **2** | **K · MixedWM38 Scratch, cleaned** (semiconductor) | The artefact check confirmed `n_dies` is a shortcut: Scratch wafers have 2,061–2,065 dies (sd 0.6), others 1,843–2,234 (sd 21.7). The 1,024 duplicate rows are 97.7% Scratch. After deduplicating and dropping `n_dies`: glassbox 0.617 vs blackbox 0.876, the largest gap of any candidate. | The tuned model reads edge fail rates, not the scratch (section 5). The 49% prevalence is artificial (GAN balancing). |
| **3** | **E · Steel plates, Bumps vs rest** (real, not semiconductor) | No cleaning, no missing data. Glassbox 0.839 vs blackbox 0.923 (+0.085, sd 0.017). Threshold saving 77%. SHAP spread out (top feature 11%). | Not semiconductor. Correlated pairs (use LASSO). About 8 validation positives per calibration bin. |
| 4 | A · AI4I | Gap +0.077 (sd 0.015); a glassbox with physics features reaches 0.914. | Synthetic, 3.4% positive, 27 contradictory labels, heavily used on Kaggle. |
| 5 | G · Manufacturing defects | No flags. Gap +0.071. | Threshold saving 4%, synthetic, defects are the 84% majority. |
| 6 | F · Machine failure | Clean. | The glassbox beats the blackbox (the blackbox wins in 4% of draws); `VOC` carries 42% of SHAP. |
| 7 | D · WM-811K, any pattern vs none | Stable. | Near-perfect (0.995). Superseded by D2. |

The flag-count summary in the notebook puts G first. The ranking above also weighs the model-decision story, the threshold story, real vs synthetic data, and semiconductor relevance. The full reasoning is in the last cell of the notebook.

### How to run the screening notebook
```bash
pip install kagglehub pandas numpy scikit-learn scipy matplotlib shap requests
```

1. Put a Kaggle API token in `~/.kaggle/kaggle.json`, or download datasets by hand and set the matching `*_DIR` environment variable (for example `STEEL_DIR`, `WM_DIR`, `MIXED_DIR`). The full list is in `LOCAL_DIRS` in the setup cell.
2. Run all cells. A dataset that fails to load is skipped, and the scorecard is built from whatever loaded.
3. WM-811K needs several GB of RAM to load the full pickle.

## 8. Slides
| Run | PowerPoint | Outline | Online deck |
|---|---|---|---|
| Run 1: Edge-Loc vs Loc | `slides/Project2_Wafer_Defect_Routing.pptx` | `slides/SLIDES.md` | Link in the outline |
| Run 2: Scratch vs not | `slides/Project2_Scratch_Detection.pptx` | `slides/SLIDES_SCRATCH.md` | Link in the outline |

Each deck has six slides with speaker notes. The last slide of the run 2 deck is the side-by-side comparison.

## 9. Repository layout
| Path | What it is |
|---|---|
| `Project 2.pdf` | Project brief (lecture slides) |
| `project/Project2_Classification.ipynb` | Run 1, with outputs |
| `project/Project2_Classification_Scratch.ipynb` | Run 2, with outputs and the side-by-side table |
| `project/build_features.py`, `project/build_features_mixedwm38.py` | Build each run's feature table and wafer maps from the Kaggle files |
| `project/data/` | Feature tables and wafer maps for both runs |
| `project/figures/`, `project/figures_scratch/` | Figures saved by each notebook |
| `project/results_summary.json`, `project/results_summary_scratch.json` | Key results of each run |
| `slides/` | Both PowerPoint files, their outlines, the published deck sources (`deck/`, `deck_scratch/`), slide-sized figures (`figures/`, `figures_scratch/`) and the scripts that build them |
| `EDA/Project2_Dataset_EDA.ipynb` | Dataset screening: 15 candidates, the same checks on each, and the ranking |
| `EDA/output.csv` | Scorecard export from the first screening run (A–J only) |

## 10. How to run
```bash
pip install pandas numpy scikit-learn scipy matplotlib shap
```
Run 1 (about 2 minutes):
```bash
cd project && jupyter nbconvert --to notebook --execute --inplace Project2_Classification.ipynb
```
Run 2 (about 4 minutes):
```bash
cd project && jupyter nbconvert --to notebook --execute --inplace Project2_Classification_Scratch.ipynb
```
Both notebooks read `project/data/`, so they don't need Kaggle. To rebuild that data from the source files (needs `kagglehub`; run 1 needs several GB of RAM):
```bash
python project/build_features.py
```
```bash
python project/build_features_mixedwm38.py
```

## Next steps
1. Check the Kaggle usability ratings for `qingyi/wm811k-wafer-map` and `co1d7era/mixedtype-wafer-defect-datasets`.
2. Decide how to fit two runs into the brief's 6 slides: present one deck and use the other's comparison slide, or cut both down.
3. Decide how to defend the 5:1 cost ratio in the Q&A, or replace it with a figure you can source.
