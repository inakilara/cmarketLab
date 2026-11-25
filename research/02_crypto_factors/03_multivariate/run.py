"""Part 03: which characteristics survive together? Fama-MacBeth regressions and spanning tests.

    python research/02_crypto_factors/03_multivariate/run.py fmb       -> reports/fmb_univariate.csv, fmb_multi.csv
    python research/02_crypto_factors/03_multivariate/run.py compact   -> reports/fmb_compact.csv (one per cluster)
    python research/02_crypto_factors/03_multivariate/run.py spanning  -> reports/spanning.csv, ls_corr.csv

Fama-MacBeth: weekly (non-overlapping) cross-sections of 7-day forward total returns (winsorised 1 / 99 %) on
characteristics ranked to [-0.5, 0.5]; slope = top-minus-bottom forward return holding the others fixed.
top100: OLS on the 100 most liquid coins; oiw: WLS weighted by 30-day OI value on the whole universe.
Spanning: daily net long-short returns of the part-02 survivors regressed on the market and on each other.
"""
import os
import sys

import numpy as np
import pandas as pd
import statsmodels.api as sm

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import CATALOGUE, FAMILIES, market_for, panels, part_dir, signal  # noqa: E402

from cmarketlab.factors import fama_macbeth, forward_returns  # noqa: E402

OUT = part_dir("03_multivariate")
UNI = os.path.join(os.path.dirname(OUT), "..", "02_univariate", "reports")
CONTROLS = ["size_oi", "beta90", "vol30", "mom30", "fund7"]       # always in the multivariate model
H = 7


def _survivors():
    S = pd.read_csv(os.path.join(UNI, "summary.csv"))
    keep = S[S["verdict"] != "weak"]["factor"].unique().tolist()
    return [f for f in CATALOGUE if f in keep and not f.endswith("_px")]


def fmb():
    P, mkt, versions = panels()
    fwd = forward_returns(P.ret, H)
    names = [f for f in CATALOGUE if not f.endswith("_px")]
    chars = {f: signal(f, P, mkt) for f in names}
    rows, multi = [], []
    for v, (u, w) in versions.items():
        for f in names:
            _, s = fama_macbeth({f: chars[f]}, fwd, u, every=H, weight=w, h=H)
            rows.append(dict(factor=f, family=CATALOGUE[f][0], version=v, **s.loc[f].to_dict()))
        sel = list(dict.fromkeys(CONTROLS + _survivors()))
        _, s = fama_macbeth({f: chars[f] for f in sel}, fwd, u, every=H, weight=w, h=H)
        multi.append(s.assign(version=v).rename_axis("factor").reset_index())
        print(v, "done", flush=True)
    U = pd.DataFrame(rows)
    U.to_csv(os.path.join(OUT, "fmb_univariate.csv"), index=False)
    M = pd.concat(multi)
    M.to_csv(os.path.join(OUT, "fmb_multi.csv"), index=False)
    return U, M


COMPACT = ["size_oi", "age", "beta90", "vol30", "ma50", "resmom30", "rsi14", "obv30", "turnover", "oi_chg7",
           "leverage", "fund7", "liq_long7", "liq_imb7"]


def fmb_compact():
    """One representative per cluster (part 02 spanning shows the trend measures are one factor), plus the
    perp measures that the univariate Fama-MacBeth flags. Also by half."""
    P, mkt, versions = panels()
    fwd = forward_returns(P.ret, H)
    chars = {f: signal(f, P, mkt) for f in COMPACT}
    split = pd.Timestamp("2024-01-01", tz="UTC")
    out = []
    for v, (u, w) in versions.items():
        S, s = fama_macbeth(chars, fwd, u, every=H, weight=w, h=H)
        from cmarketlab.factors import newey_west_t
        for tag, part in (("2022-23", S[S.index < split]), ("2024-26", S[S.index >= split])):
            s["t_" + tag] = [newey_west_t(part[c], 4) for c in S.columns]
        out.append(s.assign(version=v).rename_axis("factor").reset_index())
    M = pd.concat(out)
    M.to_csv(os.path.join(OUT, "fmb_compact.csv"), index=False)
    return M


def spanning():
    """Alpha of each survivor's net LS vs (a) the market, (b) market + the other survivors (same version)."""
    L = pd.read_parquet(os.path.join(UNI, "ls_daily.parquet"))
    P, mkt, versions = panels()
    surv = _survivors() + ["fund7_px"] * ("fund7_px" in [c.split("|")[0] for c in L.columns])
    rows = []
    for v in versions:
        bench = market_for(v, P, versions)
        X = L[[f + "|" + v for f in surv]].rename(columns=lambda c: c.split("|")[0])
        X.corr().round(2).to_csv(os.path.join(OUT, "ls_corr_%s.csv" % v))
        for f in surv:
            j = pd.concat([X[f].rename("y"), bench.rename("mkt"), X.drop(columns=[f])], axis=1).dropna()
            m1 = sm.OLS(j["y"], sm.add_constant(j[["mkt"]])).fit(cov_type="HAC", cov_kwds={"maxlags": 14})
            m2 = sm.OLS(j["y"], sm.add_constant(j.drop(columns="y"))).fit(cov_type="HAC", cov_kwds={"maxlags": 14})
            top = m2.tvalues.drop(["const", "mkt"]).abs().sort_values(ascending=False).head(3)
            rows.append(dict(factor=f, version=v, alpha_mkt=m1.params["const"] * 365, t_mkt=m1.tvalues["const"],
                             alpha_all=m2.params["const"] * 365, t_all=m2.tvalues["const"], r2_all=m2.rsquared,
                             explained_by=", ".join("%s (%.1f)" % (k, m2.tvalues[k]) for k in top.index)))
    R = pd.DataFrame(rows)
    R.to_csv(os.path.join(OUT, "spanning.csv"), index=False)
    return R


if __name__ == "__main__":
    pd.set_option("display.width", 300)
    cmd = sys.argv[1] if len(sys.argv) > 1 else "fmb"
    if cmd == "fmb":
        U, M = fmb()
        print(U.pivot_table(index=["family", "factor"], columns="version", values=["ann_slope", "t_nw"],
                            sort=False).round(2).to_string())
        print(M.round(2).to_string())
    elif cmd == "compact":
        M = fmb_compact()
        print(M.pivot_table(index="factor", columns="version", values=["ann_slope", "t_nw", "t_2022-23", "t_2024-26"],
                            sort=False).round(2).to_string())
    elif cmd == "spanning":
        print(spanning().round(2).to_string())
