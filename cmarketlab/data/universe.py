"""Which symbols count as the crypto market, day by day (trailing information only)."""
from __future__ import annotations

import pandas as pd

from .daily import daily_panel

# index / pegged / non-crypto perps that the weekend rule cannot catch
EXCLUDE = {"BTCDOM", "DEFI", "FOOTBALL", "BLUEBIRD", "PAXG", "XAUT", "XAU", "USDBRL"}
TRADFI_FROM = pd.Timestamp("2025-12-01", tz="UTC")  # Binance's equity / commodity perps all list after this


def non_crypto(d: pd.DataFrame, weekend_ratio: float = 0.45) -> set[str]:
    """Equity, ETF, commodity and FX perps, plus EXCLUDE.

    Rule: listed on or after 2025-12-01 and median weekend daily volume below `weekend_ratio` of the weekday
    median (crypto ~0.75, exchange-traded underlyings 0.06-0.40 because their reference markets close).
    """
    wk = d["date"].dt.day_of_week >= 5
    we = d[wk].groupby("symbol")["quote_volume"].median()
    wd = d[~wk].groupby("symbol")["quote_volume"].median()
    start = d.groupby("symbol")["date"].min()
    ratio = (we / wd).reindex(start.index)
    late = start[start >= TRADFI_FROM].index
    tradfi = {s for s in late if not (ratio.get(s, 0.0) >= weekend_ratio)}
    return tradfi | (EXCLUDE & set(start.index))


def crypto_universe(d: pd.DataFrame, min_age_days: int = 60, min_quote_volume: float = 1e6,
                    window: int = 30, top_n: int | None = None) -> pd.DataFrame:
    """Wide boolean daily frame: symbol in the crypto universe on that day.

    In = crypto (not `non_crypto`), listed for >= min_age_days, trailing `window`-day median daily USDT volume
    >= min_quote_volume, and has a close that day. top_n keeps only the n most liquid of those each day (by the
    same trailing median volume), for measures that should not depend on how many small coins are listed.
    Uses only data up to that day.
    """
    close = daily_panel(d, "close")
    qv = daily_panel(d, "quote_volume")
    drop = non_crypto(d)
    keep = [c for c in close.columns if c not in drop]
    close, qv = close[keep], qv[keep]
    age = close.notna().cumsum()
    med = qv.rolling(window, min_periods=window // 2).median()
    u = close.notna() & (age >= min_age_days) & (med >= min_quote_volume)
    if top_n is not None:
        rank = med.where(u).rank(axis=1, ascending=False, method="first")
        u = u & (rank <= top_n)
    return u
