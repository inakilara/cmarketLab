"""Wide daily panels for factor sorts, from the perps file's daily cache.

Return convention (long position, day t): r_t = close_t / close_{t-1} - 1 - funding_t, where funding_t is the sum
of the day's funding prints (positive = longs pay). The day's 00:00 print strictly belongs to the position held the
day before; that shift is one print in three and is ignored.
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from ..data import crypto_universe, daily_panel, load_daily


@dataclass
class FactorPanels:
    close: pd.DataFrame          # daily close
    price_ret: pd.DataFrame      # close-to-close simple return
    funding: pd.DataFrame        # daily funding (fraction; longs pay when positive)
    ret: pd.DataFrame            # total long return = price_ret - funding
    quote_volume: pd.DataFrame
    oi_value: pd.DataFrame       # open interest in USDT
    marketcap: pd.DataFrame
    universe: pd.DataFrame       # bool: in the investable universe at day t's close
    open: pd.DataFrame = None
    high: pd.DataFrame = None
    low: pd.DataFrame = None
    open_interest: pd.DataFrame = None   # in coins (base units)
    long_liq: pd.DataFrame = None        # USD liquidated longs
    short_liq: pd.DataFrame = None

    def market(self, weight: pd.DataFrame | None = None) -> pd.Series:
        """Daily return of the universe portfolio formed at the previous close (equal- or `weight`-weighted)."""
        u = self.universe.shift(1, fill_value=False)
        w = u.astype(float) if weight is None else weight.shift(1).where(u).fillna(0.0)
        r = self.ret.fillna(0.0)
        return (w * r).sum(axis=1) / w.sum(axis=1)

    def restrict(self, universe: pd.DataFrame) -> "FactorPanels":
        """Same panels with a narrower universe (AND of both)."""
        u = self.universe & universe.reindex_like(self.universe).fillna(False).astype(bool)
        return FactorPanels(**{**vars(self), "universe": u})


def factor_panels(min_age_days: int = 60, min_quote_volume: float = 1e6, top_n: int | None = None,
                  start: str | None = None) -> FactorPanels:
    """Panels on the crypto universe of `cmarketlab.data.crypto_universe` (listing-day and outage stubs dropped)."""
    d = load_daily()
    d = d[d["hours"] >= 20]
    u = crypto_universe(d, min_age_days=min_age_days, min_quote_volume=min_quote_volume, top_n=top_n)
    cols = u.columns[u.any()]           # symbols that are ever in the universe
    u = u[cols]
    P = {k: daily_panel(d, k).reindex(index=u.index, columns=cols) for k in
         ("close", "funding", "quote_volume", "oi_value", "marketcap", "open", "high", "low", "open_interest",
          "long_liq", "short_liq")}
    pr = P["close"].pct_change(fill_method=None)
    ret = pr - P["funding"].fillna(0.0)
    fp = FactorPanels(close=P["close"], price_ret=pr, funding=P["funding"], ret=ret,
                      quote_volume=P["quote_volume"], oi_value=P["oi_value"], marketcap=P["marketcap"],
                      universe=u.astype(bool), open=P["open"], high=P["high"], low=P["low"],
                      open_interest=P["open_interest"], long_liq=P["long_liq"], short_liq=P["short_liq"])
    if start is not None:
        t0 = pd.Timestamp(start, tz="UTC")
        fp = FactorPanels(**{k: v.loc[v.index >= t0] for k, v in vars(fp).items()})
    return fp
