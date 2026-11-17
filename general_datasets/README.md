# General classification datasets: screening

`Project2_General_Dataset_Screening.ipynb` screens 16 general (non-semiconductor) Kaggle classification datasets against the Project 2 brief, with the same checks on each, and ends with a ranking. It is self-contained and doesn't depend on anything else in this repository.

**Top 5 from the run**

| Rank | Dataset | Rows | Positive rate | Glassbox / blackbox AUC | Threshold saving |
|---|---|---|---|---|---|
| 1 | [Credit Risk](https://www.kaggle.com/datasets/laotse/credit-risk-dataset) | 32,581 | 21.8% | 0.869 / 0.942 | 15% |
| 2 | [Default of Credit Card Clients](https://www.kaggle.com/datasets/uciml/default-of-credit-card-clients-dataset) | 30,000 | 22.1% | 0.726 / 0.782 | 25% |
| 3 | [Online Shoppers Purchasing Intention](https://www.kaggle.com/datasets/imakash3011/online-shoppers-purchasing-intention-dataset) | 12,330 | 15.5% | 0.896 / 0.931 | 31% |
| 4 | [Bank Customer Churn](https://www.kaggle.com/datasets/gauravtopre/bank-customer-churn-dataset) | 10,000 | 20.4% | 0.762 / 0.858 | 26% |
| 5 | [Bank Marketing](https://www.kaggle.com/datasets/henriqueyamahata/bank-marketing) | 41,188 | 11.3% | 0.786 / 0.797 | 38% |

AUCs are untuned 5-fold cross-validation on an 80% development split; the threshold saving is the cost-minimising threshold against 0.5, at each dataset's assumed cost ratio. The reasons and risks for each are in the notebook's last section.

**Files**
- `Project2_General_Dataset_Screening.ipynb`: the screening, with outputs
- `Project2_General_Data_Sanity.ipynb`: data sanity checks for the top 5 only (no models): generic checks plus validity rules written for each dataset, ending with what each needs before modelling
- `screening_results.csv`: every number from the run, one row per dataset

**How to run** (downloads about 30 MB from Kaggle; needs a Kaggle token in `~/.kaggle/kaggle.json`):
```bash
pip install kagglehub pandas numpy scikit-learn scipy shap
```
```bash
cd general_datasets && jupyter nbconvert --to notebook --execute --inplace Project2_General_Dataset_Screening.ipynb
```

**Data sanity scorecard** (from `Project2_General_Data_Sanity.ipynb`, section 6b; ✅ fine · ⚠️ manageable · ❌ needs real work; thresholds are in the notebook)

| Check | Bank Customer Churn | Credit Card Default | Online Shoppers | Credit Risk | Bank Marketing |
|---|---|---|---|---|---|
| ❌ | 0 | 0 | 0 | 0 | 5 |
| ⚠️ | 1 | 4 | 5 | 6 | 5 |
| missing (table) | ✅ 0% | ✅ 0% | ✅ 0% | ⚠️ 1.1% | ⚠️ 1.5% |
| worst column missing | ✅ 0.0% | ✅ 0.0% | ✅ 0.0% | ⚠️ 9.6% (loan_int_rate) | ❌ 20.9% (default) |
| duplicate rows | ✅ 0.0% | ✅ 0.1% | ⚠️ 1.0% | ⚠️ 0.5% | ⚠️ 4.3% |
| conflicting labels | ✅ 0 rows | ⚠️ 46 rows | ✅ 0 rows | ✅ 0 rows | ❌ 542 rows |
| class balance | ✅ 20.4% | ✅ 22.1% | ✅ 15.5% | ✅ 21.8% | ✅ 11.3% |
| validation positives | ✅ 407 | ✅ 1,327 | ✅ 382 | ✅ 1,422 | ✅ 928 |
| impossible / inconsistent rows | ✅ 0 | ✅ 0 | ⚠️ 6 | ⚠️ 7 | ❌ 4,110 |
| undocumented codes | ✅ 0 rows | ⚠️ 399 rows | ✅ 0 rows | ✅ 0 rows | ⚠️ 3 rows |
| spiky columns | ✅ 0 | ⚠️ 9 | ⚠️ 6 | ⚠️ 2 | ⚠️ 3 |
| correlated pairs | ✅ 0 | ⚠️ 6 | ⚠️ 1 | ✅ 0 | ⚠️ 3 |
| leakage | ✅ strongest 0.73 | ✅ strongest 0.69 | ⚠️ PageValues is computed from later purchases | ⚠️ loan_grade / loan_int_rate are the lender's own risk ratings | ❌ duration is known only after the call |
| time drift | ✅ no | ✅ no | ✅ no | ✅ no | ❌ yes |
| looks generated | ⚠️ yes | ✅ no | ✅ no | ✅ no | ✅ no |


**Still to check by hand:** the usability rating on each Kaggle page.
