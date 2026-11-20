# DBA5106 Project 2: steel scratch triage

**Project 2, Version 2 (with data)**: a classification project presented in at most 6 slides. The brief is in [`Project 2.pdf`](Project%202.pdf).

The [final project](final/steel-scratch-triage/README.md) uses Faulty Steel Plates to prioritize known faults for scratch review. Its dataset, notebook, results, and slides are in `final/steel-scratch-triage/`.

The repository also holds **two earlier independent projects** on semiconductor wafer maps, plus a separate screening of general classification datasets (see "General classification datasets" below). Each was designed for its own question: its own features, cost ratio, search grids and decision. Neither notebook refers to the other. They are compared only in the last section of this page, after both were finished.

| | Project A | Project B |
|---|---|---|
| Question | Is this wafer's defect cluster **Edge-Loc** (hold the tool) or **Loc** (one-off particle)? | Does this wafer have a **scratch** among its defects? |
| Data | WM-811K, real fab wafer maps | MixedWM38, mixed-type wafer maps |
| Notebook | `old/project/Project2_Classification.ipynb` | `old/project/Project2_Classification_Scratch.ipynb` |
| Slides | `slides/Project2_Wafer_Defect_Routing.pptx` | `slides/Project2_Scratch_Detection.pptx` |

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

# Project A: Edge-Loc vs Loc on WM-811K

## A1. Data used
| | |
|---|---|
| Kaggle source | `qingyi/wm811k-wafer-map` (usability 5.0 out of 10) |
| What it is | 811,457 wafer maps from a real fab; 172,950 labelled by engineers with one pattern each |
| Rows used | 8,782 wafers labelled Edge-Loc or Loc |
| Positive class | Edge-Loc: 59.1% |
| Features | 10 spatial features per map: die count, fail rate overall and in four zones, number of failing clusters, size and radius of the largest cluster, how one-sided the failures are |
| Grouping | 5,008 lots |
| Built by | `old/project/build_features.py` |

**Decision supported.** Edge-Loc points to a tool's edge process drifting, so the tool is held. Loc is a one-off particle. **Evaluation loss:** (5 × missed Edge-Loc + 1 × false alarm) / wafers. The 5:1 ratio is an assumption.

## A2. Sanity checks
| Check | Result |
|---|---|
| Missing cells | 0 |
| Duplicates | 55 duplicate feature rows (0.6%), none with conflicting labels; kept |
| Constant features | None |
| Leakage | No single feature is suspiciously strong (best single-feature AUC 0.892 in the screening) |
| Class balance | 59.1% positive; 1,038 positives in validation |
| Split | 60 / 20 / 20 **by lot**, stratified: 5,268 / 1,756 / 1,758 wafers |
| Cleaning | None: no rows dropped or imputed |

## A3. Models
| | L2 loss | Surrogate loss (log loss) |
|---|---|---|
| **Glassbox:** L1-penalised linear model | LASSO regression on the 0/1 label | L1 logistic regression |
| **Blackbox:** gradient-boosted trees | Squared error | Log loss |

- **Tuning:** each model separately, by 5-fold cross-validated AUC inside the training split (folds by lot). 6 penalty values for the glassbox; depth (2, 3, 5) × trees (100, 300) for the blackbox. 24 configurations.
- **Decision rule, fixed in advance:** choose the blackbox only if its validation AUC is distinguishably higher and it lowers the evaluation loss by at least 10%.

## A4. Model comparison (validation)
| Model | Train loss | Chosen setting | Training AUC | Validation AUC (95% CI) |
|---|---|---|---|---|
| Glassbox | L2 | alpha = 0.0003 | 0.960 | 0.958 (0.947–0.968) |
| Glassbox | Log loss | C = 10 | 0.969 | **0.966** (0.957–0.974) |
| Blackbox | L2 | depth 3, 300 trees | 0.988 | 0.966 (0.954–0.975) |
| Blackbox | Log loss | depth 5, 300 trees | 1.000 | **0.972** (0.963–0.980) |

- Log loss beats L2 for both: +0.008 (glassbox) and +0.007 (blackbox); both intervals exclude zero.
- The blackbox's AUC is +0.006 higher (CI +0.0001 to +0.012), but its evaluation loss is not lower: 0.149 vs 0.143.
- **Chosen: the glassbox, L1 logistic regression.**

