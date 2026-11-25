"""Per-coin characteristics for cross-sectional factor sorts. Inputs are wide daily panels (index = UTC day,
columns = symbols); outputs have the same shape and use only data up to each day (the value on day t is known at
day t's close).
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def momentum(close: pd.DataFrame, n: int, skip: int = 0) -> pd.DataFrame:
    """Log return from day t-n to day t-skip (skip > 0 leaves out the most recent days, e.g. short-term reversal)."""
    lc = np.log(close)
    return lc.shift(skip) - lc.shift(n)


def volume_level(quote_volume: pd.DataFrame, n: int = 30) -> pd.DataFrame:
    """Log of the trailing n-day mean daily quote volume (size / liquidity)."""
    return np.log(quote_volume.rolling(n, min_periods=n // 2).mean())


def volume_shock(quote_volume: pd.DataFrame, short: int = 7, long: int = 90) -> pd.DataFrame:
    """Log ratio of the short to the long trailing mean of daily quote volume (abnormal attention)."""
    s = quote_volume.rolling(short, min_periods=short).mean()
    lg = quote_volume.rolling(long, min_periods=long // 2).mean()
    return np.log(s / lg)


def turnover(quote_volume: pd.DataFrame, oi_value: pd.DataFrame, n: int = 30) -> pd.DataFrame:
    """Log of trailing n-day volume / open interest value (how fast positions churn: speculative activity)."""
    v = quote_volume.rolling(n, min_periods=n // 2).mean()
    o = oi_value.rolling(n, min_periods=n // 2).mean()
    return np.log(v / o.where(o > 0))


def funding_carry(funding: pd.DataFrame, n: int = 7) -> pd.DataFrame:
    """Trailing n-day mean of daily funding (fraction per day; positive = longs pay), annualised."""
    return funding.rolling(n, min_periods=max(1, n // 2)).mean() * 365.25


# ---------------------------------------------------------------- helpers
def _mp(n: int) -> int:
    return max(2, int(n * 0.6))


def rolling_beta(ret: pd.DataFrame, mkt: pd.Series, n: int = 90, downside: bool = False) -> pd.DataFrame:
    """Rolling OLS beta of each coin's daily return on a market return (downside: market-down days only)."""
    m = mkt.reindex(ret.index)
    if downside:
        keep = m < 0
        ret, m = ret.where(keep, axis=0), m.where(keep)
    mm = pd.DataFrame(np.repeat(m.to_numpy()[:, None], ret.shape[1], axis=1), index=ret.index,
                      columns=ret.columns).where(ret.notna())
    mp = _mp(n) // 2 if downside else _mp(n)
    cov = (ret * mm).rolling(n, min_periods=mp).mean() - ret.rolling(n, min_periods=mp).mean() * \
        mm.rolling(n, min_periods=mp).mean()
    var = mm.rolling(n, min_periods=mp).var(ddof=0)
    return cov / var


# ---------------------------------------------------------------- momentum / trend
def residual_momentum(ret: pd.DataFrame, mkt: pd.Series, n: int = 30, beta_n: int = 90) -> pd.DataFrame:
    """Sum over n days of market-residual returns (beta from the trailing beta_n days), scaled by residual vol."""
    b = rolling_beta(ret, mkt, beta_n)
    e = ret - b.mul(mkt.reindex(ret.index), axis=0)
    return e.rolling(n, min_periods=_mp(n)).sum() / e.rolling(n, min_periods=_mp(n)).std()


def high_proximity(close: pd.DataFrame, high: pd.DataFrame, n: int = 180) -> pd.DataFrame:
    """log(close / highest high of n days): 0 at a new high (George-Hwang 52-week-high momentum)."""
    return np.log(close / high.rolling(n, min_periods=_mp(n)).max())


def up_day_share(ret: pd.DataFrame, n: int = 30) -> pd.DataFrame:
    """Share of up days in the last n days (momentum consistency, the frog-in-the-pan measure)."""
    return (ret > 0).astype(float).where(ret.notna()).rolling(n, min_periods=_mp(n)).mean()


