"""Build the modelling table for Project 2 from the WM-811K wafer maps.

Reads LSWMD.pkl (Kaggle: qingyi/wm811k-wafer-map), keeps the wafers labelled
Edge-Loc or Loc, and writes one row per wafer with 10 named spatial features,
the lot name (for lot-aware splitting) and the label. It also saves the raw
maps of those wafers, which the notebook draws next to the SHAP explanations.

Usage: python build_features.py [path/to/LSWMD.pkl]
Without a path, the file is downloaded with kagglehub.
"""
import os
import pickle
import sys

import numpy as np
import pandas as pd
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "data", "wm811k_edgeloc_loc_features.csv")
OUT_MAPS = os.path.join(HERE, "data", "wm811k_edgeloc_loc_maps.npz")
KEEP = ["Edge-Loc", "Loc"]


def load_lswmd(path):
    # The pickle was written by an old pandas, so try a few compatibility routes
    try:
        return pd.read_pickle(path)
    except Exception as e1:
        print("plain read_pickle failed:", repr(e1)[:120])
    import pandas.core.indexes as _idx
    sys.modules.setdefault("pandas.indexes", _idx)
    try:
        return pd.read_pickle(path)
    except Exception as e2:
        print("alias route failed:", repr(e2)[:120])

    class _Legacy(pickle.Unpickler):
        def find_class(self, module, name):
            if module.startswith("pandas.indexes"):
                module = "pandas.core.indexes" + module[len("pandas.indexes"):]
            if module == "pandas.core.indexes.numeric" or name in ("Int64Index", "UInt64Index", "Float64Index"):
                return pd.Index
            return super().find_class(module, name)

    with open(path, "rb") as fh:
        return _Legacy(fh, encoding="latin1").load()


def first_str(x, empty="unlabeled"):
    a = np.asarray(x, dtype=object).ravel()
    return str(a[0]).strip() if a.size else empty


def wafer_features(m):
    """10 spatial features of one wafer map (0 = no die, 1 = pass, 2 = fail)."""
    m = np.asarray(m)
    die = m > 0
    fail = m == 2
    n_die = int(die.sum())
    if n_die == 0:
        return None
    yy, xx = np.indices(m.shape)
    cy, cx = yy[die].mean(), xx[die].mean()
    r = np.hypot(yy - cy, xx - cx)
    r = r / max(r[die].max(), 1e-9)          # radius normalised so the outermost die is at 1

    def rate(zone):
        z = zone & die
        return fail[z].sum() / z.sum() if z.sum() else 0.0

    lab, n = ndimage.label(fail, structure=np.ones((3, 3)))   # 8-connected clusters of failing dies
    if n:
        sizes = ndimage.sum(fail, lab, range(1, n + 1))
        big = int(np.argmax(sizes)) + 1
        largest, big_r = sizes.max() / n_die, r[lab == big].mean()
    else:
        largest, big_r = 0.0, np.nan
    th = np.arctan2(yy[fail] - cy, xx[fail] - cx)
    ang = float(np.abs(np.exp(1j * th).mean())) if fail.sum() else np.nan
    return dict(
        n_dies=n_die,
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


def main():
    if len(sys.argv) > 1:
        path = sys.argv[1]
    else:
        import kagglehub
        path = os.path.join(kagglehub.dataset_download("qingyi/wm811k-wafer-map"), "LSWMD.pkl")
    wm = load_lswmd(path)
    wm["pattern"] = wm["failureType"].map(first_str)
    sub = wm.loc[wm["pattern"].isin(KEEP), ["waferMap", "lotName", "waferIndex", "pattern"]]
    feats = [wafer_features(m) for m in sub["waferMap"]]
    ok = [f is not None for f in feats]
    out = pd.DataFrame([f for f in feats if f is not None], index=sub.index[ok])
    out.insert(0, "lot", sub.loc[out.index, "lotName"].astype(str))
    out.insert(1, "wafer_index", sub.loc[out.index, "waferIndex"].astype(int))
    out["pattern"] = sub.loc[out.index, "pattern"]
    out["edge_loc"] = (out["pattern"] == "Edge-Loc").astype(int)
    out.index.name = "wm811k_row"
    out.round(6).to_csv(OUT)
    print(f"wrote {len(out):,} rows to {OUT}")
    # The raw maps, padded to one size (255 = padding), so the notebook can draw a wafer next to its explanation
    maps = [np.asarray(m, dtype=np.uint8) for m in sub.loc[out.index, "waferMap"]]
    h, w = max(m.shape[0] for m in maps), max(m.shape[1] for m in maps)
    stack = np.full((len(maps), h, w), 255, dtype=np.uint8)
    for i, m in enumerate(maps):
        stack[i, :m.shape[0], :m.shape[1]] = m
    np.savez_compressed(OUT_MAPS, maps=stack, wm811k_row=out.index.values)
    print(f"wrote {stack.shape} maps to {OUT_MAPS}")
    print(out["pattern"].value_counts().to_dict(), "| lots:", out["lot"].nunique())


if __name__ == "__main__":
    main()
