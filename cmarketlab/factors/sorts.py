"""Quantile-sorted portfolios with overlapping holding periods.

At each day's close t, eligible names (in the universe, signal known) are ranked into n quantiles (1 = lowest
signal). A cohort is formed every day and held, buy-and-hold, for `hold` days (t+1 .. t+hold); each day's quantile
return is the average over the `hold` live cohorts (Jegadeesh & Titman 1993). hold=1 is daily rebalancing.
A name whose return is missing during the hold (delisted, no bar) earns 0 from then on.
Long-short spread = long quantile minus short quantile (one unit long, one unit short), default top minus bottom.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


def quantile_ranks(signal: pd.DataFrame, universe: pd.DataFrame, n: int = 10,
                   min_names: int | None = None) -> pd.DataFrame:
    """Quantile (1..n) of each eligible name on each day; NaN when ineligible or the day has < min_names
    (default 5 per quantile). Ties are broken by column order."""
    s = signal.where(universe.reindex_like(signal).fillna(False).astype(bool))
    s = s.where(np.isfinite(s))
    cnt = s.notna().sum(axis=1)
    rk = s.rank(axis=1, method="first")
    q = np.ceil(rk.mul(n).div(cnt.replace(0, np.nan), axis=0))
    return q.where(cnt >= (min_names if min_names is not None else 5 * n), axis=0)


@dataclass
class SortResult:
    returns: pd.DataFrame        # daily gross returns: columns 1..n and "LS"
    turnover: pd.DataFrame       # daily turnover of each quantile leg (buys + sells, fraction of the leg)
    names: pd.DataFrame          # names per quantile at formation
    net_ls: pd.Series            # LS after costs
    n: int
    hold: int
    cost_bps: float
    legs: tuple[int, int]        # (long quantile, short quantile)

    @property
    def ls(self) -> pd.Series:
        return self.returns["LS"]


def _leg_weights(mask: pd.DataFrame, base: pd.DataFrame | None) -> pd.DataFrame:
    w = mask.astype(float) if base is None else base.where(mask).clip(lower=0).fillna(0.0)
    return w.div(w.sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0)


def quantile_portfolios(signal: pd.DataFrame, ret: pd.DataFrame, universe: pd.DataFrame, n: int = 10,
                        hold: int = 7, weight: pd.DataFrame | None = None, cost_bps: float = 4.0,
                        min_names: int | None = None, legs: tuple[int, int] | None = None) -> SortResult:
    """Daily returns of the n quantile portfolios and the long-short spread.

    signal, universe, weight: known at day t's close (row t). ret: total return of day t (row t).
    weight: None = equal weight within each quantile, else a non-negative panel (e.g. trailing OI value).
    cost_bps: cost per unit traded, each side (fee + slippage); net LS = LS - cost x (turnover long + short).
    legs: (long quantile, short quantile); default (n, 1).
    """
    idx = signal.index
    r = ret.reindex(index=idx, columns=signal.columns).fillna(0.0).to_numpy()
    q = quantile_ranks(signal, universe, n, min_names)
    L = np.vstack([np.zeros((1, r.shape[1])), np.cumsum(np.log1p(r), axis=0)])   # L[t+1] = log growth to t
    T_ = len(idx)
    out, turn, names = {}, {}, {}
    for k in range(1, n + 1):
        mask = q.eq(k)
        w0 = _leg_weights(mask, weight).to_numpy()
        names[k] = mask.sum(axis=1)
        acc = np.zeros(T_)
        live = np.zeros(T_)
        for h in range(1, hold + 1):
            # day t (>= h) holds the cohort formed at t-h, drifted by growth over t-h+1 .. t-1
            wf = w0[:-h]
            drift = np.exp(L[h:T_] - L[1:T_ - h + 1])                 # L[t] - L[t-h+1]
            wd = wf * drift
            tot = wd.sum(axis=1)
            num = (wd * r[h:]).sum(axis=1)
            ok = tot > 0
            acc[h:][ok] += num[ok] / tot[ok]
            live[h:][ok] += 1
        out[k] = pd.Series(np.where(live == hold, acc / np.maximum(live, 1), np.nan), index=idx)
        # each day 1/hold of the leg is replaced: the new cohort against the one formed `hold` days earlier
        prev = np.vstack([np.zeros((hold, w0.shape[1])), w0[:-hold]])
        turn[k] = pd.Series(np.abs(w0 - prev).sum(axis=1) / hold, index=idx)
    R = pd.DataFrame(out)
    lg = legs or (n, 1)
    R["LS"] = R[lg[0]] - R[lg[1]]
    T = pd.DataFrame(turn).shift(1)      # trades at t's close show up in day t+1's return
    net = R["LS"] - cost_bps / 1e4 * (T[lg[0]] + T[lg[1]])
    first = R["LS"].first_valid_index()
    if first is not None:
        R, T, net = R.loc[first:], T.loc[first:], net.loc[first:]
    return SortResult(returns=R, turnover=T, names=pd.DataFrame(names), net_ls=net, n=n, hold=hold,
                      cost_bps=cost_bps, legs=lg)
