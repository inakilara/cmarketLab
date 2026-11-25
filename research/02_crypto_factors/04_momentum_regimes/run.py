"""Part 04: when does cross-sectional momentum pay? Momentum long-short returns by market regime.

    python research/02_crypto_factors/04_momentum_regimes/run.py   -> reports/regimes.csv, by_year.csv,
                                                                       vol_scaled.csv, regimes.png

Uses the daily net D10 - D1 returns from part 02 (both versions). Each regime is read at the previous close
(known when the day's return starts):
    btc_trend    BTC above / below its 200-day MA
    btc_mom90    BTC 90-day return up / down
    mkt_mom30    equal-weighted universe 30-day return up / down
    rebound      bear (market 90-day return < 0) and market up over the last 7 days (Daniel-Moskowitz crash state)
    dispersion   cross-sectional spread of 30-day returns, terciles
    mkt_vol      equal-weighted market 30-day vol, terciles
    leverage     the leverage-cycle reading of project 01 (bottom zone / bear / bull / top zone ...)
Volatility scaling: LS scaled by target vol / trailing 30-day realised LS vol (Barroso & Santa-Clara 2015).
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import panels, part_dir  # noqa: E402

from cmarketlab.data import btc_daily  # noqa: E402
from cmarketlab.factors import by_year, perf  # noqa: E402
from cmarketlab.indicators.cycle import leverage_cycle, leverage_inputs  # noqa: E402

OUT = part_dir("04_momentum_regimes")
UNI = os.path.join(os.path.dirname(OUT), "..", "02_univariate", "reports")
FACTORS = ["mom14", "mom30", "mom60", "mom90", "resmom30", "resmom90", "hiprox180", "macross", "ma50"]


def regimes_frame():
    P, mkt, _ = panels()
    b = btc_daily("spliced")["close"].reindex(P.close.index)
    lm = np.log1p(mkt.fillna(0)).cumsum()
    r30 = np.log(P.close).diff(30).where(P.universe)
    disp = r30.quantile(0.75, axis=1) - r30.quantile(0.25, axis=1)
    mvol = mkt.rolling(30).std()
    li = leverage_inputs()
    lc = leverage_cycle(b, li["btc_oi"], li["lev"])
    g = pd.DataFrame(index=P.close.index)
    g["btc_trend"] = np.where(b > b.rolling(200).mean(), "BTC above 200d MA", "BTC below 200d MA")
    g["btc_mom90"] = np.where(np.log(b).diff(90) > 0, "BTC 90d up", "BTC 90d down")
    g["mkt_mom30"] = np.where(lm.diff(30) > 0, "market 30d up", "market 30d down")
    g["rebound"] = np.where((lm.diff(90) < 0) & (lm.diff(7) > 0), "bear + 7d rebound", "other")
    g["dispersion"] = pd.qcut(disp, 3, labels=["dispersion low", "mid", "high"]).astype(str)
    g["mkt_vol"] = pd.qcut(mvol, 3, labels=["market vol low", "mid", "high"]).astype(str)
    g["leverage"] = lc["reading"].reindex(g.index).fillna("n/a")
    return g.shift(1)                       # known at the previous close


def run(target_vol=0.5):
    L = pd.read_parquet(os.path.join(UNI, "ls_daily.parquet"))
    G = regimes_frame()
    rows, yrs, vs = [], {}, []
    for f in FACTORS:
        for v in ("top100", "oiw"):
            c = "%s|%s" % (f, v)
            if c not in L:
                continue
            x = L[c].dropna()
            yrs[(f, v)] = by_year(x)
            for reg in G.columns:
                for state, idx in G.loc[x.index, reg].groupby(G.loc[x.index, reg]).groups.items():
                    p = perf(x.loc[idx], 14)
                    rows.append(dict(factor=f, version=v, regime=reg, state=state, days=p["days"],
                                     ann=p["ann_mean"], t=p["t_nw"], sharpe=p["sharpe"]))
            # volatility-scaled momentum (scale known at the previous close)
            scale = (target_vol / (x.rolling(30, min_periods=20).std() * np.sqrt(365))).shift(1).clip(upper=3)
            xs_ = (x * scale).dropna()
            a, s = perf(x.loc[xs_.index], 14), perf(xs_, 14)
            vs.append(dict(factor=f, version=v, sharpe_raw=a["sharpe"], sharpe_scaled=s["sharpe"],
                           maxdd_raw=a["max_dd"], maxdd_scaled=s["max_dd"], t_raw=a["t_nw"], t_scaled=s["t_nw"]))
    R = pd.DataFrame(rows)
    R.to_csv(os.path.join(OUT, "regimes.csv"), index=False)
    Y = pd.DataFrame(yrs).T
    Y.to_csv(os.path.join(OUT, "by_year.csv"))
    V = pd.DataFrame(vs)
    V.to_csv(os.path.join(OUT, "vol_scaled.csv"), index=False)
    return R, Y, V


if __name__ == "__main__":
    pd.set_option("display.width", 300)
    R, Y, V = run()
    for f in ("mom30", "mom90", "resmom30"):
        print("\n==", f)
        print(R[R.factor == f].pivot_table(index=["regime", "state"], columns="version", values=["ann", "t", "days"],
                                           sort=False).round(2).to_string())
    print((100 * Y).round(0).to_string())
    print(V.round(2).to_string())
