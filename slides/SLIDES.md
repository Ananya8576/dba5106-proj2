# Slide outline (6 slides, 15 minutes)

Every number below comes from `project/Project2_Classification.ipynb`.

- **Deck:** https://claude.ai/artifact/S4n1WdZDCnKSmxF778twG2 (private until shared; download as PowerPoint or PDF from its Share menu).
- **PowerPoint file:** `Project2_Wafer_Defect_Routing.pptx`, built by `build_pptx.js`. Same six slides and speaker notes as the deck.
- **Deck source:** `deck/` holds the six slides as published.
- **Slide figures:** `figures/`, drawn by `make_slide_figures.py` from the notebook's own numbers. The figure names below (`03_auc_intervals.png` and so on) are the notebook's versions in `project/figures/`.

## Slide 1: The decision, the data, the loss
- **Decision:** a wafer shows a local cluster of failing dies. Is it **Edge-Loc** (a tool's edge process is drifting: hold the tool) or **Loc** (a one-off particle: normal review)?
- **Data:** WM-811K, real fab wafer maps. 8,782 wafers labelled Edge-Loc (59%) or Loc. We turned each map into 10 physical features (where the failures are, how clustered).
- **Evaluation loss:** a missed Edge-Loc costs 5 unnecessary tool holds. Loss = (5·FN + FP) / n. This is our assumption; slide 4 shows other ratios.
- **Why not "defect vs no defect"?** It's almost perfectly predictable (AUC 0.995), so we changed the question.
- Figure: two wafer maps (crop from `09_shap_local.png`), one of each class.

## Slide 2: Four models, one fair comparison
- Glassbox: L1-penalised linear model. Blackbox: gradient-boosted trees. Each trained with **L2 loss** and with **log loss**; only the loss changes.
- Split **by lot** 60 / 20 / 20. Tuned separately by cross-validation inside train: 24 configurations in total.
- Validation AUC: glassbox L2 0.958, **glassbox log loss 0.966**, blackbox L2 0.966, **blackbox log loss 0.972**.
- Log loss beats L2 for both (+0.008 and +0.007; both intervals exclude zero). L2 scores fall outside 0–1 for 20–29% of wafers.
- Why validation and not training: the blackbox's training AUC is 1.000.
- Figure: `03_auc_intervals.png`.

## Slide 3: The decision, and the threshold
- Blackbox AUC is higher by 0.006 (95% CI +0.0001 to +0.012), but its evaluation loss is **not** lower (0.149 vs 0.143). Our rule, set in advance: a blackbox must lower the cost by 10% to be chosen. **We chose the glassbox.**
- Point to make: a higher AUC didn't give a lower cost, because our costs only care about one end of the ROC curve.
- Threshold: 0.28 on the raw score, not 0.5. That lowers the evaluation loss by 27% on validation. Minimising plain misclassification would give 0.61, the opposite direction.
- Figure: `04_threshold.png`.

## Slide 4: Calibration, and why it matters for the threshold
- Glassbox ECE 0.031: it under-predicts between 0.2 and 0.5, where the threshold sits.
- Fix: isotonic regression fitted on out-of-fold training scores. ECE about 0.02, AUC unchanged. Platt scaling barely helps a logistic model (0.029), but works for the blackbox (0.034 → 0.013).
- With calibrated probabilities, theory gives the threshold directly: 1/(1+5) = 0.167. Ours is 0.22, and using 0.167 costs almost the same (0.148 vs 0.143).
- Cost ratios 3 to 8: the glassbox stays the cheaper model.
- Figures: `05_calibration.png`, `06_cost_sensitivity.png`.

## Slide 5: Interpretability: tree SHAP on the blackbox
- **Global:** `largest_cluster_radius` dominates (mean |SHAP| 4.0), then `edge_fail_rate` (1.8) and `outer_ring_fail_rate` (0.9). The model asks the question an engineer would: is the cluster at the edge?
- **Local:** three wafers next to their maps: the most confident Edge-Loc, the most confident Loc, and the costliest mistake.
- The costliest mistake has its cluster near the centre (radius 0.32). Both models call it Loc. It may be a labelling error.
- **Caution:** the glassbox's coefficients are hard to read (`fail_rate` −22, `edge_fail_rate` +13) because the fail-rate features are correlated. A glassbox isn't automatically interpretable. SHAP credit among those features is also unstable.
- Figures: `07_shap_global.png`, `09_shap_local.png`.

## Slide 6: Test result, limits, what we'd do next
- **Test, used once:** AUC 0.958 (95% CI 0.946 to 0.969). Evaluation loss 0.181 per wafer: 56% below holding every wafer, 17% below a 0.5 threshold.
- Test is worse than validation (0.181 vs 0.143): the optimiser's curse, as expected, since the model and threshold were picked on validation.
- **Limits:** the 5:1 cost ratio is assumed; labels are engineers' judgements.
- **Honest audit:** on test the blackbox we didn't choose scores 0.158 against our 0.181 (difference −0.023, 95% CI −0.051 to +0.007, so not distinguishable). We did not switch after seeing test.
- **Next:** get real cost figures from a fab; try a sparser glassbox (EBM or a shallow tree) for cleaner explanations; re-check labels on the worst mistakes.
