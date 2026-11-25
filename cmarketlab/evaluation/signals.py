"""Testing a feature or a boolean signal against a target on daily, heavily autocorrelated data."""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import rankdata


def auc(x: pd.Series, y: pd.Series) -> float:
    """P(x on a positive day > x on a negative day), ties counted half (Mann-Whitney). NaN-safe."""
    j = pd.concat([x, y], axis=1, keys=["x", "y"]).dropna()
    pos = j["y"].astype(bool)
    n1, n0 = pos.sum(), (~pos).sum()
    if n1 == 0 or n0 == 0:
        return np.nan
    r = rankdata(j["x"].values)
    return float((r[pos.values].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def shift_test(x: pd.Series, y: pd.Series, stat=auc, n: int = 500, min_shift: int = 180, seed: int = 0):
    """Two-sided p-value of stat(x, y) against circular shifts of x by >= min_shift days. Shifting keeps each
    series' own autocorrelation and breaks only their alignment, so it is honest for slow cycle features.

    Returns (observed, p-value, null mean). Rows where y is NaN (e.g. out-of-state days) stay excluded."""
    x = x.reindex(y.index)
    obs = stat(x, y)
    vals = x.values
    L = len(vals)
    if L <= 2 * min_shift:
        return obs, np.nan, np.nan
    rng = np.random.default_rng(seed)
    null = np.array([stat(pd.Series(np.roll(vals, k), index=y.index), y)
                     for k in rng.integers(min_shift, L - min_shift, n)])
    null = null[np.isfinite(null)]
    c = np.nanmean(null)
    p = (np.sum(np.abs(null - c) >= abs(obs - c)) + 1) / (len(null) + 1)
    return obs, float(p), float(c)


def feature_tests(f: pd.DataFrame, spec: dict, targets: dict, family_start: dict | None = None,
                  family_split: dict | None = None, ref_start=None, n_shift: int = 400) -> pd.DataFrame:
    """Direction-signed AUC tests of many features against bottom / top targets.

    f        daily feature frame
    spec     {feature: (family, direction_bottom, direction_top, description)}; direction +1 / -1 / 0 (no prior,
             reported as +1) / None (not tested on that side)
    targets  {horizon: (bottom target, top target)} as from labels.cycle_targets
    family_start  {family: first date to evaluate}; family_split {family: date splitting the two halves}
    ref_start     also report each feature's AUC from this date (like-for-like with a shorter-history family)
    Returns one row per side x horizon x feature: days, base_rate, auc, shift-test p, auc of each half, auc_ref."""
    family_start, family_split = family_start or {}, family_split or {}
    rows = []
    for h, (bottom, top) in targets.items():
        for side, y in (("bottom", bottom), ("top", top)):
            for name, (fam, db, dt, *_rest) in spec.items():
                d = db if side == "bottom" else dt
                if d is None:
                    continue
                x = f[name] * (d if d != 0 else 1)
                yy = y.where(x.notna())
                if fam in family_start:
                    yy = yy.where(f.index >= family_start[fam])
                n = int(yy.notna().sum())
                if n < 100:
                    continue
                a, p, null = shift_test(x, yy, auc, n=n_shift)
                row = dict(side=side, h=h, feature=name, family=fam, direction=d, days=n,
                           base_rate=float(yy.mean()), auc=a, p=p, null_auc=null)
                if fam in family_split:
                    row["auc_first"] = auc(x, yy.where(f.index < family_split[fam]))
                    row["auc_second"] = auc(x, yy.where(f.index >= family_split[fam]))
                if ref_start is not None:
                    row["auc_ref_window"] = auc(x, yy.where(f.index >= ref_start))
                rows.append(row)
    return pd.DataFrame(rows)


def quantile_table(x: pd.Series, outcomes: pd.DataFrame, q: int = 5) -> pd.DataFrame:
    """Mean of each outcome column by quantile bin of x (bins from the evaluated days)."""
    j = outcomes.join(x.rename("x"), how="inner").dropna()
    j["bin"] = pd.qcut(j["x"], q, labels=False, duplicates="drop")
    t = j.groupby("bin").agg(x_lo=("x", "min"), x_hi=("x", "max"), days=("x", "size"),
                             **{c: (c, "mean") for c in outcomes.columns})
    return t


def episodes(signal: pd.Series, gap: int = 60) -> pd.DatetimeIndex:
    """Dates where a boolean signal fires after at least `gap` days without firing (first day of each episode)."""
    s = signal.fillna(False).astype(bool)
    idx = s.index[s.values]
    if len(idx) == 0:
        return idx
    keep = [idx[0]]
    for a, b in zip(idx[:-1], idx[1:]):
        if (b - a).days > gap:
            keep.append(b)
    return pd.DatetimeIndex(keep)


def pivot_profiles(features: pd.DataFrame, pivots: pd.DataFrame, span: int = 180, standardise: bool = True):
    """Mean path of each feature from -span to +span days around pivots (zigzag output: date, kind).

    Features are z-scored over the frame first (standardise=True). Returns a long frame
    [kind, feature, offset, mean, n] (n = pivots with data at that offset)."""
    z = (features - features.mean()) / features.std() if standardise else features
    offs = np.arange(-span, span + 1)
    rows = []
    for kind in ("low", "high"):
        dates = pivots.loc[pivots["kind"] == kind, "date"]
        for name in features.columns:
            P = np.array([z[name].reindex(d + pd.to_timedelta(offs, unit="D")).values for d in dates]) \
                if len(dates) else np.full((0, len(offs)), np.nan)
            mean = np.nanmean(P, axis=0) if len(P) else np.full(len(offs), np.nan)
            n = np.isfinite(P).sum(axis=0) if len(P) else np.zeros(len(offs), int)
            rows.append(pd.DataFrame(dict(kind=kind, feature=name, offset=offs, mean=mean, n=n)))
    return pd.concat(rows, ignore_index=True)
