"""US macro and traditional-market series from FRED (public CSV download, no API key), cached in cache/.

    fred("CPIAUCSL")            raw series, indexed by observation date
    known_daily(ids, index)     each series as it was *known* on each day: shifted by its publication lag, then
                                forward-filled (no look-ahead from release delays)

FRED returns the latest revised values, not the vintage known at the time; revisions are small for CPI, yields,
spreads and the Fed balance sheet, larger for M2.
"""
from __future__ import annotations

import io
import time
import urllib.request

import pandas as pd

from ..paths import cache_path

URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=%s"

# id: (description, units, publication lag in days after the observation date)
SERIES = {
    "CPIAUCSL": ("CPI, all items, SA", "index", 45),           # month M released ~10-15th of M+1
    "CPILFESL": ("core CPI (ex food and energy), SA", "index", 45),
    "M2SL":     ("M2 money stock, SA", "USD bn", 55),           # released ~4 weeks after month end
    "DFF":      ("effective federal funds rate", "%", 1),
    "DGS2":     ("2-year Treasury yield", "%", 1),
    "DGS10":    ("10-year Treasury yield", "%", 1),
    "DFII10":   ("10-year TIPS real yield", "%", 1),
    "T10Y2Y":   ("10y minus 2y Treasury spread", "pp", 1),
    "DTWEXBGS": ("broad trade-weighted US dollar index", "index", 7),   # H.10, weekly release
    "WALCL":    ("Fed total assets (Wednesday level)", "USD mn", 2),
    "WTREGEN":  ("Treasury General Account (Wednesday level)", "USD mn", 2),
    "RRPONTSYD": ("overnight reverse repo, Fed", "USD bn", 1),
    "BAMLH0A0HYM2": ("US high-yield option-adjusted spread", "pp", 1),
    "VIXCLS":   ("VIX", "index", 1),
    "SP500":    ("S&P 500", "index", 1),
}


def fetch_fred(series_id: str, tries: int = 4) -> pd.Series:
    for k in range(tries):
        try:
            with urllib.request.urlopen(URL % series_id, timeout=60) as r:
                raw = r.read().decode()
            break
        except Exception:
            if k == tries - 1:
                raise
            time.sleep(2 ** k)
    df = pd.read_csv(io.StringIO(raw))
    s = pd.to_numeric(df.iloc[:, 1], errors="coerce")  # "." marks missing values
    s.index = pd.to_datetime(df.iloc[:, 0], utc=True)
    s.index.name = "date"
    return s.dropna().rename(series_id)


def fred(series_id: str, refresh: bool = False, max_age_days: float = 1.0) -> pd.Series:
    """Cached FRED series (refetched when the cache is older than max_age_days or refresh=True)."""
    p = cache_path("fred_%s.parquet" % series_id)
    if p.exists() and not refresh and (time.time() - p.stat().st_mtime) < max_age_days * 86400:
        return pd.read_parquet(p)[series_id]
    s = fetch_fred(series_id)
    s.to_frame().to_parquet(p)
    return s


def known_daily(ids, index: pd.DatetimeIndex, lags: dict | None = None, refresh: bool = False) -> pd.DataFrame:
    """Daily frame on `index`: each series' latest value already published on that day."""
    out = {}
    for i in ids:
        lag = (lags or {}).get(i, SERIES.get(i, (None, None, 1))[2])
        s = fred(i, refresh)
        s.index = s.index + pd.Timedelta(days=lag)
        s = s[~s.index.duplicated(keep="last")]
        out[i] = s.reindex(s.index.union(index)).ffill().reindex(index)
    return pd.DataFrame(out, index=index)
