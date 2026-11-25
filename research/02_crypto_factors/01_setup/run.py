"""Project 02: decile long-short (factor-mimicking) portfolios on the Binance perps universe.

    python research/02_crypto_factors/01_setup/run.py baseline  -> reports/summary.csv, deciles.csv, by_year.csv, ls_daily.csv,
                                                          cumulative.png, deciles.png
    python research/02_crypto_factors/01_setup/run.py robust    -> reports/robustness.csv (holding period, weights, universe,
                                                          halves, capped returns, price-only, quintiles)
    python research/02_crypto_factors/01_setup/run.py corr      -> reports/ls_correlation.csv

Baseline: crypto universe (age >= 60 d, 30-d median volume >= $1M), deciles, equal weight, daily cohorts held 7 days
(overlapping), total returns (price minus funding paid by longs), costs 4 bp per side.
"""
import os
import sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from factors import FACTORS, oi_weight  # noqa: E402

from cmarketlab.factors import by_year, factor_panels, quantile_portfolios, spread_summary  # noqa: E402
from cmarketlab.viz.factors import plot_cumulative, plot_quantile_means  # noqa: E402

OUT = os.path.join(HERE, "reports")
BASE = dict(n=10, hold=7, cost_bps=4.0)
SPLIT = pd.Timestamp("2024-01-01", tz="UTC")


def _signals(P):
    return {k: fn(P) for k, (fam, fn, _d) in FACTORS.items()}


def baseline():
    P = factor_panels()
    mkt = P.market()
    sig = _signals(P)
    rows, dec, yrs, daily = [], {}, {}, {}
    for name, s in sig.items():
        res = quantile_portfolios(s, P.ret, P.universe, **BASE)
        rows.append(dict(factor=name, family=FACTORS[name][0], **spread_summary(res, mkt)))
        dec[name] = res.returns[list(range(1, 11))].mean() * 365
        yrs[name] = by_year(res.ls)
        daily[name] = res.ls
        daily[name + "_net"] = res.net_ls
    S = pd.DataFrame(rows)
    S.to_csv(os.path.join(OUT, "summary.csv"), index=False)
    D = pd.DataFrame(dec).T
    D.to_csv(os.path.join(OUT, "deciles.csv"))
    Y = pd.DataFrame(yrs).T
    Y.to_csv(os.path.join(OUT, "by_year.csv"))
    L = pd.DataFrame(daily)
    L["market_ew"] = mkt.reindex(L.index)
    L.to_csv(os.path.join(OUT, "ls_daily.csv"))
    groups = {}
    for name, (fam, _f, _d) in FACTORS.items():
        groups.setdefault(fam, {})[name] = L[name + "_net"]
    plot_cumulative({"%s (D10 - D1, net of 4 bp)" % k: v for k, v in groups.items()},
                    os.path.join(OUT, "cumulative.png"),
                    "Decile long-short spreads, Binance perps, equal weight, 7-day overlapping holds")
    plot_quantile_means({k: D.loc[k] for k in D.index}, os.path.join(OUT, "deciles.png"),
                        "Mean return by decile (gross, annualised, total return incl. funding)")
    return S, D, Y


def _row(tag, name, res, mkt):
    s = spread_summary(res, mkt)
    return dict(factor=name, variant=tag, ls_ann=s["ls_ann"], ls_t=s["ls_t"], net_ann=s["net_ann"],
                net_t=s["net_t"], alpha=s["alpha"], t_alpha=s["t_alpha"], beta=s["beta"], mono=s["mono"],
                turnover_day=s["turnover_day"], names_per_q=s["names_per_q"], start=s["start"])


def robust():
    P = factor_panels()
    mkt = P.market()
    top = factor_panels(top_n=100).universe
    P100 = P.restrict(top)
    w = oi_weight(P)
    rows = []
    for name, (fam, fn, _d) in FACTORS.items():
        s = fn(P)
        base = quantile_portfolios(s, P.ret, P.universe, **BASE)
        rows.append(_row("baseline", name, base, mkt))
        for tag, ls in (("2022-23", base.ls[base.ls.index < SPLIT]), ("2024-26", base.ls[base.ls.index >= SPLIT])):
            sub = type(base)(returns=base.returns.loc[ls.index], turnover=base.turnover.loc[ls.index],
                             names=base.names, net_ls=base.net_ls.loc[ls.index], n=10, hold=7, cost_bps=4,
                             legs=base.legs)
            rows.append(_row(tag, name, sub, mkt))
        variants = {
            "hold 1": dict(BASE, hold=1),
            "hold 30": dict(BASE, hold=30),
            "quintiles": dict(BASE, n=5),
            "OI-weighted": dict(BASE, weight=w),
        }
        for tag, kw in variants.items():
            rows.append(_row(tag, name, quantile_portfolios(s, P.ret, P.universe, **kw), mkt))
        rows.append(_row("top 100 liquid", name, quantile_portfolios(s, P.ret, P100.universe, **BASE), P100.market()))
        rows.append(_row("returns capped +-50 %", name,
                         quantile_portfolios(s, P.ret.clip(-0.5, 0.5), P.universe, **BASE), mkt))
        rows.append(_row("price only (no funding)", name, quantile_portfolios(s, P.price_ret, P.universe, **BASE),
                         mkt))
        print(name, "done", flush=True)
    R = pd.DataFrame(rows)
    R.to_csv(os.path.join(OUT, "robustness.csv"), index=False)
    return R


def corr():
    L = pd.read_csv(os.path.join(OUT, "ls_daily.csv"), index_col=0, parse_dates=True)
    C = L[[k for k in FACTORS] + ["market_ew"]].corr().round(2)
    C.to_csv(os.path.join(OUT, "ls_correlation.csv"))
    return C


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    pd.set_option("display.width", 250)
    cmd = sys.argv[1] if len(sys.argv) > 1 else "baseline"
    if cmd == "baseline":
        S, D, Y = baseline()
        print(S.drop(columns=["family"]).round(3).to_string())
        print((100 * D).round(0).to_string())
        print((100 * Y).round(0).to_string())
    elif cmd == "robust":
        R = robust()
        print(R.pivot_table(index="factor", columns="variant", values="net_t", sort=False).round(1).to_string())
        print(R.pivot_table(index="factor", columns="variant", values="net_ann", sort=False).round(2).to_string())
    elif cmd == "corr":
        print(corr().to_string())