def ma_ratio(close: pd.DataFrame, n: int = 50) -> pd.DataFrame:
    """log(close / n-day simple MA)."""
    return np.log(close / close.rolling(n, min_periods=_mp(n)).mean())


def ma_cross(close: pd.DataFrame, fast: int = 20, slow: int = 100) -> pd.DataFrame:
    """log(fast MA / slow MA)."""
    return np.log(close.rolling(fast, min_periods=_mp(fast)).mean() / close.rolling(slow, min_periods=_mp(slow)).mean())


# ---------------------------------------------------------------- risk / lottery
def realised_vol(ret: pd.DataFrame, n: int = 30) -> pd.DataFrame:
    return ret.rolling(n, min_periods=_mp(n)).std()


def idio_vol(ret: pd.DataFrame, mkt: pd.Series, n: int = 30, beta_n: int = 90) -> pd.DataFrame:
    """Std of market-residual daily returns over n days."""
    b = rolling_beta(ret, mkt, beta_n)
    e = ret - b.mul(mkt.reindex(ret.index), axis=0)
    return e.rolling(n, min_periods=_mp(n)).std()


def skewness(ret: pd.DataFrame, n: int = 30) -> pd.DataFrame:
    return ret.rolling(n, min_periods=_mp(n)).skew()


def max_return(ret: pd.DataFrame, n: int = 30, k: int = 1, lowest: bool = False) -> pd.DataFrame:
    """Mean of the k largest (or most negative, lowest=True) daily returns in n days (Bali et al. MAX)."""
    if k == 1:
        r = ret.rolling(n, min_periods=_mp(n))
        return r.min() if lowest else r.max()
    a = ret.to_numpy()
    out = np.full(a.shape, np.nan)
    for t in range(n - 1, len(a)):
        w = a[t - n + 1:t + 1]
        ok = (~np.isnan(w)).sum(axis=0) >= _mp(n)
        s = np.sort(np.where(np.isnan(w), np.inf if lowest else -np.inf, w), axis=0)
        sel = s[:k] if lowest else s[-k:]
        out[t] = np.where(ok, sel.mean(axis=0), np.nan)
    return pd.DataFrame(out, index=ret.index, columns=ret.columns)


