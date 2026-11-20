"""Build the modelling table for scratch detection from MixedWM38.

Reads Wafer_Map_Datasets.npz (Kaggle: co1d7era/mixedtype-wafer-defect-datasets)
and writes one row per wafer map with:
  - 9 background features: how many dies fail, where, and how clustered
  - 7 line features: evidence of a thin line of failing dies
  - the label (scratch = 1 if the wafer's label includes the Scratch pattern)
  - the train / validation / test split (60 / 20 / 20, stratified, fixed here)

Cleaning, with the evidence written to data/mixedwm38_cleaning_report.json:
  - exact duplicate maps are dropped (the first copy is kept)
  - the die count is measured but not written as a feature

Usage: python build_features_mixedwm38.py [path/to/Wafer_Map_Datasets.npz]
"""
import json
import os
import sys

import numpy as np
import pandas as pd
from scipy import ndimage
from sklearn.model_selection import StratifiedGroupKFold

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "data", "mixedwm38_scratch_features.csv")
OUT_MAPS = os.path.join(HERE, "data", "mixedwm38_scratch_maps.npz")
OUT_REPORT = os.path.join(HERE, "data", "mixedwm38_cleaning_report.json")
PATTERNS = ["Center", "Donut", "Edge-Loc", "Edge-Ring", "Loc", "Near-full", "Scratch", "Random"]   # label order C2-C9
SEED = 42
EIGHT = np.ones((3, 3))                 # 8-connected neighbourhood
RADON_ANGLES = np.arange(0, 180, 6)


def _line_kernels(length=9, n_angles=12):
    """One short straight-line kernel per direction."""
    kernels, h = [], length // 2
    for a in np.arange(n_angles) * np.pi / n_angles:
        k = np.zeros((length, length))
        for t in np.linspace(-h, h, 4 * length):
            k[int(round(h + t * np.sin(a))), int(round(h + t * np.cos(a)))] = 1
        kernels.append(k / k.sum())
    return kernels


KERNELS = _line_kernels()


def background_features(m):
    """How many dies fail, where on the wafer, and how clustered (0 = no die, 1 = pass, 2 = fail)."""
    die = m > 0
    fail = m == 2
    n_die = int(die.sum())
    yy, xx = np.indices(m.shape)
    cy, cx = yy[die].mean(), xx[die].mean()
    r = np.hypot(yy - cy, xx - cx)
    r = r / max(r[die].max(), 1e-9)          # radius normalised so the outermost die is at 1

    def rate(zone):
        z = zone & die
        return fail[z].sum() / z.sum() if z.sum() else 0.0

    lab, n = ndimage.label(fail, structure=EIGHT)
    if n:
        sizes = ndimage.sum(fail, lab, range(1, n + 1))
        big = int(np.argmax(sizes)) + 1
        largest, big_r = sizes.max() / n_die, r[lab == big].mean()
    else:
        largest, big_r = 0.0, np.nan
    th = np.arctan2(yy[fail] - cy, xx[fail] - cx)
    ang = float(np.abs(np.exp(1j * th).mean())) if fail.sum() else np.nan
    return n_die, dict(
        fail_rate=fail.sum() / n_die,
        center_fail_rate=rate(r < 0.3),
        middle_fail_rate=rate((r >= 0.3) & (r < 0.7)),
        edge_fail_rate=rate(r >= 0.7),
        outer_ring_fail_rate=rate(r >= 0.9),
        n_fail_clusters=n,
        largest_cluster_share=largest,
        largest_cluster_radius=big_r,
        angular_concentration=ang,
    )


