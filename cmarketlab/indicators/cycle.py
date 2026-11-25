"""Leverage-cycle reading of BTC's mid/long-term extremes (research/01_btc_cycle/01_cycle_extremes).

Inputs are daily Series on one index:
    close          BTC daily close
    btc_oi         BTC perpetual open interest in BTC (base units), e.g. the daily cache's open_interest for BTC
    lev            aggregate crypto open interest value / aggregate market cap (indicators.market.leverage_ratio)

Readings (state from the 200-day MA):
    bear & btc_oi 90-day change <= -15 %                      -> "bottom_zone"   (leverage flushed)
    bear & btc_oi 90-day change >= +10 %                      -> "bear_building" (leverage still building: not a bottom)
    bull & lev 90-day change > +15 % on >= 30 of last 60 days  -> "top_zone"      (sustained leverage build-up)
    bull & btc_oi 90-day change <= -10 %                      -> "bull_reset"    (deleveraged bull: no top yet)
    otherwise "bear" / "bull" (neutral).
Changes are log changes of 7-day means. Thresholds were set in study 01 on 2021-12 -> 2026-10 data.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

THRESHOLDS = dict(bottom_oi=-0.15, bear_building_oi=0.10, top_lev=0.15, top_days=30, top_window=60,
                  bull_reset_oi=-0.10)


def chg90(x: pd.Series, smooth: int = 7, n: int = 90) -> pd.Series:
    """90-day log change of the 7-day mean."""
    return np.log(x.rolling(smooth).mean()).diff(n)


def leverage_inputs() -> pd.DataFrame:
    """Daily btc_oi (BTC perpetual OI in BTC) and lev (aggregate crypto OI value / market cap) from the perps
    file's daily cache, on the default crypto universe; inputs for leverage_cycle."""
    from ..data import crypto_universe, daily_panel, load_daily
    from .market import leverage_ratio
    d = load_daily()
    d = d[d["hours"] == 24]
    u = crypto_universe(d)
    oi = daily_panel(d, "oi_value").reindex(columns=u.columns)
    mc = daily_panel(d, "marketcap").reindex(columns=u.columns)
    return pd.DataFrame({"btc_oi": daily_panel(d, "open_interest")["BTC"], "lev": leverage_ratio(oi, mc, u)})


def leverage_cycle(close: pd.Series, btc_oi: pd.Series, lev: pd.Series, th: dict | None = None) -> pd.DataFrame:
    """Daily frame: ma200 (log close / 200-day MA), oi_chg90, lev_chg90, top_days (days in the last window with
    lev_chg90 above the top threshold) and `reading` (see module docstring)."""
    th = {**THRESHOLDS, **(th or {})}
    out = pd.DataFrame(index=close.index)
    out["ma200"] = np.log(close / close.rolling(200, min_periods=200).mean())
    out["oi_chg90"] = chg90(btc_oi.reindex(close.index))
    out["lev_chg90"] = chg90(lev.reindex(close.index))
    hot = out["lev_chg90"] > th["top_lev"]
    out["top_days"] = hot.astype(float).where(out["lev_chg90"].notna()).rolling(th["top_window"], min_periods=1).sum()
    bear, bull = out["ma200"] < 0, out["ma200"] > 0
    r = pd.Series(np.where(bear, "bear", np.where(bull, "bull", None)), index=close.index, dtype=object)
    r[bull & (out["oi_chg90"] <= th["bull_reset_oi"])] = "bull_reset"
    r[bull & hot & (out["top_days"] >= th["top_days"])] = "top_zone"
    r[bear & (out["oi_chg90"] >= th["bear_building_oi"])] = "bear_building"
    r[bear & (out["oi_chg90"] <= th["bottom_oi"])] = "bottom_zone"
    r[out["ma200"].isna()] = None
    out["reading"] = r
    return out
