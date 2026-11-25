"""Part 02: univariate decile sorts on the whole characteristic catalogue, in both versions (top100, oiw).

    python research/02_crypto_factors/02_univariate/run.py sorts  -> reports/summary.csv, deciles.csv, by_year.csv,
                                                                     ls_daily.parquet, tstats.png, deciles.png
    python research/02_crypto_factors/02_univariate/run.py robust -> reports/robustness.csv (capped, holds, to 2024)
    python research/02_crypto_factors/02_univariate/run.py show   -> print the saved summary
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import CATALOGUE, COST_BPS, FAMILIES, HOLD, N, SPLIT, market_for, panels, part_dir, returns_for, signal  # noqa

from cmarketlab.factors import by_year, perf, quantile_portfolios, spread_summary  # noqa: E402
from cmarketlab.viz.factors import plot_quantile_means, plot_tstats  # noqa: E402

OUT = part_dir("02_univariate")


def sorts():
    P, mkt, versions = panels()
    bench = {v: market_for(v, P, versions) for v in versions}
    rows, dec, yrs, daily = [], {}, {}, {}
    for name, spec in CATALOGUE.items():
        s = signal(name, P, mkt)
        r = returns_for(name, P)
        for v, (u, w) in versions.items():
            res = quantile_portfolios(s, r, u, n=N, hold=HOLD, weight=w, cost_bps=COST_BPS)
            row = dict(factor=name, family=spec[0], version=v, **spread_summary(res, bench[v]))
            for tag, part in (("h1", res.net_ls[res.net_ls.index < SPLIT]), ("h2", res.net_ls[res.net_ls.index >= SPLIT])):
                p = perf(part, 14)
                row["net_ann_" + tag], row["net_t_" + tag] = p.get("ann_mean"), p.get("t_nw")
            rows.append(row)
            dec[(name, v)] = res.returns[list(range(1, N + 1))].mean() * 365
            yrs[(name, v)] = by_year(res.net_ls)
            daily[name + "|" + v] = res.net_ls
        print(name, " ".join("%s t=%.1f" % (r_["version"], r_["net_t"]) for r_ in rows[-2:]), flush=True)
    S = pd.DataFrame(rows)
    S["verdict"] = S.groupby("factor", group_keys=False).apply(_verdict, include_groups=False).reindex(S.index)
    S.to_csv(os.path.join(OUT, "summary.csv"), index=False)
    D = pd.DataFrame(dec).T
    D.index.names = ["factor", "version"]
    D.to_csv(os.path.join(OUT, "deciles.csv"))
    Y = pd.DataFrame(yrs).T
    Y.index.names = ["factor", "version"]
    Y.to_csv(os.path.join(OUT, "by_year.csv"))
    pd.DataFrame(daily).to_parquet(os.path.join(OUT, "ls_daily.parquet"))
    charts(S, D)
    return S


def _verdict(g):
    """robust: net |t| >= 2 in both versions with the same sign, and the same sign in both halves of both.
    candidate: net |t| >= 2 in one version, same sign in the other. weak: otherwise."""
    t = g.set_index("version")["net_t"]
    same = np.sign(t).nunique() == 1
    halves = np.sign(pd.concat([g["net_t_h1"], g["net_t_h2"]])).nunique() == 1
    if same and (t.abs() >= 2).all() and halves:
        v = "robust"
    elif same and (t.abs() >= 2).any():
        v = "candidate"
    else:
        v = "weak"
    return pd.Series(v, index=g.index)


def charts(S, D):
    order = [f for fam in FAMILIES for f in CATALOGUE if CATALOGUE[f][0] == fam]
    T = S.set_index("factor").loc[order].reset_index()
    plot_tstats(T, os.path.join(OUT, "tstats.png"),
                "Decile D10 - D1, net of 4 bp, Newey-West t (top 100 equal weight vs all coins OI-weighted)")
    keep = S[S.verdict != "weak"]["factor"].unique().tolist()
    if keep:
        plot_quantile_means({"%s (%s)" % (f, v): D.loc[(f, v)] for f in keep for v in ("top100", "oiw")},
                            os.path.join(OUT, "deciles.png"),
                            "Mean return by decile for robust and candidate factors (gross, annualised)")


def robust():
    """Robust and candidate factors: daily coin returns capped at +-50 % (pump days), holding 14 and 30 days, and
    without 2025-26 (the strongest years)."""
    P, mkt, versions = panels()
    S = pd.read_csv(os.path.join(OUT, "summary.csv"))
    keep = S[S.verdict != "weak"]["factor"].unique().tolist()
    rows = []
    for name in keep:
        s = signal(name, P, mkt)
        r = returns_for(name, P)
        for v, (u, w) in versions.items():
            var = {"capped +-50 %": dict(ret=r.clip(-0.5, 0.5)), "hold 14": dict(hold=14), "hold 30": dict(hold=30)}
            for tag, kw in var.items():
                res = quantile_portfolios(s, kw.get("ret", r), u, n=N, hold=kw.get("hold", HOLD), weight=w,
                                          cost_bps=COST_BPS)
                p = perf(res.net_ls, 2 * res.hold)
                rows.append(dict(factor=name, version=v, variant=tag, net_ann=p["ann_mean"], net_t=p["t_nw"]))
            base = pd.read_parquet(os.path.join(OUT, "ls_daily.parquet"))[name + "|" + v]
            p = perf(base[base.index < pd.Timestamp("2025-01-01", tz="UTC")], 14)
            rows.append(dict(factor=name, version=v, variant="to 2024", net_ann=p["ann_mean"], net_t=p["t_nw"]))
        print(name, flush=True)
    R = pd.DataFrame(rows)
    R.to_csv(os.path.join(OUT, "robustness.csv"), index=False)
    return R


def show():
    S = pd.read_csv(os.path.join(OUT, "summary.csv"))
    cols = ["net_ann", "net_t", "net_t_h1", "net_t_h2", "t_alpha", "beta", "mono", "turnover_day"]
    X = S.pivot_table(index=["family", "factor", "verdict"], columns="version", values=cols, sort=False)
    X.columns = ["%s_%s" % c for c in X.columns]
    print(X.round(2).to_string())


if __name__ == "__main__":
    pd.set_option("display.width", 300)
    cmd = sys.argv[1] if len(sys.argv) > 1 else "sorts"
    if cmd == "sorts":
        sorts()
    if cmd == "robust":
        R = robust()
        print(R.pivot_table(index="factor", columns=["version", "variant"], values="net_t", sort=False).round(1)
              .to_string())
    else:
        show()