def line_features(m):
    """Evidence of a thin line of failing dies. No feature says where on the wafer the line is."""
    die = m > 0
    fail = m == 2
    n_die = die.sum()
    side = m.shape[0]

    # (a) Thin structures: failing dies that do not survive a 2x2 opening. Blobs survive; lines and specks do not.
    thin = fail & ~ndimage.binary_opening(fail, structure=np.ones((2, 2)))
    lab, n = ndimage.label(thin, structure=EIGHT)
    longest, n_long = 0.0, 0
    if n:
        sizes = ndimage.sum(thin, lab, range(1, n + 1))
        for k in np.flatnonzero(sizes >= 5) + 1:
            yy, xx = np.nonzero(lab == k)
            major = np.sort(np.linalg.eigvalsh(np.cov(np.vstack([yy, xx])) + np.eye(2) * 1e-6))[1]
            length = 4 * np.sqrt(major)                       # about the end-to-end length of the structure, in dies
            n_long += length >= 10
            longest = max(longest, length)

    # (b) Straight-line evidence over the whole wafer: the strongest line sum over all directions, against the typical one.
    centred = thin.astype(float) - thin.sum() / max(n_die, 1) * die
    peaks = np.array([ndimage.uniform_filter1d(ndimage.rotate(centred, a, reshape=False, order=1), size=3, axis=0).sum(axis=1).max()
                      for a in RADON_ANGLES])

    # (c) Local direction: at each failing die, the share of failing dies along the best direction minus the typical direction.
    #     A die on a line scores high; a die inside a blob scores low, because every direction is full.
    resp = np.stack([ndimage.convolve(fail.astype(float), k, mode="constant") for k in KERNELS])
    score = (resp.max(0) - np.median(resp, 0)) * fail
    on_line = score >= 0.5
    lab2, n2 = ndimage.label(on_line, structure=EIGHT)
    seg_len = 0.0
    if n2:
        k = int(np.argmax(ndimage.sum(on_line, lab2, range(1, n2 + 1)))) + 1
        yy, xx = np.nonzero(lab2 == k)
        seg_len = float(np.hypot(yy.max() - yy.min(), xx.max() - xx.min()))
    top = np.sort(score[die])[::-1][:20]

    return dict(
        thin_fail_rate=thin.sum() / n_die,
        longest_thin_length=longest / side,
        n_long_thin=n_long,
        line_peak_contrast=(peaks.max() - np.median(peaks)) / side,
        longest_line_length=seg_len / side,
        n_line_segments=n2,
        line_score_top20=top.mean(),
    )


def main():
    if len(sys.argv) > 1:
        path = sys.argv[1]
    else:
        import kagglehub
        path = os.path.join(kagglehub.dataset_download("co1d7era/mixedtype-wafer-defect-datasets"), "Wafer_Map_Datasets.npz")
    z = np.load(path, allow_pickle=False)
    arrs = [z[k] for k in z.files]
    maps = next(a for a in arrs if a.ndim == 3)
    labels = next(a for a in arrs if a.ndim == 2 and a.shape[1] == len(PATTERNS)).astype(int)
    scratch_all = labels[:, PATTERNS.index("Scratch")]
    print(f"read {maps.shape[0]:,} maps of {maps.shape[1]}x{maps.shape[2]}")

    # Exact duplicate maps: keep the first copy
    _, first = np.unique(maps.reshape(len(maps), -1), axis=0, return_index=True)
    keep = np.sort(first)
    dropped = np.setdiff1d(np.arange(len(maps)), keep)

    rows, n_dies = [], []
    for i in keep:
        nd, f = background_features(maps[i])
        f.update(line_features(maps[i]))
        rows.append(f)
        n_dies.append(nd)
    out = pd.DataFrame(rows, index=pd.Index(keep, name="wafer_id"))
    lab = labels[keep]
    out["pattern"] = [" + ".join(p for p, on in zip(PATTERNS, r) if on) or "none" for r in lab]
    out["n_patterns"] = lab.sum(1)
    out["scratch"] = lab[:, PATTERNS.index("Scratch")]

    # Fixed 60 / 20 / 20 split, stratified on the label. The dataset has no lots, so each wafer is its own group;
    # this keeps the partition identical to the one this table has had since it was first built.
    folds = [te for _, te in StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=SEED).split(out, out["scratch"], np.arange(len(out)))]
    out["split"] = "train"
    out.iloc[folds[0], out.columns.get_loc("split")] = "test"
    out.iloc[folds[1], out.columns.get_loc("split")] = "validation"

    n_dies = np.array(n_dies)
    s = out["scratch"].values == 1
    report = {
        "maps_read": int(len(maps)),
        "duplicate_maps_dropped": int(len(dropped)),
        "share_of_dropped_duplicates_with_scratch": round(float(scratch_all[dropped].mean()), 4),
        "maps_kept": int(len(keep)),
        "scratch_rate_kept": round(float(out["scratch"].mean()), 4),
        "die_count_scratch": {"min": int(n_dies[s].min()), "max": int(n_dies[s].max()), "sd": round(float(n_dies[s].std()), 2)},
        "die_count_no_scratch": {"min": int(n_dies[~s].min()), "max": int(n_dies[~s].max()), "sd": round(float(n_dies[~s].std()), 2)},
        "share_of_no_scratch_wafers_outside_the_scratch_die_count_range":
            round(float(((n_dies[~s] < n_dies[s].min()) | (n_dies[~s] > n_dies[s].max())).mean()), 4),
    }
    json.dump(report, open(OUT_REPORT, "w"), indent=2)
    out.round(6).to_csv(OUT)
    np.savez_compressed(OUT_MAPS, maps=maps[keep].astype(np.uint8), wafer_id=keep)
    print(f"wrote {len(out):,} rows to {OUT}")
    print(json.dumps(report, indent=2))
    print(out["split"].value_counts().to_dict())


if __name__ == "__main__":
    main()
