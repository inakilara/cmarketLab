"""Study 02: BTC <-> alt flows, funding cross-section and return dispersion through the cycle.

    python research/01_btc_cycle/02_rotation_dispersion/run.py tests     -> reports/feature_tests.csv   (AUC vs study-01 targets)
    python research/01_btc_cycle/02_rotation_dispersion/run.py extra     -> reports/incremental.csv      (beyond the leverage rule)
                                                               reports/by_reading.csv       (mean by leverage reading)
    python research/01_btc_cycle/02_rotation_dispersion/run.py profiles  -> reports/profiles.png, profiles.csv (around swing pivots)
"""
import os
import sys

import numpy as np
import pandas as pd
import statsmodels.api as sm

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from features import FEATURES, build  # noqa: E402

from cmarketlab.evaluation import auc, feature_tests, pivot_profiles  # noqa: E402
from cmarketlab.labels import cycle_targets, zigzag  # noqa: E402
from cmarketlab.viz import plot_pivot_profiles  # noqa: E402

OUT = os.path.join(HERE, "reports")
HORIZONS = (90, 180, 365)
START = pd.Timestamp("2021-12-01", tz="UTC")
SPLIT = pd.Timestamp("2024-01-01", tz="UTC")
LEVER = {"bottom": "oi_chg90", "top": "lev_chg90"}   # study 01's leverage measure for each side
LEVER_SIGN = {"bottom": -1, "top": +1}


def targets(f, h):
    return cycle_targets(f["close"], h, f["low"], f["high"], f["ma200"])


def tests(n_shift=400):
    f = build()
    tg = {h: targets(f, h)[:2] for h in HORIZONS}
    fams = {v[0] for v in FEATURES.values()}
    t = feature_tests(f, FEATURES, tg, family_start={k: START for k in fams}, family_split={k: SPLIT for k in fams},
                      n_shift=n_shift)
    t.to_csv(os.path.join(OUT, "feature_tests.csv"), index=False)
    return t


def show(t):
    pd.set_option("display.width", 250)
    for side in ("bottom", "top"):
        x = t[t.side == side].pivot_table(index=["family", "feature"], columns="h", values=["auc", "p"])
        x.columns = ["%s_%d" % c for c in x.columns]
        e = t[(t.side == side) & (t.h == 180)].set_index(["family", "feature"])[
            ["direction", "days", "base_rate", "auc_first", "auc_second"]]
        print("\n=== %s (direction-signed AUC; >0.5 supports the hypothesis)" % side.upper())
        print(x.join(e).sort_values("auc_180", ascending=False).round(2).to_string())


def extra(h=180):
    """Does each feature add to the leverage measure? (1) logistic regression with HAC errors: target ~ leverage +
    feature (both standardised); (2) the feature's AUC within terciles of the leverage measure."""
    f = build()
    bottom, top, _ = targets(f, h)
    rows = []
    for side, y in (("bottom", bottom), ("top", top)):
        lv = LEVER[side]
        for name, (fam, db, dt, *_r) in FEATURES.items():
            d = db if side == "bottom" else dt
            if d is None:
                continue
            sgn = d if d != 0 else 1
            j = pd.DataFrame({"y": y, "lev": LEVER_SIGN[side] * f[lv], "x": sgn * f[name]})
            j = j[j.index >= START].dropna()
            if len(j) < 200 or j["y"].nunique() < 2:
                continue
            z = (j[["lev", "x"]] - j[["lev", "x"]].mean()) / j[["lev", "x"]].std()
            try:
                m = sm.Logit(j["y"], sm.add_constant(z)).fit(disp=0, cov_type="HAC", cov_kwds={"maxlags": 90})
                zx, zl = float(m.tvalues["x"]), float(m.tvalues["lev"])
                m0 = sm.Logit(j["y"], sm.add_constant(z[["lev"]])).fit(disp=0)
                dr2 = float(m.prsquared - m0.prsquared)
            except Exception:
                zx = zl = dr2 = np.nan
            terc = pd.qcut(j["lev"], 3, labels=False)
            at = [auc(g["x"], g["y"]) for _, g in j.groupby(terc)]
            rows.append(dict(side=side, feature=name, family=fam, days=len(j), auc_alone=auc(j["x"], j["y"]),
                             z_feature=zx, z_leverage=zl, pseudo_r2_gain=dr2,
                             auc_lev_low=at[0], auc_lev_mid=at[1], auc_lev_high=at[2]))
    inc = pd.DataFrame(rows)
    inc.to_csv(os.path.join(OUT, "incremental.csv"), index=False)
    # mean of each feature by study-01 reading (descriptive)
    order = ["bottom_zone", "bear_building", "bear", "bull_reset", "bull", "top_zone"]
    g = f[f.index >= START].groupby("reading")[list(FEATURES)].mean().reindex(order)
    g.insert(0, "days", f[f.index >= START].groupby("reading").size().reindex(order))
    g.to_csv(os.path.join(OUT, "by_reading.csv"))
    return inc, g


def profiles(threshold=0.2, span=180):
    """Mean path of each (standardised) feature from -span to +span days around 20 % swing lows and highs."""
    f = build()
    piv = zigzag(f["close"], threshold)
    piv = piv[(piv["date"] >= START + pd.Timedelta(days=90)) & (piv.index < len(piv) - 1)]  # drop provisional last
    prof = pivot_profiles(f.loc[f.index >= START, list(FEATURES)], piv, span)
    prof.to_csv(os.path.join(OUT, "profiles.csv"), index=False)
    nl, nh = (piv["kind"] == "low").sum(), (piv["kind"] == "high").sum()
    plot_pivot_profiles(prof, os.path.join(OUT, "profiles.png"),
                        "Feature paths around BTC 20 %% swing lows (%d) and highs (%d), 2022-2026; z-scores "
                        "(pivots known only afterwards)" % (nl, nh))
    return prof, piv


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    cmd = sys.argv[1] if len(sys.argv) > 1 else "tests"
    pd.set_option("display.width", 250)
    if cmd == "tests":
        show(tests())
    elif cmd == "show":
        show(pd.read_csv(os.path.join(OUT, "feature_tests.csv")))
    elif cmd == "extra":
        inc, g = extra()
        print(inc.round(2).to_string())
        print(g.round(3).T.to_string())
    elif cmd == "profiles":
        prof, piv = profiles()
        print(piv.to_string())
        s = prof[prof.offset.isin([-90, -30, 0, 30, 90])].pivot_table(index=["kind", "feature"], columns="offset",
                                                                       values="mean")
        print(s.round(2).to_string())