## A5. Results
| Step | Result |
|---|---|
| Threshold (validation) | 0.28 on the raw score. Loss 0.196 → 0.143 (−27%) against 0.5; accuracy 91.6% → 89.8% |
| Calibration (validation) | ECE 0.031 → 0.021 with isotonic regression fitted on out-of-fold training scores; AUC unchanged. Calibrated threshold 0.22 against the theoretical 0.167 |
| Tree SHAP (on the boosted trees) | `largest_cluster_radius` 4.0, `edge_fail_rate` 1.8, `outer_ring_fail_rate` 0.9. The model asks whether the cluster is at the edge |
| Test, used once | AUC 0.958 (0.946–0.969); loss 0.181 per wafer (0.143–0.223), 56% below holding every wafer (0.409); recall 97.3%, precision 85.0%, accuracy 88.3% |
| Audit of the choice | The blackbox scores 0.158 on test, slightly better; the difference (−0.023, CI −0.051 to +0.007) isn't distinguishable from zero |

## A6. Flags
1. **Kaggle usability is 5.0 out of 10.** The brief says to find a high-usability dataset; this one is not.
2. **The source dataset is large** (811,457 maps, 2 GB), against "avoid large datasets". The project uses an 8,782-wafer subset.
3. **Feature extraction is preprocessing**, against "avoid data cleaning".
4. **The 5:1 cost ratio is an assumption.**
5. **The decision is not a pure validation-AUC ranking.** The blackbox has the highest AUC; the glassbox was chosen on evaluation loss and interpretability.
6. **On test the blackbox does slightly better** (0.158 vs 0.181); not distinguishable from zero.
7. **The glassbox's coefficients are hard to read.** All 10 features stay, and correlated ones get large opposite-sign coefficients.
8. **Test is worse than validation** (0.181 vs 0.143).
9. **Labels are engineers' judgements**, and some look wrong.

# Project B: scratch detection on MixedWM38

