"""Binance public market data (no API key): klines from spot and USD-M futures, cached in cache/.

    klines("BTCUSDT", "1d", market="spot")   spot, from 2017-08-17 for BTCUSDT
    klines("BTCUSDT", "1d", market="usdm")   USDT-margined perpetual, from 2019-09-08 for BTCUSDT
    btc_daily()                              BTC daily OHLCV for long price studies (spot)

The cache is extended incrementally: only bars after the last cached one are fetched. The last (still open) bar
is never cached.
"""
from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request

import pandas as pd

from ..paths import cache_path

BASE = {"spot": "https://api.binance.com/api/v3/klines", "usdm": "https://fapi.binance.com/fapi/v1/klines"}
LIMIT = {"spot": 1000, "usdm": 1500}
COLS = ["open_time", "open", "high", "low", "close", "volume", "close_time", "quote_volume", "trades",
        "taker_buy_volume", "taker_buy_quote_volume", "ignore"]


def _get(url: str, params: dict, tries: int = 5):
    q = url + "?" + urllib.parse.urlencode(params)
    for k in range(tries):
        try:
            with urllib.request.urlopen(q, timeout=30) as r:
                return json.loads(r.read())
        except Exception:
            if k == tries - 1:
                raise
            time.sleep(2 ** k)


def fetch_klines(symbol: str, interval: str = "1d", market: str = "spot", start_ms: int = 0) -> pd.DataFrame:
    """All closed klines from start_ms on, paginated."""
    rows, t = [], start_ms
    now = int(time.time() * 1000)
    while True:
        batch = _get(BASE[market], dict(symbol=symbol, interval=interval, startTime=t, limit=LIMIT[market]))
        if not batch:
            break
        rows += batch
        t = batch[-1][0] + 1
        if len(batch) < LIMIT[market] or t > now:
            break
        time.sleep(0.2)
    df = pd.DataFrame(rows, columns=COLS).drop(columns="ignore")
    df = df[df["close_time"] < now]  # drop the bar still open
    for c in COLS[1:6] + COLS[7:8] + COLS[9:11]:
        df[c] = df[c].astype(float)
    df["trades"] = df["trades"].astype("int64")
    df["date"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
    return df


def klines(symbol: str, interval: str = "1d", market: str = "spot", refresh: bool = True) -> pd.DataFrame:
    """Cached klines (index = bar open time, UTC). refresh=True fetches bars newer than the cache."""
    p = cache_path("binance_%s_%s_%s.parquet" % (market, symbol, interval))
    old = pd.read_parquet(p) if p.exists() else None
    if old is None or refresh:
        start = 0 if old is None else int(old["open_time"].max()) + 1
        new = fetch_klines(symbol, interval, market, start)
        df = new if old is None else pd.concat([old, new], ignore_index=True)
        df = df.drop_duplicates("open_time").sort_values("open_time", ignore_index=True)
        df.to_parquet(p, index=False)
    else:
        df = old
    return df.set_index("date")


def btc_daily(market: str = "spliced", refresh: bool = True) -> pd.DataFrame:
    """BTCUSDT daily open, high, low, close, volume (BTC), quote_volume (USDT); index = UTC day.

    market "spot" (2017-08-17 on), "usdm" (USDT-M perpetual, 2019-09-08 on; identical to the Amberdata perps
    file), or "spliced": perpetual prices from its first day, spot prices before (median gap 0.05 %), and
    volume from spot throughout (the perpetual's volume is ~10x larger, so splicing it would break volume ratios).
    """
    cols = ["open", "high", "low", "close", "volume", "quote_volume"]
    if market == "spliced":
        s = klines("BTCUSDT", "1d", "spot", refresh)[cols]
        u = klines("BTCUSDT", "1d", "usdm", refresh)[cols]
        out = s.copy()
        px = ["open", "high", "low", "close"]
        out.loc[u.index.intersection(s.index), px] = u.loc[u.index.intersection(s.index), px]
    else:
        out = klines("BTCUSDT", "1d", market, refresh)[cols].copy()
    out.index.name = "date"
    return out


FUNDING_URL = "https://fapi.binance.com/fapi/v1/fundingRate"


def funding_history(symbol: str = "BTCUSDT", refresh: bool = True) -> pd.Series:
    """USD-M perpetual funding rate per funding event (fraction per interval, usually 8 h), index = funding time
    (UTC). BTCUSDT starts 2019-09-10. Cached in cache/, extended incrementally."""
    p = cache_path("binance_funding_%s.parquet" % symbol)
    old = pd.read_parquet(p) if p.exists() else None
    if old is None or refresh:
        t = 1567296000000 if old is None else int(old["fundingTime"].max()) + 1  # 2019-09-01
        rows = []
        while True:
            batch = _get(FUNDING_URL, dict(symbol=symbol, startTime=t, limit=1000))
            if not batch:
                break
            rows += batch
            t = batch[-1]["fundingTime"] + 1
            if len(batch) < 1000:
                break
            time.sleep(0.3)
        new = pd.DataFrame(rows, columns=["fundingTime", "fundingRate"])
        new["fundingRate"] = new["fundingRate"].astype(float)
        df = new if old is None else pd.concat([old, new], ignore_index=True)
        df = df.drop_duplicates("fundingTime").sort_values("fundingTime", ignore_index=True)
        df.to_parquet(p, index=False)
    else:
        df = old
    s = pd.Series(df["fundingRate"].values, index=pd.to_datetime(df["fundingTime"], unit="ms", utc=True),
                  name="funding_rate")
    s.index.name = "time"
    return s
