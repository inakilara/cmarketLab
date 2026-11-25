"""Binance USD-M perpetuals, hourly (shared-data/binance-perps-1h), read in place.

Long format: one row per (symbol, date). See the dataset README for units:
volume and open_interest in base units, liquidations in USD, funding_rate only on funding hours.
"""
from __future__ import annotations

from collections.abc import Iterable

import pandas as pd
import pyarrow.parquet as pq

from ..paths import PERPS_1H

FIELDS = ["open", "high", "low", "close", "volume", "open_interest", "funding_rate", "est_funding_rate",
          "long_liquidations", "short_liquidations", "marketcap"]


def _ts(x) -> pd.Timestamp | None:
    if x is None:
        return None
    t = pd.Timestamp(x)
    return t.tz_localize("UTC") if t.tzinfo is None else t.tz_convert("UTC")


def symbols(path=PERPS_1H) -> list[str]:
    """All symbols in the file (base asset names: 'BTC', 'XRP', '1000PEPE', ...)."""
    return sorted(pq.read_table(path, columns=["symbol"]).column("symbol").unique().to_pylist())


def load_perps(syms: str | Iterable[str] | None = None, fields: Iterable[str] | None = None, start=None, end=None,
               path=PERPS_1H) -> pd.DataFrame:
    """Long table [symbol, date, *fields], filtered at read time (the full file is ~1.4 GB in memory).

    start is inclusive, end exclusive; naive timestamps are taken as UTC.
    """
    filters = []
    if syms is not None:
        filters.append(("symbol", "in", [syms] if isinstance(syms, str) else list(syms)))
    if start is not None:
        filters.append(("date", ">=", _ts(start)))
    if end is not None:
        filters.append(("date", "<", _ts(end)))
    cols = ["symbol", "date"] + (list(fields) if fields is not None else FIELDS)
    df = pd.read_parquet(path, columns=cols, filters=filters or None)
    df["symbol"] = df["symbol"].astype(str)
    return df.sort_values(["symbol", "date"], ignore_index=True)


def panel(df: pd.DataFrame, field: str) -> pd.DataFrame:
    """Wide frame of one field: index = date (every hour in range), columns = symbols."""
    w = df.pivot(index="date", columns="symbol", values=field)
    full = pd.date_range(w.index.min(), w.index.max(), freq="h", name="date")
    return w.reindex(full)


def funding_per_hour(df: pd.DataFrame) -> pd.DataFrame:
    """Funding paid by longs in each hour (decimal of notional), wide; 0 between events, NaN before listing.

    Works whatever the pair's funding interval (8, 4, 2 or 1 h) because it uses the actual events.
    """
    w = panel(df, "funding_rate")
    listed = panel(df, "close").notna()
    return w.fillna(0.0).where(listed)


def universe(df: pd.DataFrame, min_quote_volume: float = 0.0, min_history_hours: int = 0,
             window: str = "30D") -> pd.DataFrame:
    """Boolean wide frame: symbol eligible at each hour (trailing info only).

    Eligible = listed for at least `min_history_hours` and trailing `window` mean hourly USDT volume
    (volume x close) >= min_quote_volume.
    """
    close = panel(df, "close")
    qv = panel(df, "volume") * close
    age = close.notna().cumsum()
    liq = qv.rolling(window, min_periods=1).mean().fillna(0.0) >= min_quote_volume
    return close.notna() & (age >= min_history_hours) & liq
