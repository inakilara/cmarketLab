"""Daily features for study 04 (ideas from the 'Bitcoin cycles: macro & microstructure drivers' note that studies
01-03 had not tested), cached in cache/flow_basis_dominance_features.parquet. All Binance / FRED, all trailing.

Sources and first usable day:
    BTCUSDT spot klines (taker buy volume)       2017-08
    BTCUSDT perpetual klines, funding history    2019-09
    perps file market caps (dominance), BTC OI   2021-09
    FRED S&P 500                                 (1-day publication lag)
"""
import numpy as np
import pandas as pd

from cmarketlab.data import btc_daily, crypto_universe, daily_panel, fred, funding_history, klines, load_daily
from cmarketlab.indicators import flow
from cmarketlab.indicators.cycle import chg90, leverage_cycle, leverage_inputs
from cmarketlab.paths import cache_path

# name: (family, direction for BOTTOMS, for TOPS, hypothesis). +1: higher -> extreme more likely; -1: lower;
# 0: no prior (reported as +1); None: not tested on that side.
FEATURES = {
    # order flow (taker buy vs sell volume)
    "spot_imb30":   ("flow_spot", 0, +1, "spot taker imbalance, 30 d: aggressive buying near tops"),
    "spot_imb90":   ("flow_spot", 0, +1, "spot taker imbalance, 90 d"),
    "perp_imb30":   ("flow_perp", 0, +1, "perpetual taker imbalance, 30 d"),
    "spot_lead30":  ("flow_perp", +1, -1, "spot minus perp imbalance, 30 d: spot-led buying (accumulation) vs "
                                          "perp-led froth"),
    # basis and funding (Binance funding history, longer than the perps file)
    "basis30":      ("basis", -1, +1, "perpetual / spot log gap, 30-day mean"),
    "fund_btc30":   ("basis", -1, +1, "BTC perpetual funding, 30-day mean, annualised"),
    "fund_hot30":   ("basis", None, +1, "share of 8-h funding prints > 0.05 % in 30 d (overcrowded longs)"),
    "fund_neg30":   ("basis", +1, None, "share of funding prints < 0 in 30 d (peak fear / short crowding)"),
    # dominance (market cap, perps-file universe)
    "btc_dom":      ("dominance", +1, -1, "BTC share of crypto market cap: rising near bottoms, falling at froth"),
    "btc_dom_chg90": ("dominance", +1, -1, "90-day change of BTC dominance"),
    # price x open interest
    "px_up_oi_down": ("price_oi", None, +1, "90-d price up while BTC OI falls: fragile (short-squeeze) rally"),
    "px_up_oi_up":  ("price_oi", None, -1, "90-d price up with OI up: trend confirmed by new money (no top)"),
    "oi_minus_px":  ("price_oi", -1, +1, "OI 90-d change minus price 90-d change (leverage outrunning price)"),
    # cross-asset regime
    "corr_spx90":   ("cross_asset", 0, 0, "BTC vs S&P 500 90-day return correlation"),
}

HALVINGS = pd.to_datetime(["2012-11-28", "2016-07-09", "2020-05-11", "2024-04-20"], utc=True)


def days_since_halving(idx: pd.DatetimeIndex) -> pd.Series:
    pos = HALVINGS.searchsorted(idx, side="right") - 1
    return pd.Series((idx - HALVINGS[pos]).days, index=idx)


def build(force: bool = False) -> pd.DataFrame:
    p = cache_path("flow_basis_dominance_features.parquet")
    if p.exists() and not force:
        return pd.read_parquet(p)
    b = btc_daily("spliced")
    s, u = klines("BTCUSDT", "1d", "spot"), klines("BTCUSDT", "1d", "usdm")
    f = pd.DataFrame(index=b.index)
    f["spot_imb30"] = flow.taker_imbalance(s["taker_buy_quote_volume"], s["quote_volume"], 30)
    f["spot_imb90"] = flow.taker_imbalance(s["taker_buy_quote_volume"], s["quote_volume"], 90)
    f["perp_imb30"] = flow.taker_imbalance(u["taker_buy_quote_volume"], u["quote_volume"], 30)
    f["spot_lead30"] = f["spot_imb30"] - f["perp_imb30"]
    f["basis30"] = flow.basis(u["close"], s["close"], 30)
    ev = funding_history("BTCUSDT")
    f["fund_btc30"] = flow.daily_funding(ev).rolling(30, min_periods=15).mean() * 365.25
    f["fund_hot30"] = flow.share_of_events(ev, above=0.0005, window=30)
    f["fund_neg30"] = flow.share_of_events(ev, below=0.0, window=30)
    # dominance and OI from the perps file
    d = load_daily()
    d = d[d["hours"] == 24]
    uni = crypto_universe(d)
    mc = daily_panel(d, "marketcap").reindex(columns=uni.columns)
    f["btc_dom"] = flow.dominance(mc, uni, ["BTC"])
    f["btc_dom_chg90"] = f["btc_dom"].diff(90)
    li = leverage_inputs()
    oi90 = chg90(li["btc_oi"]).reindex(f.index)
    px90 = np.log(b["close"]).diff(90)
    ok = oi90.notna()
    f["px_up_oi_down"] = ((px90 > 0) & (oi90 < 0)).astype(float).where(ok)
    f["px_up_oi_up"] = ((px90 > 0) & (oi90 > 0)).astype(float).where(ok)
    f["oi_minus_px"] = oi90 - px90
    # S&P 500 (FRED, as known the next day)

    raw = fred("SP500")
    raw.index = raw.index + pd.Timedelta(days=1)          # known the day after
    f["corr_spx90"] = flow.rolling_corr(b["close"], raw.reindex(b.index), 90)
    f["halving_days"] = days_since_halving(f.index)
    out = b[["close", "high", "low"]].join(f)
    lc = leverage_cycle(out["close"], li["btc_oi"], li["lev"])
    out = out.join(lc[["ma200", "oi_chg90", "lev_chg90", "reading"]])
    out["mom180"] = np.log(out["close"]).diff(180)
    out.to_parquet(p)
    return out


if __name__ == "__main__":
    f = build(force=True)
    pd.set_option("display.width", 220)
    print(f.describe().T.round(4).to_string())
    print(f.drop(columns="reading").notna().idxmax().to_string())
