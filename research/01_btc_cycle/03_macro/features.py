"""Daily macro / traditional-market features for study 03, as known on each day (publication lags applied),
cached in cache/macro_features.parquet. BTC price from the Binance API (2017-08 on); FRED series from their start.
"""
import numpy as np
import pandas as pd

from cmarketlab.data import btc_daily, known_daily
from cmarketlab.indicators import macro as mc
from cmarketlab.paths import cache_path

# name: (family, direction for BOTTOMS, for TOPS, hypothesis). +1: higher -> extreme more likely; -1: lower;
# 0: no prior (reported as +1).
FEATURES = {
    # inflation
    "cpi_yoy":      ("inflation", 0, 0, "headline CPI, year on year"),
    "core_yoy":     ("inflation", 0, 0, "core CPI, year on year"),
    "core_3m":      ("inflation", -1, +1, "core CPI, 3-month annualised: cooling inflation allows easing (bottoms), "
                                          "re-acceleration forces tightening (tops)"),
    "core_chg180":  ("inflation", -1, +1, "180-day change of core CPI YoY (disinflation / re-inflation)"),
    # policy and rates
    "ff":           ("rates", 0, 0, "effective fed funds rate"),
    "ff_chg180":    ("rates", -1, +1, "180-day change of fed funds: cutting cycles help bottoms, hiking ends tops"),
    "real_policy":  ("rates", 0, 0, "fed funds minus core CPI YoY (real policy rate)"),
    "y2_chg90":     ("rates", -1, +1, "90-day change of the 2-year yield: market pricing cuts / hikes"),
    "y2_chg180":    ("rates", -1, +1, "180-day change of the 2-year yield"),
    "y10":          ("rates", 0, 0, "10-year yield"),
    "real10":       ("rates", 0, 0, "10-year real (TIPS) yield"),
    "real10_chg180": ("rates", -1, +1, "180-day change of the real 10-year yield (cost of holding non-yielding "
                                       "assets)"),
    "curve":        ("rates", 0, 0, "10y minus 2y spread"),
    "curve_chg180": ("rates", 0, 0, "180-day change of the spread (steepening / flattening)"),
    # liquidity and dollar
    "usd_chg90":    ("liquidity", -1, +1, "90-day log change of the broad dollar: weak dollar = easy global "
                                          "liquidity"),
    "netliq_chg90": ("liquidity", +1, -1, "90-day log change of Fed net liquidity (assets - TGA - reverse repo)"),
    "m2_yoy":       ("liquidity", +1, -1, "M2 year on year"),
    # risk assets
    "vix30":        ("risk", +1, -1, "VIX, 30-day mean: fear peaks near bottoms, complacency near tops"),
    "spx_ma200":    ("risk", +1, -1, "S&P 500 vs its 200-day MA: equities holding up support a crypto bottom; "
                                     "equities rolling over end crypto rallies"),
    "spx_mom180":   ("risk", 0, 0, "S&P 500 180-day log return"),
}


def build(force: bool = False) -> pd.DataFrame:
    p = cache_path("macro_features.parquet")
    if p.exists() and not force:
        return pd.read_parquet(p)
    b = btc_daily("spliced")
    # start the macro frame early so 180/365-day windows are full from the first BTC day
    idx = pd.date_range(b.index[0] - pd.Timedelta(days=800), b.index[-1], freq="D", tz="UTC", name="date")
    k = known_daily(["CPIAUCSL", "CPILFESL", "M2SL", "DFF", "DGS2", "DGS10", "DFII10", "T10Y2Y", "DTWEXBGS",
                     "WALCL", "WTREGEN", "RRPONTSYD", "VIXCLS", "SP500"], idx)
    f = pd.DataFrame(index=idx)
    f["cpi_yoy"] = mc.growth(k["CPIAUCSL"], 365)
    f["core_yoy"] = mc.growth(k["CPILFESL"], 365)
    f["core_3m"] = mc.growth(k["CPILFESL"], 91, annualise=True)
    f["core_chg180"] = f["core_yoy"].diff(180)
    f["ff"] = k["DFF"]
    f["ff_chg180"] = k["DFF"].diff(180)
    f["real_policy"] = k["DFF"] - 100 * f["core_yoy"]
    f["y2_chg90"] = k["DGS2"].diff(90)
    f["y2_chg180"] = k["DGS2"].diff(180)
    f["y10"] = k["DGS10"]
    f["real10"] = k["DFII10"]
    f["real10_chg180"] = k["DFII10"].diff(180)
    f["curve"] = k["T10Y2Y"]
    f["curve_chg180"] = k["T10Y2Y"].diff(180)
    f["usd_chg90"] = mc.change_days(k["DTWEXBGS"], 90, log=True)
    f["netliq"] = mc.net_liquidity(k["WALCL"], k["WTREGEN"], k["RRPONTSYD"])
    f["netliq_chg90"] = mc.change_days(f["netliq"], 90, log=True)
    f["m2_yoy"] = mc.growth(k["M2SL"], 365)
    f["vix30"] = k["VIXCLS"].rolling(30, min_periods=20).mean()
    f["spx_ma200"] = mc.above_ma(k["SP500"], 200)
    f["spx_mom180"] = mc.change_days(k["SP500"], 180, log=True)
    out = b[["close", "high", "low"]].join(f, how="left")
    out["ma200"] = np.log(out["close"] / out["close"].rolling(200, min_periods=200).mean())
    out["mom180"] = np.log(out["close"] / out["close"].shift(180))
    out.to_parquet(p)
    return out


if __name__ == "__main__":
    f = build(force=True)
    pd.set_option("display.width", 220)
    print(f.describe().T.round(3).to_string())
    print(f.notna().idxmax().to_string())
