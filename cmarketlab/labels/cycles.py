"""Cycle targets. These look into the future by construction: use them only as evaluation labels."""
from __future__ import annotations

import numpy as np
import pandas as pd


def zigzag(close: pd.Series, threshold: float = 0.3) -> pd.DataFrame:
    """Alternating swing highs and lows on closes: a swing ends when price reverses by more than `threshold`
    (0.3 = 30 %) from the running extreme. Returns DataFrame [date, price, kind] with kind 'high' / 'low'.
    The last pivot is provisional (the swing after it has not reversed yet)."""
    c = close.dropna()
    piv, trend = [], 0
    ext_i, ext_p = c.index[0], c.iloc[0]
    lo_i, lo_p, hi_i, hi_p = ext_i, ext_p, ext_i, ext_p
    for t, p in c.items():
        if trend == 0:
            if p > hi_p:
                hi_i, hi_p = t, p
            if p < lo_p:
                lo_i, lo_p = t, p
            if p >= lo_p * (1 + threshold):
                piv.append((lo_i, lo_p, "low"))
                trend, ext_i, ext_p = 1, t, p
            elif p <= hi_p * (1 - threshold):
                piv.append((hi_i, hi_p, "high"))
                trend, ext_i, ext_p = -1, t, p
        elif trend == 1:
            if p > ext_p:
                ext_i, ext_p = t, p
            elif p <= ext_p * (1 - threshold):
                piv.append((ext_i, ext_p, "high"))
                trend, ext_i, ext_p = -1, t, p
        else:
            if p < ext_p:
                ext_i, ext_p = t, p
            elif p >= ext_p * (1 + threshold):
                piv.append((ext_i, ext_p, "low"))
                trend, ext_i, ext_p = 1, t, p
    piv.append((ext_i, ext_p, "high" if trend == 1 else "low"))
    return pd.DataFrame(piv, columns=["date", "price", "kind"])


def _fwd_roll(x: pd.Series, h: int, fn: str) -> pd.Series:
    """fn over x[t+1 .. t+h]; NaN when fewer than h future rows exist."""
    r = getattr(x[::-1].rolling(h, min_periods=h), fn)()[::-1]
    return r.shift(-1)


def forward_outcomes(close: pd.Series, horizon: int, low: pd.Series | None = None,
                     high: pd.Series | None = None) -> pd.DataFrame:
    """Per day t (rows = days): fwd_ret = close[t+h]/close[t]-1, fwd_min = min(low[t+1..t+h])/close[t]-1
    (worst further decline), fwd_max = max(high[t+1..t+h])/close[t]-1 (best further rise)."""
    low = close if low is None else low
    high = close if high is None else high
    return pd.DataFrame({
        "fwd_ret": close.shift(-horizon) / close - 1,
        "fwd_min": _fwd_roll(low, horizon, "min") / close - 1,
        "fwd_max": _fwd_roll(high, horizon, "max") / close - 1,
    }, index=close.index)


def cycle_targets(close: pd.Series, horizon: int, low: pd.Series | None = None, high: pd.Series | None = None,
                  trend: pd.Series | None = None, move: float = 0.15):
    """Binary "extreme near" targets (study 01 definitions), NaN where not applicable.

    bottom: on bear days (trend < 0), 1 if the lowest low of the next `horizon` days is less than `move` below
            today's close;
    top:    on bull days (trend > 0), 1 if the highest high of the next `horizon` days is less than `move` above.
    trend defaults to log(close / 200-day MA). Returns (bottom, top, forward_outcomes frame)."""
    o = forward_outcomes(close, horizon, low, high)
    if trend is None:
        trend = np.log(close / close.rolling(200, min_periods=200).mean())
    bottom = (o["fwd_min"] > -move).astype(float).where((trend < 0) & o["fwd_min"].notna())
    top = (o["fwd_max"] < move).astype(float).where((trend > 0) & o["fwd_max"].notna())
    return bottom, top, o


def pivot_context(index: pd.DatetimeIndex, pivots: pd.DataFrame, close: pd.Series | None = None) -> pd.DataFrame:
    """For each date: the next pivot (kind, days until it, its price / close - 1) and the previous pivot's kind.
    Dates after the last pivot get NaN for the 'next' columns."""
    p = pivots.sort_values("date").reset_index(drop=True)
    pos = np.searchsorted(p["date"].values, index.values, side="left")
    nxt = pd.Series(pos, index=index)
    has = nxt < len(p)
    out = pd.DataFrame(index=index)
    out["next_kind"] = np.where(has, p["kind"].reindex(nxt.clip(upper=len(p) - 1)).values, None)
    nd = pd.to_datetime(p["date"].reindex(nxt.clip(upper=len(p) - 1)).values, utc=True)
    out["days_to_next"] = np.where(has, (nd - index).days, np.nan)
    if close is not None:
        np_ = p["price"].reindex(nxt.clip(upper=len(p) - 1)).values
        out["next_vs_close"] = np.where(has, np_ / close.reindex(index).values - 1, np.nan)
    prv = pos - 1 + (has & (p["date"].reindex(nxt.clip(upper=len(p) - 1)).values == index.values))
    out["prev_kind"] = np.where(prv >= 0, p["kind"].reindex(np.clip(prv, 0, None)).values, None)
    return out
