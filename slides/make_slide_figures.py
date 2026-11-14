"""Redraw the key figures at slide size with large labels.

Runs the code cells of a project notebook, then draws from the resulting
objects, so every slide figure uses the notebook's own numbers.

Usage (from anywhere):
    python slides/make_slide_figures.py            # main project (WM-811K, Edge-Loc vs Loc)
    python slides/make_slide_figures.py scratch    # comparison run (MixedWM38, Scratch vs not)
"""
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
RUN = sys.argv[1] if len(sys.argv) > 1 else "main"
CFG = {
    "main": dict(notebook="Project2_Classification.ipynb", out="figures", positive="Edge-Loc",
                 auc_xlim=(0.944, 0.986), cost_ylim=0.6, cost_xmax=0.9, loss_label=(0.60, 0.40), mis_label=(0.62, 0.035)),
    "scratch": dict(notebook="Project2_Classification_Scratch.ipynb", out="figures_scratch", positive="scratch",
                    auc_xlim=(0.56, 0.96), cost_ylim=1.4, cost_xmax=0.9, loss_label=(0.52, 0.85), mis_label=(0.55, 0.10)),
}[RUN]
OUT = os.path.join(HERE, CFG["out"])
os.makedirs(OUT, exist_ok=True)
os.chdir(os.path.join(HERE, "..", "project"))      # the notebook reads data/ relative to its own folder

# Run the notebook's code with plotting and display switched off
ns = {"display": lambda *a, **k: None}
nb = json.load(open(CFG["notebook"]))
plt.show = lambda *a, **k: None
for cell in nb["cells"]:
    if cell["cell_type"] == "code":
        src = "".join(cell["source"]).replace("from IPython.display import display, Markdown", "Markdown = str")
        exec(src, ns)
        ns["savefig"] = lambda name: None            # keep the notebook's own figures untouched
        plt.close("all")
g = ns.__getitem__
BLUE, ORANGE, INK2, MUTED = g("BLUE"), g("ORANGE"), g("INK2"), g("MUTED")
plt.rcParams.update({"font.size": 18, "axes.labelsize": 18, "xtick.labelsize": 16, "ytick.labelsize": 16,
                     "legend.fontsize": 16, "axes.titlesize": 18, "lines.linewidth": 3})


def save(name, w, h):
    plt.gcf().set_size_inches(w / 100, h / 100)
    plt.savefig(os.path.join(OUT, name), dpi=200)
    plt.close("all")


yv, CHOSEN, MODELS, S_va, STYLE = g("yv"), g("CHOSEN"), g("MODELS"), g("S_va"), g("STYLE")
df, val_idx, FEATURES, X_va = g("df"), g("val_idx"), g("FEATURES"), g("X_va")
sv, p_gbm, picks, wafer_map, wafer_cmap = g("sv"), g("p_gbm"), g("picks"), g("wafer_map"), g("wafer_cmap")

# 1. Two example wafers
if RUN == "main":      # the most confident Loc and Edge-Loc
    examples = [(val_idx[picks[1][1]], "Loc: cluster in the interior"), (val_idx[picks[0][1]], "Edge-Loc: cluster at the edge")]
else:                  # the first validation wafer with a scratch alone, and the first with a scratch among two other patterns
    val = df.iloc[val_idx]
    examples = [(val.index[(val["pattern"] == "Scratch").values][0], "Scratch alone"),
                (val.index[((val["scratch"] == 1) & (val["n_patterns"] == 3)).values][0], "Scratch + two other patterns")]
fig, axes = plt.subplots(1, 2, constrained_layout=True)
for ax, (row, name) in zip(axes, examples):
    ax.imshow(wafer_map(df.loc[row, df.columns[0]]), cmap=wafer_cmap, vmin=0, vmax=2, interpolation="nearest")
    ax.axis("off"); ax.set_title(name, fontsize=20, fontweight="bold")
    print("example wafer:", name, "|", df.loc[row, "pattern"])
save("s1_wafers.png", 820, 430)

# 2. Validation AUC with intervals
tab = g("auc_tab")
fig, ax = plt.subplots(constrained_layout=True)
for i, r in tab.iloc[::-1].reset_index(drop=True).iterrows():
    k = (r["model"], r["train loss"])
    ax.plot([r["95% CI low"], r["95% CI high"]], [i, i], color=STYLE[k][0], lw=4, ls=STYLE[k][1])
    ax.plot(r["validation AUC"], i, "o", ms=16, color=STYLE[k][0], mec="#fcfcfb", mew=3)
    ax.text(r["95% CI high"] + (CFG["auc_xlim"][1] - CFG["auc_xlim"][0]) / 42, i, f"{r['validation AUC']:.3f}", va="center", fontsize=18, color=INK2)
