"""Build the modelling table for the scratch-detection comparison from MixedWM38.

Reads Wafer_Map_Datasets.npz (Kaggle: co1d7era/mixedtype-wafer-defect-datasets),
computes the same spatial features as build_features.py for every wafer map,
and applies the cleaning the screening notebook found necessary:
  - exact duplicate maps are dropped (they were 97.7% Scratch)
  - n_dies is not written (in this dataset it gives the label away)
Target: scratch = 1 if the wafer's label includes the Scratch pattern.

Usage: python build_features_mixedwm38.py [path/to/Wafer_Map_Datasets.npz]
"""
import os
import sys

import numpy as np
import pandas as pd

from build_features import wafer_features

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "data", "mixedwm38_scratch_features.csv")
OUT_MAPS = os.path.join(HERE, "data", "mixedwm38_scratch_maps.npz")
PATTERNS = ["Center", "Donut", "Edge-Loc", "Edge-Ring", "Loc", "Near-full", "Scratch", "Random"]   # label order C2-C9


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
    print(f"read {maps.shape[0]:,} maps of {maps.shape[1]}x{maps.shape[2]}")

    # Exact duplicate maps: keep the first copy
    flat = maps.reshape(len(maps), -1)
    _, first = np.unique(flat, axis=0, return_index=True)
    keep = np.sort(first)
    print(f"exact duplicate maps dropped: {len(maps) - len(keep):,} "
          f"({labels[np.setdiff1d(np.arange(len(maps)), keep), PATTERNS.index('Scratch')].mean():.1%} of them Scratch)")

    rows = []
    for i in keep:
        f = wafer_features(maps[i])
        f.pop("n_dies")
        rows.append(f)
    out = pd.DataFrame(rows, index=pd.Index(keep, name="wafer_id"))
    lab = labels[keep]
    out["pattern"] = [" + ".join(p for p, on in zip(PATTERNS, r) if on) or "none" for r in lab]
    out["n_patterns"] = lab.sum(1)
    out["scratch"] = lab[:, PATTERNS.index("Scratch")]
    out.round(6).to_csv(OUT)
    np.savez_compressed(OUT_MAPS, maps=maps[keep].astype(np.uint8), wafer_id=keep)
    print(f"wrote {len(out):,} rows to {OUT} and their maps to {OUT_MAPS}")
    print("scratch rate:", round(out["scratch"].mean(), 4), "| wafers by number of patterns:", out["n_patterns"].value_counts().sort_index().to_dict())
    print("feature rows still duplicated after dropping duplicate maps:", int(out.drop(columns=["pattern", "n_patterns", "scratch"]).duplicated().sum()))


if __name__ == "__main__":
    main()
