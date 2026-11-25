"""Daily feature table for the BTC cycle-extremes study (all trailing), cached in cache/btc_cycle_features.parquet.

All Binance. BTC price (features and targets): Binance BTCUSDT daily from the public API, USDT-M perpetual from
2019-09-08 and spot before it, back to 2017-08-17 (cmarketlab.data.btc_daily, "spliced"); BTC volume from spot.
Market features: all crypto perps in the Binance perps file (Amberdata, 2021-09 onward; TradFi and index perps
excluded, >= 60 days listed, >= $1M median daily volume).
"""
import numpy as np
import pandas as pd

from cmarketlab.data import btc_daily, crypto_universe, daily_panel, load_daily
from cmarketlab.indicators import market as mk
from cmarketlab.indicators import trend as tr
from cmarketlab.paths import cache_path

# name: (family, hypothesis direction for BOTTOMS, for TOPS, description). +1 = higher value -> extreme more
# likely, -1 = lower value -> more likely, 0 = no prior direction (tested both ways), None = not tested.
FEATURES = {
    "dd365":       ("price", -1, None, "drawdown from the 365-day high"),
    "rally365":    ("price", None, +1, "rise from the 365-day low"),
    "dsh365":      ("price", +1, None, "days since the 365-day high (bear duration)"),
    "dsl365":      ("price", None, +1, "days since the 365-day low (bull duration)"),
    "dsl90":       ("price", +1, None, "days since the 90-day low (no new lows: base building)"),
    "dsh90":       ("price", None, +1, "days since the 90-day high (no new highs: stalling)"),
    "ma200":       ("price", -1, +1, "log(close / 200-day MA)"),
    "ma365":       ("price", -1, +1, "log(close / 365-day MA)"),
    "mom180":      ("price", -1, +1, "180-day log return"),
    "decel":       ("price", +1, -1, "30-day return minus the 180-day return's 30-day pace (trend deceleration)"),
    "volr":        ("price", 0, 0, "30-day / 365-day realised vol"),
    "vspike60":    ("price", +1, None, "max 7-day / 365-day volume ratio in the last 60 days (capitulation volume)"),
    "fund30":      ("market", -1, +1, "OI-weighted market funding, 30 days, annualised"),
    "negfund":     ("market", +1, -1, "share of perps with negative 30-day funding"),
    "lev":         ("market", -1, +1, "aggregate OI / market cap"),
    "lev_chg90":   ("market", -1, +1, "90-day log change of aggregate OI / market cap"),
    "btc_oi_chg90": ("market", -1, +1, "90-day log change of BTC open interest in BTC"),
    "liq_long60":  ("market", +1, None, "max 7-day long liquidations / OI in the last 60 days (capitulation)"),
    "liq_short60": ("market", None, +1, "max 7-day short liquidations / OI in the last 60 days (squeeze)"),
    "breadth":     ("market", -1, +1, "share of perps above their 100-day MA"),
    "breadth_chg60": ("market", +1, -1, "60-day change of that share (improving / deteriorating breadth)"),
    "new_lows":    ("market", 0, None, "share of perps at a 90-day low (7-day mean)"),
    "new_highs":   ("market", None, +1, "share of perps at a 90-day high (7-day mean)"),
    "altrs90":     ("market", -1, +1, "median alt 90-day return minus BTC's"),
    "gainers":     ("market", None, +1, "share of perps up > 100 % in 90 days"),
    "corr60":      ("market", +1, -1, "median 60-day correlation of alts with BTC"),
    "mvol":        ("market", -1, +1, "market volume, 30-day / 365-day mean"),
    "altvol":      ("market", -1, +1, "share of volume outside BTC and ETH, 30 days"),
    "listings90":  ("market", -1, +1, "new perp listings in the last 90 days"),
}


def price_features(b: pd.DataFrame) -> pd.DataFrame:
    c, v = b["close"], b["volume"]
    f = pd.DataFrame(index=b.index)
    f["dd365"] = tr.drawdown(c, 365)
    f["rally365"] = tr.rally(c, 365)
    f["dsh365"] = tr.days_since_high(c, 365)
    f["dsl365"] = tr.days_since_low(c, 365)
    f["dsl90"] = tr.days_since_low(c, 90)
    f["dsh90"] = tr.days_since_high(c, 90)
    f["ma200"] = tr.ma_ratio(c, 200)
    f["ma365"] = tr.ma_ratio(c, 365)
    f["mom180"] = tr.momentum(c, 180)
    f["decel"] = tr.momentum(c, 30) - f["mom180"] / 6
    f["volr"] = tr.vol_ratio(c, 30, 365)
    vr = v.rolling(7).mean() / v.rolling(365, min_periods=180).mean()
    f["vspike60"] = vr.rolling(60, min_periods=30).max()
    # the first 365 days lack a full lookback for the 365-day measures
    f.loc[f.index < b.index[0] + pd.Timedelta(days=365), ["dd365", "rally365", "dsh365", "dsl365"]] = np.nan
    return f


def market_features(d: pd.DataFrame) -> pd.DataFrame:
    d = d[d["hours"] == 24]  # drop the partial last day
    u = crypto_universe(d)
    P = {k: daily_panel(d, k).reindex(columns=u.columns) for k in
         ("close", "quote_volume", "oi_value", "open_interest", "funding", "long_liq", "short_liq", "marketcap")}
    f = pd.DataFrame(index=u.index)
    f["fund30"] = mk.weighted_funding(P["funding"], P["oi_value"], u, 30)
    f["negfund"] = mk.share_negative_funding(P["funding"], u, 30)
    f["lev"] = mk.leverage_ratio(P["oi_value"], P["marketcap"], u)
    f["lev_chg90"] = np.log(f["lev"].rolling(7).mean()).diff(90)
    f["btc_oi_chg90"] = np.log(P["open_interest"]["BTC"].rolling(7).mean()).diff(90)
    lo, sh = mk.liquidation_intensity(P["long_liq"], P["short_liq"], P["oi_value"], u, 7)
    f["liq_long60"] = lo.rolling(60, min_periods=30).max()
    f["liq_short60"] = sh.rolling(60, min_periods=30).max()
    f["breadth"] = mk.breadth_above_ma(P["close"], u, 100)
    f["breadth_chg60"] = f["breadth"].diff(60)
    f["new_highs"], f["new_lows"] = mk.breadth_extremes(P["close"], u, 90)
    f["altrs90"] = mk.alt_relative_strength(P["close"], u, "BTC", 90)
    f["gainers"] = mk.share_big_gainers(P["close"], u, 90, 1.0)
    f["corr60"] = mk.corr_to_base(P["close"], u, "BTC", 60)
    f["mvol"] = mk.volume_ratio(P["quote_volume"], u, 30, 365)
    f["altvol"] = mk.alt_volume_share(P["quote_volume"], u, ("BTC", "ETH"), 30)
    f["listings90"] = mk.listings(daily_panel(d, "close").reindex(columns=u.columns), 90)
    f["n_universe"] = u.sum(axis=1)
    f["btc_oi"] = P["open_interest"]["BTC"]
    return f


def build(force: bool = False) -> pd.DataFrame:
    p = cache_path("btc_cycle_features.parquet")
    if p.exists() and not force:
        return pd.read_parquet(p)
    b = btc_daily("spliced")
    f = price_features(b).join(market_features(load_daily()), how="left")
    f = b[["close", "high", "low"]].join(f)
    f.to_parquet(p)
    return f


if __name__ == "__main__":
    f = build(force=True)
    pd.set_option("display.width", 220)
    print(f.describe().T.round(3).to_string())
    print(f.notna().idxmax().to_string())
