"""Daily features for study 02 (rotation, funding cross-section, return dispersion), cached in
cache/rotation_dispersion_features.parquet. All trailing; all Binance (BTC price from the API, market panels from the
perps file, same crypto universe as study 01).
"""
import numpy as np
import pandas as pd

from cmarketlab.data import btc_daily, crypto_universe, daily_panel, load_daily
from cmarketlab.indicators import market as mk
from cmarketlab.indicators.cycle import leverage_cycle
from cmarketlab.paths import cache_path

# name: (family, direction for BOTTOMS, for TOPS, hypothesis). +1: higher -> extreme more likely; -1: lower;
# 0: no prior direction (reported as +1); None: not tested on that side.
FEATURES = {
    # 1. volume and leverage flows between BTC and alts
    "btc_vshare30":      ("rotation", +1, -1, "BTC share of market volume, 30 d: flight to BTC near bottoms, money "
                                              "leaving BTC for alts near tops"),
    "btc_vshare_chg90":  ("rotation", +1, -1, "90-day change of that share"),
    "alt_vshare30":      ("rotation", -1, +1, "volume share outside BTC and ETH, 30 d: alt speculation peaks at tops"),
    "alt_vshare_chg90":  ("rotation", -1, +1, "90-day change of that share"),
    "btc_oishare":       ("rotation", +1, -1, "BTC share of market open interest: leverage migrates to alts late"),
    "btc_oishare_chg90": ("rotation", +1, -1, "90-day change of that share"),
    "altrs90":           ("rotation", -1, +1, "median alt 90-day return minus BTC's (price rotation, from study 01)"),
    # 2. funding: level and cross-section
    "fund_med30":        ("funding", -1, +1, "median coin's 30-day funding, annualised (equal-weighted)"),
    "fund_wavg30":       ("funding", -1, +1, "OI-weighted 30-day funding, annualised (study 01's fund30)"),
    "fund_disp30":       ("funding", 0, +1, "cross-sectional spread (robust std) of 30-day funding: froth spreads "
                                            "unevenly at tops"),
    "fund_alt_btc30":    ("funding", -1, +1, "median alt funding minus BTC funding, 30 d: alt leverage premium"),
    # 3. cross-sectional return dispersion
    "rdisp1":            ("dispersion", 0, +1, "cross-sectional spread of daily returns, 30-day mean"),
    "rdisp30":           ("dispersion", 0, +1, "cross-sectional spread of 30-day returns (7-day mean)"),
    "rdisp_rel":         ("dispersion", -1, +1, "daily-return spread / BTC 30-day daily vol: idiosyncratic share; "
                                                "everything moves together at capitulation, coins diverge at tops"),
    "rdisp1_chg90":      ("dispersion", 0, +1, "90-day log change of rdisp1"),
}


def build(force: bool = False) -> pd.DataFrame:
    p = cache_path("rotation_dispersion_features.parquet")
    if p.exists() and not force:
        return pd.read_parquet(p)
    b = btc_daily("spliced")
    d = load_daily()
    d = d[d["hours"] == 24]
    u = crypto_universe(d)
    P = {k: daily_panel(d, k).reindex(columns=u.columns) for k in
         ("close", "quote_volume", "oi_value", "open_interest", "funding", "marketcap")}
    f = pd.DataFrame(index=u.index)
    f["btc_vshare30"] = mk.volume_share(P["quote_volume"], u, ["BTC"], 30)
    f["btc_vshare_chg90"] = f["btc_vshare30"].diff(90)
    f["alt_vshare30"] = mk.alt_volume_share(P["quote_volume"], u, ("BTC", "ETH"), 30)
    f["alt_vshare_chg90"] = f["alt_vshare30"].diff(90)
    f["btc_oishare"] = mk.oi_share(P["oi_value"], u, ["BTC"], 7)
    f["btc_oishare_chg90"] = f["btc_oishare"].diff(90)
    f["altrs90"] = mk.alt_relative_strength(P["close"], u, "BTC", 90)
    f["fund_med30"], f["fund_disp30"] = mk.funding_cross_section(P["funding"], u, 30)
    f["fund_wavg30"] = mk.weighted_funding(P["funding"], P["oi_value"], u, 30)
    btc_f = P["funding"]["BTC"].rolling(30, min_periods=15).mean() * 365.25
    f["fund_alt_btc30"] = f["fund_med30"] - btc_f
    f["rdisp1"] = mk.return_dispersion(P["close"], u, 1, 30)
    f["rdisp30"] = mk.return_dispersion(P["close"], u, 30, 7)
    btc_vol = np.log(P["close"]["BTC"]).diff().rolling(30, min_periods=15).std()
    f["rdisp_rel"] = f["rdisp1"] / btc_vol
    f["rdisp1_chg90"] = np.log(f["rdisp1"]).diff(90)
    # leverage reference (study 01) for the incremental tests
    lev = mk.leverage_ratio(P["oi_value"], P["marketcap"], u)
    out = b[["close", "high", "low"]].join(f, how="left")
    lc = leverage_cycle(out["close"], P["open_interest"]["BTC"], lev)
    out = out.join(lc[["ma200", "oi_chg90", "lev_chg90", "reading"]])
    out.to_parquet(p)
    return out


if __name__ == "__main__":
    f = build(force=True)
    pd.set_option("display.width", 220)
    print(f.describe().T.round(3).to_string())
    print(f.drop(columns="reading").notna().idxmax().to_string())
