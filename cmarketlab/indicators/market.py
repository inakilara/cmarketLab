"""Whole-market measures from wide daily panels (index = day, columns = symbols) and a boolean universe mask of the
same shape (cmarketlab.data.universe.crypto_universe). Each returns a daily Series. Trailing only.

Panels come from cmarketlab.data.daily_panel on the daily cache: close, quote_volume, oi_value, funding (daily sum
of events), long_liq, short_liq, marketcap.

Groups: breadth (breadth_above_ma, breadth_extremes), funding (weighted_funding, share_negative_funding,
funding_cross_section), leverage (leverage_ratio, liquidation_intensity), rotation (alt_relative_strength,
volume_share, alt_volume_share, oi_share), dispersion and correlation (return_dispersion, corr_to_base), froth
(share_big_gainers, volume_ratio, listings).
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def _align(mask, *panels):
    cols = mask.columns
    out = [p.reindex(index=mask.index, columns=cols) for p in panels]
    return out[0] if len(out) == 1 else out


def _share(cond, mask):
    """Share of True among universe symbols where cond is defined (cond: bool/float frame with NaN = undefined)."""
    cond = cond.astype("float64")
    m = mask & cond.notna()
    n = m.sum(axis=1).astype("float64")
    return cond.where(m).sum(axis=1) / n.where(n > 0)


def breadth_above_ma(close, mask, n: int = 100):
    """Share of universe symbols closing above their n-day moving average."""
    close = _align(mask, close)
    ma = close.rolling(n, min_periods=n).mean()
    return _share((close > ma).where(ma.notna()), mask)


def breadth_extremes(close, mask, n: int = 90, smooth: int = 7):
    """(share at a new n-day closing high, share at a new n-day low), each averaged over `smooth` days."""
    close = _align(mask, close)
    full = close.rolling(n, min_periods=n)
    hi = (close >= full.max()).where(close.notna() & full.max().notna())
    lo = (close <= full.min()).where(close.notna() & full.min().notna())
    return (_share(hi, mask).rolling(smooth, min_periods=1).mean(),
            _share(lo, mask).rolling(smooth, min_periods=1).mean())


def weighted_funding(funding, oi_value, mask, window: int = 30):
    """Open-interest-weighted market funding over the trailing window, annualised (decimal per year paid by
    longs). Weights are each symbol's mean OI value over the window."""
    funding, oi_value = _align(mask, funding, oi_value)
    f = funding.where(mask).rolling(window, min_periods=window // 2).mean() * 365.25
    w = oi_value.where(mask).rolling(window, min_periods=window // 2).mean()
    ok = f.notna() & w.notna()
    return (f.where(ok) * w.where(ok)).sum(axis=1) / w.where(ok).sum(axis=1).replace(0, np.nan)


def share_negative_funding(funding, mask, window: int = 30):
    """Share of universe symbols whose trailing `window`-day funding sum is negative (shorts pay)."""
    funding = _align(mask, funding)
    s = funding.where(mask).rolling(window, min_periods=window // 2).sum()
    return _share((s < 0).where(s.notna()), mask)


def leverage_ratio(oi_value, marketcap, mask):
    """Aggregate open interest value / aggregate market cap, over symbols with both (daily)."""
    oi_value, marketcap = _align(mask, oi_value, marketcap)
    ok = mask & oi_value.notna() & marketcap.notna() & (marketcap > 0)
    return oi_value.where(ok).sum(axis=1) / marketcap.where(ok).sum(axis=1).replace(0, np.nan)


def liquidation_intensity(long_liq, short_liq, oi_value, mask, window: int = 7):
    """(long, short) liquidated USD over `window` days / mean aggregate OI value over the same days."""
    long_liq, short_liq, oi_value = _align(mask, long_liq, short_liq, oi_value)
    oi = oi_value.where(mask).sum(axis=1).rolling(window, min_periods=1).mean()
    lo = long_liq.where(mask).sum(axis=1).rolling(window, min_periods=1).sum()
    sh = short_liq.where(mask).sum(axis=1).rolling(window, min_periods=1).sum()
    return lo / oi, sh / oi


def alt_relative_strength(close, mask, base: str = "BTC", n: int = 90):
    """Median n-day log return of universe alts minus the base's n-day log return."""
    close = _align(mask, close)
    r = np.log(close / close.shift(n))
    alts = r.drop(columns=[base]).where(mask.drop(columns=[base]))
    return alts.median(axis=1) - r[base]


def share_big_gainers(close, mask, n: int = 90, gain: float = 1.0):
    """Share of universe symbols up more than `gain` (1.0 = +100 %) over n days."""
    close = _align(mask, close)
    r = close / close.shift(n) - 1
    return _share((r > gain).where(r.notna()), mask)


def corr_to_base(close, mask, base: str = "BTC", window: int = 60):
    """Median rolling correlation of universe alts' daily log returns with the base."""
    close = _align(mask, close)
    r = np.log(close).diff()
    c = r.drop(columns=[base]).rolling(window, min_periods=window // 2).corr(r[base])
    return c.where(mask.drop(columns=[base])).median(axis=1)


def volume_ratio(quote_volume, mask, short: int = 30, long: int = 365):
    """Aggregate universe volume: short-window mean / long-window mean."""
    qv = _align(mask, quote_volume).where(mask).sum(axis=1)
    return qv.rolling(short, min_periods=short).mean() / qv.rolling(long, min_periods=long // 2).mean()


def alt_volume_share(quote_volume, mask, majors=("BTC", "ETH"), window: int = 30):
    """Share of universe volume outside the majors, trailing window."""
    qv = _align(mask, quote_volume).where(mask)
    tot = qv.sum(axis=1).rolling(window, min_periods=1).sum()
    maj = qv[[m for m in majors if m in qv.columns]].sum(axis=1).rolling(window, min_periods=1).sum()
    return 1 - maj / tot


def listings(close, window: int = 90, start=None):
    """Number of symbols whose first bar falls in the trailing window (new-listing pace). Listings before
    `start` (default: the first date + window, i.e. the file's initial roster) are not counted."""
    first = close.apply(pd.Series.first_valid_index)
    start = start or close.index[0] + pd.Timedelta(days=window)
    first = first[first >= start]
    s = pd.Series(1, index=pd.DatetimeIndex(first.tolist())).groupby(level=0).sum()
    s = s.reindex(close.index, fill_value=0)
    return s.rolling(window, min_periods=1).sum().where(close.index >= start)


# ---- rotation, funding dispersion, return dispersion ---------------------------------------------------------

def _xs_spread(x, mask, kind: str = "iqr"):
    """Cross-sectional spread per day over universe symbols: 'iqr' (interquartile range / 1.349, a robust std:
    unaffected by a few extreme coins) or 'std'."""
    v = x.where(mask)
    if kind == "std":
        return v.std(axis=1)
    return (v.quantile(0.75, axis=1) - v.quantile(0.25, axis=1)) / 1.349


def volume_share(quote_volume, mask, symbols, window: int = 30):
    """Share of universe volume traded in `symbols` (e.g. ["BTC"]), trailing `window` days."""
    qv = _align(mask, quote_volume).where(mask)
    tot = qv.sum(axis=1).rolling(window, min_periods=1).sum()
    part = qv[[s for s in symbols if s in qv.columns]].sum(axis=1).rolling(window, min_periods=1).sum()
    return part / tot


def oi_share(oi_value, mask, symbols, smooth: int = 7):
    """Share of universe open interest (USD) held in `symbols`, `smooth`-day mean."""
    oi = _align(mask, oi_value).where(mask)
    tot = oi.sum(axis=1).replace(0, np.nan)
    return (oi[[s for s in symbols if s in oi.columns]].sum(axis=1) / tot).rolling(smooth, min_periods=1).mean()


def funding_cross_section(funding, mask, window: int = 30, kind: str = "iqr"):
    """(median, spread) across universe symbols of each symbol's trailing `window`-day funding, annualised
    (decimal per year paid by longs). Equal-weighted: every coin counts once, unlike weighted_funding."""
    f = _align(mask, funding).where(mask).rolling(window, min_periods=window // 2).mean() * 365.25
    f = f.where(mask)
    return f.median(axis=1), _xs_spread(f, mask, kind)


def return_dispersion(close, mask, n: int = 1, smooth: int = 30, kind: str = "iqr"):
    """Cross-sectional spread of n-day log returns across universe symbols, averaged over `smooth` days
    (n = 1, smooth = 30: a 30-day 'cross-sectional volatility' of daily returns)."""
    close = _align(mask, close)
    r = np.log(close / close.shift(n))
    d = _xs_spread(r, mask & r.notna(), kind)
    return d.rolling(smooth, min_periods=smooth // 2).mean()
