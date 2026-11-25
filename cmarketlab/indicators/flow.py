"""Order flow, perp-spot basis and dominance. Inputs are daily Series / wide panels (index = UTC day); trailing only.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def taker_imbalance(taker_buy: pd.Series, volume: pd.Series, window: int = 30) -> pd.Series:
    """Normalised order imbalance over `window` days: (buy - sell) / total taker volume, in [-1, 1].
    taker_buy and volume in the same units (e.g. klines' taker_buy_quote_volume and quote_volume)."""
    b = taker_buy.rolling(window, min_periods=window // 2).sum()
    v = volume.rolling(window, min_periods=window // 2).sum()
    return (2 * b - v) / v


def basis(perp_close: pd.Series, spot_close: pd.Series, smooth: int = 30) -> pd.Series:
    """Mean of the daily log gap perp / spot over `smooth` days (positive = perp at a premium)."""
    g = np.log(perp_close / spot_close.reindex(perp_close.index))
    return g.rolling(smooth, min_periods=smooth // 2).mean()


def daily_funding(events: pd.Series) -> pd.Series:
    """Sum of funding events per UTC day (fraction per day)."""
    return events.groupby(events.index.floor("D")).sum()


def share_of_events(events: pd.Series, above: float | None = None, below: float | None = None,
                    window: int = 30) -> pd.Series:
    """Daily share of funding events in the last `window` days above / below a threshold (per-event rate)."""
    cond = pd.Series(True, index=events.index)
    if above is not None:
        cond &= events > above
    if below is not None:
        cond &= events < below
    hit = cond.astype(float).groupby(events.index.floor("D")).sum()
    n = events.groupby(events.index.floor("D")).size().astype(float)
    return hit.rolling(window, min_periods=window // 2).sum() / n.rolling(window, min_periods=window // 2).sum()


def dominance(marketcap: pd.DataFrame, mask: pd.DataFrame, symbols, smooth: int = 7) -> pd.Series:
    """Market-cap share of `symbols` in the masked universe (7-day mean)."""
    m = marketcap.where(mask.reindex_like(marketcap).fillna(False).astype(bool))
    s = m[[c for c in symbols if c in m.columns]].sum(axis=1) / m.sum(axis=1)
    return s.where(m.sum(axis=1) > 0).rolling(smooth, min_periods=1).mean()


def rolling_corr(a: pd.Series, b: pd.Series, window: int = 90) -> pd.Series:
    """Rolling correlation of daily log returns, on the days both have data (e.g. BTC vs S&P 500 trading days)."""
    j = np.log(pd.concat([a, b], axis=1).dropna()).diff().dropna()  # returns between common days
    c = j.iloc[:, 0].rolling(window, min_periods=window * 2 // 3).corr(j.iloc[:, 1])
    return c.reindex(a.index).ffill(limit=5)
