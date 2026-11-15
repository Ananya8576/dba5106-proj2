# Slide outline, project B: scratch detection (6 slides)

Every number below comes from `project/Project2_Classification_Scratch.ipynb`.

- **Deck:** https://claude.ai/artifact/TVt1dE1fV5p8tuV6fe84WL (private until shared; download as PowerPoint or PDF from its Share menu).
- **PowerPoint file:** `Project2_Scratch_Detection.pptx`, built by `build_pptx_scratch.js`. Same six slides and speaker notes as the deck.
- **Deck source:** `deck_scratch/` holds the six slides as published.
- **Slide figures:** `figures_scratch/`, drawn by `make_slide_figures.py scratch` from the notebook's own numbers.

## Slide 1: Is there a scratch on this wafer?
- **Decision:** a scratch comes from mechanical contact, repeats until the handler is fixed, and puts neighbouring dies at risk. A flag holds the handler and sends the wafer to neighbour-die screening.
- **Data:** MixedWM38 (Kaggle usability 7.5), 36,991 wafer maps, each labelled with every pattern it has. 49% have a scratch, a rate the authors balanced, partly with generated maps.
- **Evaluation loss:** (10 × missed scratch + 1 × false alarm) / wafers. The 10:1 ratio is our assumption.
- **Cleaning:** 1,024 duplicate maps dropped (97.7% scratched); the die count withheld.
- Figure: `s1_wafers.png`.

## Slide 2: Features built for a line, then four models
- 16 features: 9 background, 7 line. The line features are the seven strongest single features (AUC 0.63–0.73). None says where the line is.
- Validation AUC: glassbox L2 0.885, glassbox log loss 0.909, blackbox L2 0.958, blackbox log loss 0.963.
- Log loss beats L2 for both (+0.024 and +0.005; both intervals exclude zero). L2 scores fall outside 0–1 for 10–24% of wafers.
- 60 / 20 / 20 stratified split; 32 configurations, tuned inside the training split.
- Figure: `s2_auc.png`.

## Slide 3: We chose the blackbox, at threshold 0.117
- The blackbox's AUC is 0.054 higher (95% CI +0.049 to +0.060) and its evaluation loss 38% lower (0.250 vs 0.406). The rule, set in advance, asked for 10%.
- Threshold 0.117, not 0.5: cost −59% (0.613 → 0.250); accuracy 89.1% → 81.2%.
- Misses 51 instead of 414; false alarms 1,339 instead of 395.
- The choice holds for every cost ratio from 1 to 20.
- Figure: `s3_threshold.png`.

## Slide 4: Calibration: close already, slightly better after
- Calibration error 0.011 before, 0.009 after Platt scaling fitted on out-of-fold training scores. AUC unchanged.
- The L2 versions are the worst calibrated: 0.077 (glassbox) and 0.035 (blackbox).
- Threshold on calibrated probabilities 0.105, against the theoretical 0.091, at almost the same cost.
- Figure: `s4_calibration.png`.

## Slide 5: Tree SHAP: does the model look at the scratch?
- **Global:** `outer_ring_fail_rate` (1.9, background) leads, then `thin_fail_rate` (1.4) and `line_score_top20` (1.2). Line features carry 49% of the attribution.
- **Local:** the most confident scratch is a scratch-only wafer with a visible diagonal line. The costliest mistake is a Donut + Edge-Loc + Loc + Scratch wafer where large blobs hide the line (P = 0.003).
- **Caution:** part of the background attribution may be which patterns come with a Scratch label in this dataset.
- Figures: `s5_shap_global.png`, `s5_shap_local_correct.png`, `s5_shap_local_mistake.png`.

## Slide 6: Test result, used once, and what to flag
- AUC 0.961 (95% CI 0.957 to 0.964); loss 0.263 per wafer (0.242 to 0.286), 49% below flagging every wafer (0.513); recall 98.4%, precision 72.3%.
- **Audit:** the glassbox scores 0.426 on test (+0.162, CI +0.134 to +0.191). Validation and test agree: 0.250 vs 0.263.
- **Limits:** artificial 49% scratch rate; assumed 10:1 ratio; half the attribution is background; random split. An earlier version with other features was scored on this test split once.
