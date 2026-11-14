# Slide outline, run 2: scratch detection (6 slides)

Every number below comes from `project/Project2_Classification_Scratch.ipynb`.

- **Deck:** https://claude.ai/artifact/TVt1dE1fV5p8tuV6fe84WL (private until shared; download as PowerPoint or PDF from its Share menu).
- **PowerPoint file:** `Project2_Scratch_Detection.pptx`, built by `build_pptx_scratch.js`. Same six slides and speaker notes as the deck.
- **Deck source:** `deck_scratch/` holds the six slides as published.
- **Slide figures:** `figures_scratch/`, drawn by `make_slide_figures.py scratch` from the notebook's own numbers.

The run 1 outline is in `SLIDES.md`. The brief allows at most 6 slides in total, so the two decks can't both be presented in full.

## Slide 1: Is there a scratch on this wafer?
- **Decision:** a scratch is a thin line of failing dies from mechanical contact. If the model says "scratch", the handling path is held.
- **Data:** MixedWM38, 36,991 wafer maps, each labelled with every pattern it has. 49% have a scratch (balanced by the authors, partly with generated maps).
- **Cleaning:** 1,024 duplicate maps dropped (97.7% scratch); the die-count feature deleted because it gave the label away.
- **Everything else is the same as run 1:** features, models, search grids, split sizes, and the 5:1 evaluation loss.
- Figure: `s1_wafers.png`.

## Slide 2: The same four models, a very different picture
- Validation AUC: glassbox L2 0.597, glassbox log loss 0.654, blackbox L2 0.879, blackbox log loss 0.881.
- The glassbox can't see a thin line: the blackbox is +0.227 ahead (95% CI +0.215 to +0.241).
- Log loss beats L2 for the glassbox (+0.057) and ties for the blackbox (+0.002, interval includes zero).
- The split is random, because the dataset has no lot information.
- Figure: `s2_auc.png`.

## Slide 3: This time the blackbox wins, at threshold 0.175
- Same rule as run 1: the blackbox must cut the cost by 10%. Here it cuts it by 36% (0.328 vs 0.512).
- The glassbox's best cost equals holding the tool for every wafer (0.513).
- Threshold 0.175, not 0.5: cost −45% (0.595 → 0.328); accuracy 79.1% → 70.9%.
- Misses 68 instead of 714; false alarms 2,088 instead of 835.
- Figure: `s3_threshold.png`.

## Slide 4: Calibration: already good, and the threshold shows it
- Calibration error 0.013 before, 0.009 after Platt scaling fitted on out-of-fold training scores. AUC unchanged.
- Threshold on calibrated probabilities 0.155, against the theoretical 0.167. In run 1 it was 0.22.
- Figure: `s4_calibration.png`.

## Slide 5: Tree SHAP: the model does not look at the scratch
- **Global:** `edge_fail_rate` (1.2) and `outer_ring_fail_rate` (1.0) lead. No feature describes a line.
- **Local:** the most confident scratch (Donut + Edge-Ring + Loc + Scratch, P = 1.000) shows no visible line. The costliest mistake is an Edge-Loc + Scratch wafer scored 0.013.
- Likely cause: the model has learned which mixes of patterns come with the Scratch label in this dataset.
- Figures: `s5_shap_global.png`, `s5_shap_local_correct.png`, `s5_shap_local_mistake.png`.

## Slide 6: Two runs, one pipeline, opposite decisions
- Side-by-side table of run 1 and run 2: data, validation AUC, loss, model chosen, threshold, calibration, test AUC, test loss, whether SHAP matches the physics.
- Run 2 test, used once: AUC 0.882 (95% CI 0.874 to 0.889); loss 0.330 per wafer, 36% below holding every wafer (0.513).
- **What the comparison shows:** the same rule picks the glassbox when a linear model captures the signal, and the blackbox when it can't. Log loss never loses to L2.
- **Which to trust:** run 1. Run 2's model reads how the dataset was built, and its 49% scratch rate is artificial.
