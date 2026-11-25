"""Part 05: does taker order flow (aggressive buying vs selling) drive the cross-section of returns?

    python research/02_crypto_factors/05_taker_flow/run.py fetch     Binance USD-M daily klines -> cache/ (~15 min once)
    python research/02_crypto_factors/05_taker_flow/run.py check     coverage and volume match vs the perps file
    python research/02_crypto_factors/05_taker_flow/run.py sorts     decile sorts, 3 versions -> reports/summary.csv, ...
    python research/02_crypto_factors/05_taker_flow/run.py fmb       Fama-MacBeth with part 03's compact controls
    python research/02_crypto_factors/05_taker_flow/run.py spanning  taker long-shorts vs market, ma50, liquidations
    python research/02_crypto_factors/05_taker_flow/run.py combo     ma50 + liquidations (+ taker) composite

The perps file has no taker volume, so it comes from Binance's public klines (fapi/v1/klines, field
taker_buy_quote_volume). Versions: top100 (equal weight), oiw (whole universe, OI-weighted) and top100_oiw (the
100 most liquid coins, OI-weighted), the version that worked best for ma50 and liquidations.
"""
import os
import sys

import numpy as np
import pandas as pd
import statsmodels.api as sm

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import COST_BPS, HOLD, N, SPLIT, market_for, panels, part_dir, signal  # noqa: E402

from cmarketlab.data import usdm_daily_panel  # noqa: E402
from cmarketlab.factors import (by_year, cs_rank, fama_macbeth, forward_returns, newey_west_t, perf,  # noqa: E402
                                quantile_portfolios, spread_summary)
from cmarketlab.indicators import xsection as xs  # noqa: E402

OUT = part_dir("05_taker_flow")
TO2024 = pd.Timestamp("2025-01-01", tz="UTC")


def all_versions():
    P, mkt, versions = panels()
    versions = dict(versions)
    versions["top100_oiw"] = (versions["top100"][0], versions["oiw"][1])
    return P, mkt, versions


def flow_panels(P, fetch=False):
    d = usdm_daily_panel(list(P.close.columns), fetch=fetch, log=lambda s: print(s, flush=True))
    out = {k: v.reindex(index=P.close.index, columns=P.close.columns) for k, v in d.items() if k != "missing"}
    return out, d["missing"]


def taker_catalogue(P, F, universe):
    tb, qv, tr = F["taker_buy_quote_volume"], F["quote_volume"], F["trades"]
    imb7 = xs.taker_imbalance(tb, qv, 7)
    return {
        "taker1":     (xs.taker_imbalance(tb, qv, 1), "taker imbalance, last day"),
        "taker7":     (imb7, "taker imbalance, 7 d"),
        "taker30":    (xs.taker_imbalance(tb, qv, 30), "taker imbalance, 30 d"),
        "taker_shift": (xs.taker_shift(tb, qv, 7, 60), "taker imbalance 7 d minus 60 d"),
        "flow_gap7":  (cs_rank(imb7, universe) - cs_rank(xs.momentum(P.close, 7), universe),
                       "rank of 7-d taker imbalance minus rank of 7-d return (buying not yet in the price)"),
        "tradesize30": (xs.trade_size(qv, tr, 30), "log average trade size, 30 d"),
    }


# ---------------------------------------------------------------------------------------------------- commands

def fetch():
    P, _, _ = panels()
    F, missing = flow_panels(P, fetch=True)
    print("fetched; missing:", len(missing), missing[:30])


def check():
    P, _, versions = all_versions()
    F, missing = flow_panels(P)
    u = P.universe
    have = F["quote_volume"].notna() & u
    ratio = (F["quote_volume"] / P.quote_volume).where(u)
    share = 2 * F["taker_buy_quote_volume"] / F["quote_volume"] - 1
    rows = dict(symbols_in_universe=int(u.any().sum()), symbols_missing=len(missing),
                universe_coin_days=int(u.values.sum()), with_klines=int(have.values.sum()),
                coverage=have.values.sum() / u.values.sum(),
                coverage_top100=(have & versions["top100"][0]).values.sum() / versions["top100"][0].values.sum(),
                volume_ratio_median=float(np.nanmedian(ratio.values)),
                volume_ratio_p05=float(np.nanpercentile(ratio.values, 5)),
                volume_ratio_p95=float(np.nanpercentile(ratio.values, 95)),
                daily_imbalance_median=float(np.nanmedian(share.where(u).values)),
                daily_imbalance_sd=float(np.nanstd(share.where(u).values)))
    S = pd.Series(rows)
    S.to_csv(os.path.join(OUT, "coverage.csv"), header=["value"])
    pd.Series(missing, name="symbol").to_csv(os.path.join(OUT, "missing_symbols.csv"), index=False)
    print(S.to_string())


