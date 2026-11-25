"""Daily bars from the hourly perps file, built in symbol chunks (RAM) and cached in cache/perps_1d.parquet.

Daily columns per symbol (UTC days):
    open, high, low, close            USDT price
    volume                            base units;   quote_volume = sum(volume x close) in USDT
    open_interest                     base units at the day's last hour; oi_value = open_interest x close (USDT)
    funding                           sum of funding events in the day (decimal, paid by longs)
    est_funding                       mean of hourly estimated funding
    long_liq, short_liq               liquidated USD in the day
    marketcap                         last value of the day (USD)
    hours                             hours with a bar (24 = complete day)
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..paths import PERPS_1H, SHARED, cache_path
from .perps import load_perps, symbols

DERIBIT_BTC_PERP = SHARED / "deribit-futures" / "deribit_BTC_perpetual_1h.parquet"


def to_daily(df: pd.DataFrame) -> pd.DataFrame:
    """Hourly long table (load_perps output, all FIELDS) -> daily long table [symbol, date, ...]."""
    d = df.assign(day=df["date"].dt.floor("D"), qv=df["volume"] * df["close"])
    g = d.groupby(["symbol", "day"], sort=True, observed=True)
    out = pd.DataFrame({
        "open": g["open"].first(), "high": g["high"].max(), "low": g["low"].min(), "close": g["close"].last(),
        "volume": g["volume"].sum(), "quote_volume": g["qv"].sum(),
        "open_interest": g["open_interest"].last(),
        "funding": g["funding_rate"].sum(min_count=1), "est_funding": g["est_funding_rate"].mean(),
        "long_liq": g["long_liquidations"].sum(min_count=1), "short_liq": g["short_liquidations"].sum(min_count=1),
        "marketcap": g["marketcap"].last(), "hours": g["close"].size(),
    })
    out["oi_value"] = out["open_interest"] * out["close"]
    out["funding"] = out["funding"].fillna(0.0)
    return out.reset_index().rename(columns={"day": "date"})


def build_daily(chunk: int = 60, path=PERPS_1H, out=None, force: bool = False) -> pd.DataFrame:
    """Build (or read) the daily cache for every symbol."""
    out = out or cache_path("perps_1d.parquet")
    if out.exists() and not force:
        return pd.read_parquet(out)
    syms = symbols(path)
    parts = [to_daily(load_perps(syms[i:i + chunk], path=path)) for i in range(0, len(syms), chunk)]
    d = pd.concat(parts, ignore_index=True)
    d.to_parquet(out, index=False)
    return d


def load_daily(fields=None) -> pd.DataFrame:
    """Daily long table from the cache (built on first use)."""
    p = cache_path("perps_1d.parquet")
    if not p.exists():
        build_daily()
    return pd.read_parquet(p, columns=None if fields is None else ["symbol", "date", *fields])


def daily_panel(d: pd.DataFrame, field: str) -> pd.DataFrame:
    """Wide daily frame (index = every day in range, columns = symbols)."""
    w = d.pivot(index="date", columns="symbol", values=field)
    return w.reindex(pd.date_range(w.index.min(), w.index.max(), freq="D", name="date"))


def btc_daily_long() -> pd.DataFrame:
    """BTC daily OHLCV from the Deribit BTC perpetual (2018-08-14 onward), for price-only studies on a longer
    history than the Binance file. Columns: open, high, low, close, volume (BTC); index = UTC day."""
    h = pd.read_parquet(DERIBIT_BTC_PERP)
    t = pd.to_datetime(h["timestamp"], unit="ms", utc=True)
    h = h.set_index(t)
    d = pd.DataFrame({"open": h["open"].resample("D").first(), "high": h["high"].resample("D").max(),
                      "low": h["low"].resample("D").min(), "close": h["close"].resample("D").last(),
                      "volume": h["volume"].resample("D").sum()})
    d.index.name = "date"
    return d.loc[d.index >= d.index.min() + pd.Timedelta("1D")].dropna(subset=["close"]).astype(np.float64)