# ---------------------------------------------------------------- size / age / liquidity
def log_size(x: pd.DataFrame, n: int = 30) -> pd.DataFrame:
    """Log of the trailing n-day mean (market cap or OI value)."""
    return np.log(x.where(x > 0).rolling(n, min_periods=max(1, n // 3)).mean())


def listing_age(close: pd.DataFrame) -> pd.DataFrame:
    """log(days with a close so far)."""
    return np.log(close.notna().cumsum().where(close.notna()))


def amihud(ret: pd.DataFrame, quote_volume: pd.DataFrame, n: int = 30) -> pd.DataFrame:
    """log of the mean |return| per $1M traded over n days (Amihud illiquidity)."""
    x = ret.abs() / (quote_volume.where(quote_volume > 0) / 1e6)
    return np.log(x.rolling(n, min_periods=_mp(n)).mean())


def chl_spread(close: pd.DataFrame, high: pd.DataFrame, low: pd.DataFrame, n: int = 30) -> pd.DataFrame:
    """Abdi-Ranaldo (2017) close-high-low bid-ask spread estimate over n days (negative estimates set to 0).
    Each term uses day t-1's close and the mid-ranges of days t-1 and t, so the value on day t is known at t."""
    c, eta = np.log(close), (np.log(high) + np.log(low)) / 2
    s2 = 4 * (c.shift(1) - eta.shift(1)) * (c.shift(1) - eta)
    return np.sqrt(s2.rolling(n, min_periods=_mp(n)).mean().clip(lower=0))


def range_vol(high: pd.DataFrame, low: pd.DataFrame, n: int = 30) -> pd.DataFrame:
    """Parkinson range volatility over n days."""
    hl = np.log(high / low) ** 2 / (4 * np.log(2))
    return np.sqrt(hl.rolling(n, min_periods=_mp(n)).mean())


# ---------------------------------------------------------------- perp microstructure
def oi_change(open_interest: pd.DataFrame, n: int = 7, smooth: int = 3) -> pd.DataFrame:
    """n-day log change of open interest in coins (smoothed over `smooth` days)."""
    return np.log(open_interest.where(open_interest > 0).rolling(smooth, min_periods=1).mean()).diff(n)


def leverage(oi_value: pd.DataFrame, marketcap: pd.DataFrame, n: int = 7) -> pd.DataFrame:
    """log(OI value / market cap), n-day means."""
    o = oi_value.rolling(n, min_periods=1).mean()
    m = marketcap.where(marketcap > 0).rolling(n, min_periods=1).mean()
    return np.log(o / m)


def liquidation_ratio(liq: pd.DataFrame, oi_value: pd.DataFrame, n: int = 7) -> pd.DataFrame:
    """n-day liquidations / mean OI value."""
    return liq.rolling(n, min_periods=1).sum() / oi_value.where(oi_value > 0).rolling(n, min_periods=1).mean()


def liquidation_imbalance(long_liq: pd.DataFrame, short_liq: pd.DataFrame, n: int = 7) -> pd.DataFrame:
    """(long - short) / (long + short) liquidations over n days (+1: only longs liquidated)."""
    lo, sh = long_liq.rolling(n, min_periods=1).sum(), short_liq.rolling(n, min_periods=1).sum()
    tot = lo + sh
    return (lo - sh) / tot.where(tot > 0)


# ---------------------------------------------------------------- technical analysis
def rsi(close: pd.DataFrame, n: int = 14) -> pd.DataFrame:
    """Wilder RSI (0-100)."""
    d = close.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, min_periods=n).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, min_periods=n).mean()
    return 100 - 100 / (1 + up / dn)


def bollinger_pctb(close: pd.DataFrame, n: int = 20, k: float = 2.0) -> pd.DataFrame:
    """Bollinger %B: 0 at the lower band, 1 at the upper band."""
    m, s = close.rolling(n, min_periods=n).mean(), close.rolling(n, min_periods=n).std()
    return (close - (m - k * s)) / (2 * k * s)


def macd_hist(close: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    """MACD histogram scaled by price."""
    macd = close.ewm(span=fast, min_periods=slow).mean() - close.ewm(span=slow, min_periods=slow).mean()
    return (macd - macd.ewm(span=signal, min_periods=signal).mean()) / close


def stochastic_k(close: pd.DataFrame, high: pd.DataFrame, low: pd.DataFrame, n: int = 14) -> pd.DataFrame:
    """%K: position of the close in the n-day high-low range (0-1)."""
    hh, ll = high.rolling(n, min_periods=n).max(), low.rolling(n, min_periods=n).min()
    rng = hh - ll
    return (close - ll) / rng.where(rng > 0)


def close_location(close: pd.DataFrame, high: pd.DataFrame, low: pd.DataFrame, n: int = 7) -> pd.DataFrame:
    """Mean close location value over n days: +1 closes at the high, -1 at the low (buying / selling pressure)."""
    rng = high - low
    clv = ((close - low) - (high - close)) / rng.where(rng > 0)
    return clv.rolling(n, min_periods=_mp(n)).mean()


def signed_volume(ret: pd.DataFrame, quote_volume: pd.DataFrame, n: int = 30) -> pd.DataFrame:
    """Sum of sign(return) x volume / total volume over n days (OBV-style accumulation, in [-1, 1])."""
    sv = np.sign(ret) * quote_volume
    return sv.rolling(n, min_periods=_mp(n)).sum() / quote_volume.rolling(n, min_periods=_mp(n)).sum()


def price_volume_corr(ret: pd.DataFrame, quote_volume: pd.DataFrame, n: int = 30) -> pd.DataFrame:
    """Correlation of daily returns with daily log volume changes over n days."""
    dv = np.log(quote_volume.where(quote_volume > 0)).diff()
    return ret.rolling(n, min_periods=_mp(n)).corr(dv)


def vol_compression(high: pd.DataFrame, low: pd.DataFrame, short: int = 14, long: int = 90) -> pd.DataFrame:
    """log(short-window range vol / long-window range vol): < 0 = volatility squeeze."""
    return np.log(range_vol(high, low, short) / range_vol(high, low, long))