def sorts():
    P, mkt, versions = all_versions()
    F, _ = flow_panels(P)
    bench = {v: market_for(v, P, versions) for v in versions}
    cat = taker_catalogue(P, F, P.universe)
    for f in ("ma50", "liq_imb7", "mom30"):                      # reference factors, same engine, all versions
        cat[f] = (signal(f, P, mkt), "reference (part 02)")
    cap = P.ret.clip(-0.5, 0.5)
    rows, dec, yrs, daily = [], {}, {}, {}
    for name, (s, desc) in cat.items():
        for v, (u, w) in versions.items():
            res = quantile_portfolios(s, P.ret, u, n=N, hold=HOLD, weight=w, cost_bps=COST_BPS)
            rc = quantile_portfolios(s, cap, u, n=N, hold=HOLD, weight=w, cost_bps=COST_BPS)
            x = res.net_ls.dropna()
            row = dict(factor=name, version=v, desc=desc, **spread_summary(res, bench[v]))
            for tag, part in (("h1", x[x.index < SPLIT]), ("h2", x[x.index >= SPLIT])):
                p = perf(part, 14)
                row["net_ann_" + tag], row["net_t_" + tag] = p.get("ann_mean"), p.get("t_nw")
            row["t_capped"] = perf(rc.net_ls.dropna(), 14)["t_nw"]
            row["t_to2024"] = perf(x[x.index < TO2024], 14)["t_nw"]
            row["sharpe"] = perf(x, 14)["sharpe"]
            rows.append(row)
            dec[(name, v)] = res.returns[list(range(1, N + 1))].mean() * 365
            yrs[(name, v)] = x.groupby(x.index.year).sum()
            daily[name + "|" + v] = res.net_ls
        print(name, " ".join("%s t=%.1f" % (r["version"], r["net_t"]) for r in rows[-3:]), flush=True)
    S = pd.DataFrame(rows)
    S.to_csv(os.path.join(OUT, "summary.csv"), index=False)
    D = pd.DataFrame(dec).T
    D.index.names = ["factor", "version"]
    D.to_csv(os.path.join(OUT, "deciles.csv"))
    Y = pd.DataFrame(yrs).T
    Y.index.names = ["factor", "version"]
    Y.to_csv(os.path.join(OUT, "by_year_sum.csv"))
    pd.DataFrame(daily).to_parquet(os.path.join(OUT, "ls_daily.parquet"))
    return S, D, Y


COMPACT = ["size_oi", "age", "beta90", "vol30", "ma50", "rsi14", "obv30", "turnover", "oi_chg7", "leverage",
           "fund7", "liq_long7", "liq_imb7"]
TAKER = ["taker7", "taker30", "taker_shift", "flow_gap7", "tradesize30"]


def fmb():
    """Each taker characteristic alone, then all taker measures with part 03's compact controls."""
    P, mkt, versions = all_versions()
    F, _ = flow_panels(P)
    cat = taker_catalogue(P, F, P.universe)
    fwd = forward_returns(P.ret, HOLD)
    chars = {f: signal(f, P, mkt) for f in COMPACT}
    chars.update({f: cat[f][0] for f in TAKER})
    split = pd.Timestamp("2024-01-01", tz="UTC")
    out = []
    for v, (u, w) in versions.items():
        for f in TAKER:
            _, s = fama_macbeth({f: chars[f]}, fwd, u, every=HOLD, weight=w, h=HOLD)
            out.append(s.assign(version=v, model="alone").rename_axis("factor").reset_index())
        S, s = fama_macbeth({f: chars[f] for f in COMPACT + TAKER}, fwd, u, every=HOLD, weight=w, h=HOLD)
        for tag, part in (("2022-23", S[S.index < split]), ("2024-26", S[S.index >= split])):
            s["t_" + tag] = [newey_west_t(part[c], 4) for c in S.columns]
        out.append(s.assign(version=v, model="compact+taker").rename_axis("factor").reset_index())
        print(v, "done", flush=True)
    M = pd.concat(out)
    M.to_csv(os.path.join(OUT, "fmb.csv"), index=False)
    return M


