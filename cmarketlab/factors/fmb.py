"""Fama-MacBeth cross-sectional regressions of forward returns on characteristics.

Each characteristic is turned into a cross-sectional rank scaled to [-0.5, 0.5] on each formation date (missing =
0, the cross-sectional middle), so a slope is the forward-return difference between the highest- and lowest-ranked
coin, holding the other characteristics fixed. Formation dates are every `every` days (non-overlapping when
every = horizon); slopes are averaged over dates with Newey-West t-statistics.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .stats import newey_west_t


def forward_returns(ret: pd.DataFrame, h: int = 7) -> pd.DataFrame:
    """Compounded return over days t+1 .. t+h (missing days earn 0), on row t."""
    lg = np.log1p(ret.fillna(0.0)).cumsum()
    return np.expm1(lg.shift(-h) - lg)


def cs_rank(x: pd.DataFrame, universe: pd.DataFrame) -> pd.DataFrame:
    """Cross-sectional rank within the universe, scaled to [-0.5, 0.5]."""
    s = x.where(universe.reindex_like(x).fillna(False).astype(bool))
    s = s.where(np.isfinite(s))
    r = s.rank(axis=1, pct=True)
    n = s.notna().sum(axis=1)
    lo = 1.0 / n
    return (r.sub(lo, axis=0)).div((1 - lo).replace(0, np.nan), axis=0) - 0.5


def fama_macbeth(chars: dict, fwd: pd.DataFrame, universe: pd.DataFrame, every: int = 7, weight=None,
                 winsor: float = 0.01, min_names: int = 30, h: int = 7, lags: int = 4):
    """Returns (slopes: date x characteristic, summary: mean slope annualised, NW t, share of dates > 0).

    chars: {name: wide panel known at day t's close}; fwd: forward returns on row t (forward_returns).
    weight: None (OLS) or a non-negative panel for WLS (e.g. trailing OI value).
    winsor: forward returns are clipped at these cross-sectional quantiles on each date.
    """
    u = universe.reindex_like(fwd).fillna(False).astype(bool)
    R = {k: cs_rank(v.reindex_like(fwd), u) for k, v in chars.items()}
    names = list(R)
    dates = fwd.index[::every]
    rows = {}
    for t in dates:
        m = u.loc[t] & fwd.loc[t].notna()
        if m.sum() < min_names:
            continue
        y = fwd.loc[t, m]
        if winsor:
            y = y.clip(y.quantile(winsor), y.quantile(1 - winsor))
        X = np.column_stack([np.ones(m.sum())] + [R[k].loc[t, m].fillna(0.0).to_numpy() for k in names])
        w = None if weight is None else weight.loc[t, m].fillna(0.0).clip(lower=0).to_numpy()
        if w is not None:
            if w.sum() <= 0:
                continue
            sw = np.sqrt(w / w.sum())
            b = np.linalg.lstsq(X * sw[:, None], y.to_numpy() * sw, rcond=None)[0]
        else:
            b = np.linalg.lstsq(X, y.to_numpy(), rcond=None)[0]
        rows[t] = b[1:]
    S = pd.DataFrame(rows, index=names).T
    summ = pd.DataFrame({"ann_slope": S.mean() * 365 / h,
                         "t_nw": [newey_west_t(S[c], lags) for c in names],
                         "share_pos": (S > 0).mean(),
                         "dates": S.notna().sum()})
    return S, summ
