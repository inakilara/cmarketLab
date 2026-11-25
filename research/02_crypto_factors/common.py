"""Shared definitions for project 02's parts: the characteristic catalogue, the two test versions and loaders.

Every characteristic is a wide daily panel known at day t's close (cmarketlab.indicators.xsection). Portfolios
are formed at that close and earn returns from day t+1. Deciles are sorted ascending; the long-short spread is
always D10 - D1 (high minus low), whatever the sign of the effect.

Versions (each factor is tested in both):
    top100   the 100 most liquid coins each day (30-day median volume), equal weight within deciles
    oiw      the whole crypto universe (age >= 60 d, 30-d median volume >= $1M), weighted by 30-day mean OI value
"""
from __future__ import annotations

import os
import sys
from functools import lru_cache

import pandas as pd

from cmarketlab.factors import factor_panels
from cmarketlab.indicators import xsection as xs

ROOT = os.path.dirname(os.path.abspath(__file__))
COST_BPS = 4.0          # per side, per unit traded (Binance taker fee + slippage, from experience)
HOLD = 7
N = 10
SPLIT = pd.Timestamp("2024-01-01", tz="UTC")

# name: (family, builder(P, mkt) -> panel, description[, returns]); returns "price" evaluates on price returns only
CATALOGUE = {
    # ---- momentum and trend
    "rev1":      ("momentum", lambda P, m: xs.momentum(P.close, 1), "last day's return"),
    "mom7":      ("momentum", lambda P, m: xs.momentum(P.close, 7, 1), "return t-7 .. t-1"),
    "mom14":     ("momentum", lambda P, m: xs.momentum(P.close, 14, 1), "return t-14 .. t-1"),
    "mom30":     ("momentum", lambda P, m: xs.momentum(P.close, 30, 1), "return t-30 .. t-1"),
    "mom60":     ("momentum", lambda P, m: xs.momentum(P.close, 60, 1), "return t-60 .. t-1"),
    "mom90":     ("momentum", lambda P, m: xs.momentum(P.close, 90, 1), "return t-90 .. t-1"),
    "mom180":    ("momentum", lambda P, m: xs.momentum(P.close, 180, 7), "return t-180 .. t-7"),
    "resmom30":  ("momentum", lambda P, m: xs.residual_momentum(P.ret, m, 30), "market-residual return, 30 d, "
                                                                               "scaled by residual vol"),
    "resmom90":  ("momentum", lambda P, m: xs.residual_momentum(P.ret, m, 90), "market-residual return, 90 d"),
    "hiprox180": ("momentum", lambda P, m: xs.high_proximity(P.close, P.high, 180), "close vs 180-day high"),
    "upshare30": ("momentum", lambda P, m: xs.up_day_share(P.ret, 30), "share of up days, 30 d"),
    # ---- risk and lottery
    "vol30":     ("risk", lambda P, m: xs.realised_vol(P.ret, 30), "realised vol, 30 d"),
    "ivol30":    ("risk", lambda P, m: xs.idio_vol(P.ret, m, 30), "idiosyncratic vol vs market, 30 d"),
    "rvol30":    ("risk", lambda P, m: xs.range_vol(P.high, P.low, 30), "high-low range vol, 30 d"),
    "beta90":    ("risk", lambda P, m: xs.rolling_beta(P.ret, m, 90), "market beta, 90 d"),
    "dbeta90":   ("risk", lambda P, m: xs.rolling_beta(P.ret, m, 90, downside=True), "downside beta, 90 d"),
    "skew30":    ("risk", lambda P, m: xs.skewness(P.ret, 30), "skewness of daily returns, 30 d"),
    "max30":     ("risk", lambda P, m: xs.max_return(P.ret, 30), "largest daily return, 30 d (lottery)"),
    "max5_30":   ("risk", lambda P, m: xs.max_return(P.ret, 30, k=5), "mean of the 5 largest daily returns, 30 d"),
    "min30":     ("risk", lambda P, m: xs.max_return(P.ret, 30, lowest=True), "worst daily return, 30 d"),
    # ---- size, age and liquidity
    "size_oi":   ("size_liq", lambda P, m: xs.log_size(P.oi_value, 30), "log OI value, 30 d"),
    "size_mcap": ("size_liq", lambda P, m: xs.log_size(P.marketcap, 30), "log market cap, 30 d"),
    "age":       ("size_liq", lambda P, m: xs.listing_age(P.close), "log days listed"),
    "volume":    ("size_liq", lambda P, m: xs.volume_level(P.quote_volume, 30), "log daily volume, 30 d"),
    "amihud":    ("size_liq", lambda P, m: xs.amihud(P.ret, P.quote_volume, 30), "Amihud illiquidity, 30 d"),
    "spread":    ("size_liq", lambda P, m: xs.chl_spread(P.close, P.high, P.low, 30),
                  "Abdi-Ranaldo spread estimate, 30 d"),
    "turnover":  ("size_liq", lambda P, m: xs.turnover(P.quote_volume, P.oi_value, 30), "volume / OI, 30 d"),
    "vshock":    ("size_liq", lambda P, m: xs.volume_shock(P.quote_volume, 7, 90), "volume 7 d / 90 d"),
    # ---- perp microstructure
    "oi_chg7":   ("perp", lambda P, m: xs.oi_change(P.open_interest, 7), "OI (coins) change, 7 d"),
    "oi_chg30":  ("perp", lambda P, m: xs.oi_change(P.open_interest, 30), "OI (coins) change, 30 d"),
    "leverage":  ("perp", lambda P, m: xs.leverage(P.oi_value, P.marketcap, 7), "OI value / market cap"),
    "fund7":     ("perp", lambda P, m: xs.funding_carry(P.funding, 7), "funding, 7 d (total return)"),
    "fund30":    ("perp", lambda P, m: xs.funding_carry(P.funding, 30), "funding, 30 d (total return)"),
    "fund_chg":  ("perp", lambda P, m: xs.funding_carry(P.funding, 7) - xs.funding_carry(P.funding, 30),
                  "funding 7 d minus 30 d"),
    "fund7_px":  ("perp", lambda P, m: xs.funding_carry(P.funding, 7), "funding, 7 d (price return only)", "price"),
    "liq_long7": ("perp", lambda P, m: xs.liquidation_ratio(P.long_liq, P.oi_value, 7), "long liquidations / OI"),
    "liq_short7": ("perp", lambda P, m: xs.liquidation_ratio(P.short_liq, P.oi_value, 7), "short liquidations / OI"),
    "liq_imb7":  ("perp", lambda P, m: xs.liquidation_imbalance(P.long_liq, P.short_liq, 7),
                  "long minus short liquidations, share"),
    # ---- technical analysis
    "rsi14":     ("technical", lambda P, m: xs.rsi(P.close, 14), "RSI 14"),
    "bb20":      ("technical", lambda P, m: xs.bollinger_pctb(P.close, 20), "Bollinger %B, 20 d"),
    "macd":      ("technical", lambda P, m: xs.macd_hist(P.close), "MACD histogram / price"),
    "stoch14":   ("technical", lambda P, m: xs.stochastic_k(P.close, P.high, P.low, 14), "stochastic %K, 14 d"),
    "ma50":      ("technical", lambda P, m: xs.ma_ratio(P.close, 50), "close / 50-day MA"),
    "macross":   ("technical", lambda P, m: xs.ma_cross(P.close, 20, 100), "20-day MA / 100-day MA"),
    "clv7":      ("technical", lambda P, m: xs.close_location(P.close, P.high, P.low, 7), "close location in "
                                                                                          "daily range, 7 d"),
    "obv30":     ("technical", lambda P, m: xs.signed_volume(P.ret, P.quote_volume, 30), "signed volume share, 30 d"),
    "pvcorr30":  ("technical", lambda P, m: xs.price_volume_corr(P.ret, P.quote_volume, 30),
                  "return / volume-change correlation, 30 d"),
    "squeeze":   ("technical", lambda P, m: xs.vol_compression(P.high, P.low, 14, 90), "range vol 14 d / 90 d"),
}
FAMILIES = ["momentum", "risk", "size_liq", "perp", "technical"]


@lru_cache(maxsize=1)
def panels():
    """(P, mkt, versions): panels on the full crypto universe, the equal-weighted market return, and
    {version: (universe, weight)}."""
    P = factor_panels()
    top = factor_panels(top_n=100).universe
    u100 = P.universe & top.reindex_like(P.universe).fillna(False).astype(bool)
    oiw = P.oi_value.rolling(30, min_periods=10).mean()
    versions = {"top100": (u100, None), "oiw": (P.universe, oiw)}
    return P, P.market(), versions


def signal(name, P, mkt):
    return CATALOGUE[name][1](P, mkt)


def returns_for(name, P):
    spec = CATALOGUE[name]
    return P.price_ret if (len(spec) > 3 and spec[3] == "price") else P.ret


def market_for(version, P, versions):
    """Benchmark for alpha: equal-weighted top-100 return, or OI-weighted universe return."""
    u, w = versions[version]
    from cmarketlab.factors import FactorPanels
    Q = FactorPanels(**{**vars(P), "universe": u})
    return Q.market(w)


def part_dir(name):
    d = os.path.join(ROOT, name, "reports")
    os.makedirs(d, exist_ok=True)
    return d


if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