def spanning():
    """Alpha of each taker long-short vs the market, then vs market + ma50 + liquidation imbalance."""
    L = pd.read_parquet(os.path.join(OUT, "ls_daily.parquet"))
    P, _, versions = all_versions()
    rows = []
    for v in versions:
        bench = market_for(v, P, versions).rename("mkt")
        for f in TAKER + ["taker1"]:
            j = pd.concat([L[f + "|" + v].rename("y"), bench, L["ma50|" + v].rename("ma50"),
                           L["liq_imb7|" + v].rename("liq_imb7")], axis=1, sort=True).dropna()
            m1 = sm.OLS(j.y, sm.add_constant(j[["mkt"]])).fit(cov_type="HAC", cov_kwds={"maxlags": 14})
            m2 = sm.OLS(j.y, sm.add_constant(j[["mkt", "ma50", "liq_imb7"]])).fit(cov_type="HAC",
                                                                                cov_kwds={"maxlags": 14})
            rows.append(dict(factor=f, version=v, alpha_mkt=m1.params["const"] * 365, t_mkt=m1.tvalues["const"],
                             alpha_all=m2.params["const"] * 365, t_all=m2.tvalues["const"],
                             b_ma50=m2.params["ma50"], t_ma50=m2.tvalues["ma50"], b_liq=m2.params["liq_imb7"],
                             t_liq=m2.tvalues["liq_imb7"], r2=m2.rsquared,
                             corr_ma50=j.y.corr(j.ma50), corr_liq=j.y.corr(j.liq_imb7)))
    R = pd.DataFrame(rows)
    R.to_csv(os.path.join(OUT, "spanning.csv"), index=False)
    return R


def _inv_vol(legs: pd.DataFrame, lookback=180):
    v = legs.rolling(lookback, min_periods=30).std().shift(1)
    w = (1 / v).div((1 / v).sum(axis=1), axis=0)
    return (legs * w).sum(axis=1).where(w.notna().all(axis=1))


def combo(extra=("taker7",), version="top100_oiw"):
    """ma50 + liquidations (long squeezed shorts) composite, with and without a taker leg, 50/50 or 1/3 each and
    inverse-vol (180 d). Taker legs enter with the sign of their full-sample net mean."""
    L = pd.read_parquet(os.path.join(OUT, "ls_daily.parquet"))
    base = pd.DataFrame({"ma50": L["ma50|" + version], "liq": -L["liq_imb7|" + version]})
    rows, yrs = {}, {}
    sets = {"ma50 + liq": base}
    for f in extra:
        x = L[f + "|" + version]
        sets["ma50 + liq + " + f] = base.assign(**{f: np.sign(x.mean()) * x})
    start = max(_inv_vol(s).dropna().index[0] for s in sets.values())
    for name, legs in sets.items():
        for how, r in (("equal", legs.mean(axis=1, skipna=False)), ("inv-vol 180d", _inv_vol(legs))):
            r = r[r.index >= start].dropna()
            p = perf(r, 14)
            k = "%s | %s" % (name, how)
            rows[k] = dict(ann=p["ann_mean"], vol=p["ann_vol"], sharpe=p["sharpe"], t=p["t_nw"], max_dd=p["max_dd"],
                           t_to2024=perf(r[r.index < TO2024], 14)["t_nw"])
            yrs[k] = r.groupby(r.index.year).sum()
    C = pd.DataFrame(rows).T
    C.to_csv(os.path.join(OUT, "combo.csv"))
    Y = pd.DataFrame(yrs).T
    Y.to_csv(os.path.join(OUT, "combo_by_year.csv"))
    print("legs correlation (%s):\n" % version, sets[list(sets)[-1]].corr().round(2))
    return C, Y


if __name__ == "__main__":
    pd.set_option("display.width", 300)
    pd.set_option("display.max_columns", 40)
    cmd = sys.argv[1] if len(sys.argv) > 1 else "sorts"
    if cmd == "fetch":
        fetch()
    elif cmd == "check":
        check()
    elif cmd == "sorts":
        S, D, Y = sorts()
        cols = ["factor", "version", "net_ann", "net_t", "sharpe", "t_alpha", "net_t_h1", "net_t_h2", "t_capped",
                "t_to2024", "mono", "turnover_day"]
        print(S[cols].round(2).to_string())
        print((D * 100).round(0).to_string())
        print((Y * 100).round(0).to_string())
    elif cmd == "fmb":
        M = fmb()
        print(M.round(2).to_string())
    elif cmd == "spanning":
        print(spanning().round(2).to_string())
    elif cmd == "combo":
        extra = tuple(sys.argv[2].split(",")) if len(sys.argv) > 2 else ("taker7",)
        C, Y = combo(extra)
        print(C.round(2).to_string())
        print((Y * 100).round(0).to_string())