ax.set_yticks(range(4)); ax.set_yticklabels([f"{r['model']}, {r['train loss']}" for _, r in tab.iloc[::-1].iterrows()])
ax.set_xlim(*CFG["auc_xlim"]); ax.set_ylim(-0.5, 3.5); ax.grid(axis="y", visible=False)
ax.set_xlabel("validation AUC, with 95% interval")
save("s2_auc.png", 860, 430)

# 3. Evaluation loss vs threshold
ts, curve, curve_mis, T_STAR = g("ts"), g("curve"), g("curve_mis"), g("T_STAR")
fig, ax = plt.subplots(constrained_layout=True)
ax.plot(ts, curve, color=ORANGE, label="our loss (miss = 5, false alarm = 1)")
ax.plot(ts, curve_mis, color=BLUE, label="misclassification rate")
ax.axvline(T_STAR, color=INK2, lw=2, ls="--"); ax.text(T_STAR + 0.015, CFG["cost_ylim"] * 0.93, f"best: {T_STAR:.2f}" if RUN == "main" else f"best: {T_STAR:.3f}", color=INK2)
ax.axvline(0.5, color=MUTED, lw=2, ls=":"); ax.text(0.515, CFG["cost_ylim"] * 0.93, "default: 0.5", color=MUTED)
ax.set_ylim(0, CFG["cost_ylim"]); ax.set_xlim(0, CFG["cost_xmax"]); ax.set_xlabel(f"threshold on the {CHOSEN[0]} score"); ax.set_ylabel("cost per wafer")
ax.text(*CFG["loss_label"], "our loss\n(miss = 5, false alarm = 1)", color=ORANGE, ha="right", fontweight="bold")
ax.text(*CFG["mis_label"], "misclassification rate", color=BLUE, fontweight="bold")
save("s3_threshold.png", 900, 520)

# 4. Reliability: chosen model before and after, with the L2 glassbox for contrast
reliability, ece, CAL, CALIB = g("reliability"), g("ece"), g("CAL"), g("CALIB")
raw = S_va[CHOSEN]; cal = CAL[CHOSEN][CALIB](raw); l2 = S_va[(CHOSEN[0], "L2")]
fig, ax = plt.subplots(constrained_layout=True)
ax.plot([0, 1], [0, 1], color=MUTED, lw=2, ls=":")
for p, c, ls, mk, lab in [(l2, MUTED, "--", "D", f"{CHOSEN[0]}, L2 loss (ECE {ece(yv, l2):.3f})"),
                          (raw, BLUE, "-", "o", f"chosen model, raw (ECE {ece(yv, raw):.3f})"),
                          (cal, ORANGE, "-", "s", f"chosen model, calibrated (ECE {ece(yv, cal):.3f})")]:
    mp, ob = reliability(yv, p); ax.plot(mp, ob, color=c, ls=ls, marker=mk, ms=9, label=lab)
ax.set_xlabel(f"predicted probability of {CFG['positive']}"); ax.set_ylabel(f"observed {CFG['positive']} rate"); ax.legend(loc="upper left")
save("s4_calibration.png", 900, 560)

# 5a. Global SHAP
glob = pd.Series(np.abs(sv).mean(0), index=FEATURES).sort_values()
fig, ax = plt.subplots(constrained_layout=True)
ax.barh(glob.index, glob.values, color=ORANGE, height=0.62); ax.grid(axis="y", visible=False)
ax.set_xlabel("mean |SHAP| (log-odds)")
save("s5_shap_global.png", 760, 560)

# 5b. Local SHAP: two wafers next to their maps
base_value, logit = g("base_value"), g("logit")
for name, (title, i) in [("s5_shap_local_correct.png", picks[0]), ("s5_shap_local_mistake.png", picks[2])]:
    fig, (axm, axs) = plt.subplots(1, 2, gridspec_kw={"width_ratios": [1, 2.3]}, constrained_layout=True)
    axm.imshow(wafer_map(df.iloc[val_idx[i]][df.columns[0]]), cmap=wafer_cmap, vmin=0, vmax=2, interpolation="nearest"); axm.axis("off")
    c = pd.Series(sv[i], index=FEATURES); c = c.reindex(c.abs().sort_values().index[-4:])
    axs.barh([f"{f} = {X_va.iloc[i][f]:.2g}" for f in c.index], c.values, color=[ORANGE if v > 0 else BLUE for v in c.values], height=0.62)
    axs.axvline(0, color=MUTED, lw=2); axs.grid(axis="y", visible=False); axs.tick_params(axis="y", labelsize=15)
    axs.set_xlabel("SHAP value (log-odds)", fontsize=16)
    save(name, 900, 270)
print("wrote", sorted(os.listdir(OUT)))