## B1. Data used
| | |
|---|---|
| Kaggle source | `co1d7era/mixedtype-wafer-defect-datasets` (usability 7.5 out of 10) |
| What it is | 38,015 wafer maps, all 52 × 52; each labelled with every pattern it contains (38 combinations of 8 patterns). Real maps plus generated ones the authors added to balance the classes |
| Rows used | 36,991 wafers, after dropping duplicate maps |
| Positive class | Label includes Scratch: 48.7% (balanced by the authors, not a fab's real rate) |
| Features | 16: nine background features (fail rates by zone, clusters) and **seven line features** built for this question (thin structures, lined-up failing dies, straight-line evidence) |
| Grouping | None in the dataset |
| Built by | `old/project/build_features_mixedwm38.py` |

**Decision supported.** A scratch comes from mechanical contact and repeats until the handler is fixed; dies next to it can pass test and fail later. A flag holds the handling path and sends the wafer to neighbour-die screening. **Evaluation loss:** (10 × missed scratch + 1 × false alarm) / wafers. A miss carries a repeating cost and a reliability cost. The 10:1 ratio is an assumption.

## B2. Sanity checks
| Check | Result |
|---|---|
| Missing cells | 0 |
| Duplicates | 1,024 exact duplicate maps, 97.7% of them scratched; **dropped** |
| Die count | Scratched wafers have 2,061–2,065 dies; unscratched ones range from 1,843 to 2,234, and 5.2% of them have a count no scratched wafer has. No physical link to a scratch, so it is **not used as a feature** |
| Position | Scratches in these maps tend to sit in the same region. Position is **left out of the features** on purpose |
| Class balance | 48.7% positive (artificial); 3,600 positives in validation |
| Split | 60 / 20 / 20 stratified random: 22,195 / 7,398 / 7,398 wafers |
| Signal check (training split) | The seven line features are the seven strongest single features (AUC 0.63–0.73); no background feature exceeds 0.58 |
| Mixed labels | 29,000 wafers carry more than one pattern; 17,000 scratched wafers also carry another |

## B3. Models
| | L2 loss | Surrogate loss (log loss) |
|---|---|---|
| **Glassbox:** L1-penalised linear model | LASSO regression on the 0/1 label | L1 logistic regression |
| **Blackbox:** gradient-boosted trees | Squared error | Log loss |

- **Tuning:** each model separately, by 5-fold cross-validated AUC inside the training split. 7 penalty values for the glassbox; depth (3, 5, 8) × trees (200, 500, 1,000) for the blackbox. 32 configurations.
- **Decision rule, fixed in advance:** choose the blackbox only if its validation AUC is distinguishably higher and it lowers the evaluation loss by at least 10%.

## B4. Model comparison (validation)
| Model | Train loss | Chosen setting | Training AUC | Validation AUC (95% CI) |
|---|---|---|---|---|
| Glassbox | L2 | alpha = 0.0001 | 0.886 | 0.885 (0.878–0.892) |
| Glassbox | Log loss | C = 100 | 0.910 | **0.909** (0.902–0.915) |
| Blackbox | L2 | depth 8, 500 trees | 0.984 | 0.958 (0.954–0.962) |
| Blackbox | Log loss | depth 8, 200 trees | 0.989 | **0.963** (0.959–0.967) |

- Log loss beats L2 for both: +0.024 (glassbox) and +0.005 (blackbox); both intervals exclude zero.
- The blackbox's AUC is +0.054 higher (CI +0.049 to +0.060), and it lowers the evaluation loss by 38%: 0.250 vs 0.406.
- **Chosen: the blackbox, boosted trees with log loss.** The choice holds for every cost ratio from 1 to 20.

## B5. Results
| Step | Result |
|---|---|
| Threshold (validation) | 0.117 on the raw score. Loss 0.613 → 0.250 (−59%) against 0.5; accuracy 89.1% → 81.2%; misses 414 → 51, false alarms 395 → 1,339 |
| Calibration (validation) | ECE 0.011 → 0.009 with Platt scaling fitted on out-of-fold training scores; AUC unchanged. Calibrated threshold 0.105 against the theoretical 0.091 |
| Tree SHAP (on the chosen model) | `outer_ring_fail_rate` 1.9, `thin_fail_rate` 1.4, `line_score_top20` 1.2. The seven line features carry 49% of the attribution |
| Local SHAP | Most confident scratch: a scratch-only wafer with a visible line, led by line features. Costliest mistake: a wafer where large blobs hide the scratch |
| Test, used once | AUC 0.961 (0.957–0.964); loss 0.263 per wafer (0.242–0.286), 49% below flagging every wafer (0.513); recall 98.4%, precision 72.3%, accuracy 80.8% |
| Audit of the choice | The glassbox scores 0.426 on test, 0.162 worse (CI +0.134 to +0.191) |

## B6. Flags
1. **Half of the model's attribution is background, and the top feature is `outer_ring_fail_rate`.** Some of that is legitimate context; some may be which other patterns come with a Scratch label in this dataset.
2. **The class balance is artificial**, partly from generated maps, so the cost per wafer is not a forecast for a fab.
3. **Cleaning and feature extraction were needed**, against "avoid data cleaning".
4. **The 10:1 cost ratio is an assumption.**
5. **Two searches ended at the edge of their grids** (blackbox depth 8; glassbox weakest penalty, so all 16 features stay).
6. **This test split had been scored once before**, by an earlier version with a different feature set. The current features and grids were designed on the training split.
7. **Random split**, because the dataset has no lot information.
8. **Kaggle usability is 7.5 out of 10.**

# Comparison, made after both projects were finished
Nothing in this section fed back into either project.

| | Project A: Edge-Loc vs Loc | Project B: Scratch vs not |
|---|---|---|
| Data | Real fab maps; 8,782 wafers; 59% positive | Real + generated maps; 36,991 wafers; 49% positive (artificial) |
| Kaggle usability | 5.0 | 7.5 |
| Cleaning needed | None | Duplicates dropped; die count withheld |
| Features | 10 general spatial features | 9 background + 7 line features |
| Cost ratio (miss : false alarm) | 5 : 1 | 10 : 1 |
| Configurations tried | 24 | 32 |
| Validation AUC, glassbox L2 / log loss | 0.958 / 0.966 | 0.885 / 0.909 |
| Validation AUC, blackbox L2 / log loss | 0.966 / 0.972 | 0.958 / 0.963 |
| Log loss − L2, glassbox / blackbox | +0.008 / +0.007 | +0.024 / +0.005 |
| Blackbox − glassbox AUC | +0.006 | +0.054 |
| Does the blackbox cut the cost by 10%? | No (4% higher) | Yes (38% lower) |
| **Model chosen** | **Glassbox** | **Blackbox** |
| Threshold; saving against 0.5 | 0.28; −27% | 0.117; −59% |
| Calibration error, before → after | 0.031 → 0.021 (isotonic) | 0.011 → 0.009 (Platt) |
| Calibrated threshold vs theory | 0.22 vs 0.167 | 0.105 vs 0.091 |
| Top SHAP feature | `largest_cluster_radius` | `outer_ring_fail_rate`, then two line features |
| Test AUC | 0.958 | 0.961 |
| Test loss, against flagging every wafer | 0.181 vs 0.409 (−56%) | 0.263 vs 0.513 (−49%) |
| Validation → test loss | 0.143 → 0.181 | 0.250 → 0.263 |
| Audit: the model not chosen, on test | Slightly better, not distinguishable | Clearly worse |

The loss levels can't be compared directly: the cost ratios differ and project B's positive rate is artificial. The patterns can.

**What the comparison shows**
- **Each project reached its own model choice.** In A a linear model captures the signal (is the cluster at the edge?), so the blackbox adds too little to justify itself. In B the scratch evidence interacts with the background, and the blackbox cuts the cost by more than a third.
- **Log loss beat L2 in all four cases**, and every L2 model gave some scores outside 0–1.
- **Tuning the threshold to the evaluation loss paid off in both**, at the price of lower accuracy in both.
- **Both chosen models were close to calibrated**, and in both the searched threshold landed near the theoretical one.
- **The larger validation split in B left a smaller gap between validation and test.**
- **A is the cleaner story to defend:** real data, no cleaning, and an explanation that matches the physics. **B has the stronger modelling result**, with caveats about generated data and background features.

# General dataset screening

The screening in `general/` compared 17 Kaggle classification datasets. It evaluated Faulty Steel Plates as **Bumps vs. other faults**. The final steel project uses **scratch vs. other faults**.

- `general/Project2_General_Dataset_Screening.ipynb` ranks the 17 datasets.
- `general/Project2_General_Data_Sanity.ipynb` runs data sanity checks for the top six.
- `general/screening_results.csv` contains the screening results.

**Data sanity scorecard for the top 6** (✅ fine · ⚠️ manageable · ❌ needs real work; thresholds are in the sanity notebook, section 6b)

| Check | Bank Customer Churn | Credit Card Default | Steel Plates (Bumps) | Online Shoppers | Credit Risk | Bank Marketing |
|---|---|---|---|---|---|---|
| ❌ | 0 | 0 | 0 | 0 | 0 | 5 |
| ⚠️ | 1 | 4 | 4 | 5 | 6 | 5 |
| missing (table) | ✅ 0% | ✅ 0% | ✅ 0% | ✅ 0% | ⚠️ 1.1% | ⚠️ 1.5% |
| worst column missing | ✅ 0.0% | ✅ 0.0% | ✅ 0.0% | ✅ 0.0% | ⚠️ 9.6% (loan_int_rate) | ❌ 20.9% (default) |
| duplicate rows | ✅ 0.0% | ✅ 0.1% | ✅ 0.0% | ⚠️ 1.0% | ⚠️ 0.5% | ⚠️ 4.3% |
| conflicting labels | ✅ 0 rows | ⚠️ 46 rows | ✅ 0 rows | ✅ 0 rows | ✅ 0 rows | ❌ 542 rows |
| class balance | ✅ 20.4% | ✅ 22.1% | ✅ 20.7% | ✅ 15.5% | ✅ 21.8% | ✅ 11.3% |
| validation positives | ✅ 407 | ✅ 1,327 | ⚠️ 80 | ✅ 382 | ✅ 1,422 | ✅ 928 |
| impossible / inconsistent rows | ✅ 0 | ✅ 0 | ⚠️ 2 | ⚠️ 6 | ⚠️ 7 | ❌ 4,110 |
| undocumented codes | ✅ 0 rows | ⚠️ 399 rows | ✅ 0 rows | ✅ 0 rows | ✅ 0 rows | ⚠️ 3 rows |
| spiky columns | ✅ 0 | ⚠️ 9 | ⚠️ 5 | ⚠️ 6 | ⚠️ 2 | ⚠️ 3 |
| correlated pairs | ✅ 0 | ⚠️ 6 | ⚠️ 7 | ⚠️ 1 | ✅ 0 | ⚠️ 3 |
| leakage | ✅ strongest 0.73 | ✅ strongest 0.69 | ✅ strongest 0.69 | ⚠️ PageValues is computed from later purchases | ⚠️ loan_grade / loan_int_rate are the lender's own risk ratings | ❌ duration is known only after the call |
| time drift | ✅ no | ✅ no | ✅ no | ✅ no | ✅ no | ❌ yes |
| looks generated | ⚠️ yes | ✅ no | ✅ no | ✅ no | ✅ no | ✅ no |

**Reading it**
- **Missing values:** only Credit Risk (interest rate, 9.6%) and Bank Marketing ("unknown" entries, worst in `default` at 20.9%) have any.
- **Bank Marketing** has the most problems: a column known only after the call, rows in time order with strong drift, and 542 rows with conflicting labels.
- **Bank Customer Churn** has the fewest marks, but looks generated and is the course's own example.
- **Faulty Steel Plates** is the cleanest of the real datasets (no missing values, duplicates or conflicting labels). Its limits: about 80 validation positives, and the file is sorted by fault type, so it must be shuffled.
- **Strongest candidates:** Faulty Steel Plates (clean real data, a large stable model gap and the biggest threshold saving, but small), Default of Credit Card Clients (real data, light cleaning) and Credit Risk (clear model gap, one column to impute).
- **Still to check by hand:** the Kaggle usability rating of each.

## Slides
| Project | PowerPoint | Outline | Online deck |
|---|---|---|---|
| A: Edge-Loc vs Loc | `slides/Project2_Wafer_Defect_Routing.pptx` | `slides/SLIDES.md` | Link in the outline |
| B: Scratch vs not | `slides/Project2_Scratch_Detection.pptx` | `slides/SLIDES_SCRATCH.md` | Link in the outline |

Each deck has six slides with speaker notes and covers its own project only. The brief allows at most 6 slides, so the two decks can't both be presented in full.

## Repository layout
| Path | What it is |
|---|---|
| `Project 2.pdf` | Project brief (lecture slides) |
| `old/project/Project2_Classification.ipynb` | Project A, with outputs |
| `old/project/Project2_Classification_Scratch.ipynb` | Project B, with outputs |
| `old/project/build_features.py`, `old/project/build_features_mixedwm38.py` | Build each project's feature table and wafer maps from the Kaggle files |
| `old/project/data/` | Feature tables and wafer maps for both projects, and project B's cleaning report |
| `old/project/figures/`, `old/project/figures_scratch/` | Figures saved by each notebook |
| `old/project/results_summary.json`, `old/project/results_summary_scratch.json` | Key results of each project |
| `slides/` | Both PowerPoint files, their outlines, the published deck sources (`deck/`, `deck_scratch/`), slide-sized figures (`figures/`, `figures_scratch/`) and the scripts that build them |
| `final/steel-scratch-triage/` | Final Faulty Steel Plates dataset, scratch-triage analysis, results, and slides |
| `general/` | General dataset screening and sanity checks |
| `old/EDA/Project2_Dataset_EDA.ipynb` | Dataset screening: 15 candidates, the same checks on each, and the ranking |
| `old/EDA/output.csv` | Scorecard export from the first screening run (A–J only) |

## How to run
```bash
pip install pandas numpy scikit-learn scipy matplotlib shap
```
Project A (about 2 minutes):
```bash
cd old/project && jupyter nbconvert --to notebook --execute --inplace Project2_Classification.ipynb
```
Project B (about 5 minutes):
```bash
cd old/project && jupyter nbconvert --to notebook --execute --inplace Project2_Classification_Scratch.ipynb
```
Both notebooks read `old/project/data/`, so they don't need Kaggle. To rebuild that data from the source files (needs `kagglehub`; project A needs several GB of RAM):
```bash
python old/project/build_features.py
```
```bash
python old/project/build_features_mixedwm38.py
```

## Next steps
1. Decide which project to present within the brief's 6 slides, or how to cut the two decks down to fit.
2. Decide how to defend each cost ratio in the Q&A, or replace it with a figure you can source.
3. For project A, be ready for the usability question: the dataset scores 5.0 out of 10.

## Appendix: how the two datasets were chosen
Both come from screening 15 candidates in `old/EDA/Project2_Dataset_EDA.ipynb`, which runs the same checks on each. The two semiconductor datasets that ranked first and second became the two runs. The screening used untuned models and random splits; the project notebooks tune the models and, where lots exist, split by lot.

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
| **2** | **K · MixedWM38 Scratch, cleaned** (semiconductor) | The artefact check confirmed `n_dies` is a shortcut: Scratch wafers have 2,061–2,065 dies (sd 0.6), others 1,843–2,234 (sd 21.7). The 1,024 duplicate rows are 97.7% Scratch. After deduplicating and dropping `n_dies`: glassbox 0.617 vs blackbox 0.876, the largest gap of any candidate. | The screening used general features only. The 49% prevalence is artificial (GAN balancing). |
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

