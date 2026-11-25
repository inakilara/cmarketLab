"""Study 03: can macro / traditional-market indicators mark BTC's mid/long-term tops and bottoms?

    python research/01_btc_cycle/03_macro/run.py tests     -> reports/feature_tests.csv  (AUC vs study-01 targets, 2018-2026)
    python research/01_btc_cycle/03_macro/run.py extra     -> reports/incremental.csv     (beyond BTC's own trend; beyond leverage)
    python research/01_btc_cycle/03_macro/run.py profiles  -> reports/profiles.png, profiles.csv (around 20 % swing pivots)
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
from cmarketlab.indicators.cycle import leverage_cycle, leverage_inputs  # noqa: E402
from cmarketlab.labels import cycle_targets, zigzag  # noqa: E402
from cmarketlab.viz import plot_pivot_profiles  # noqa: E402

OUT = os.path.join(HERE, "reports")
HORIZONS = (90, 180, 365)
SPLIT = pd.Timestamp("2022-01-01", tz="UTC")
LEV_START = pd.Timestamp("2021-12-01", tz="UTC")


def targets(f, h):
    return cycle_targets(f["close"], h, f["low"], f["high"], f["ma200"])


def tests(n_shift=400):
    f = build()
    tg = {h: targets(f, h)[:2] for h in HORIZONS}
    fams = {v[0] for v in FEATURES.values()}
    t = feature_tests(f, FEATURES, tg, family_split={k: SPLIT for k in fams}, ref_start=LEV_START, n_shift=n_shift)
    t.to_csv(os.path.join(OUT, "feature_tests.csv"), index=False)
    return t


def show(t):
    pd.set_option("display.width", 250)
    for side in ("bottom", "top"):
        x = t[t.side == side].pivot_table(index=["family", "feature"], columns="h", values=["auc", "p"])
        x.columns = ["%s_%d" % c for c in x.columns]
        e = t[(t.side == side) & (t.h == 180)].set_index(["family", "feature"])[
            ["direction", "days", "base_rate", "auc_first", "auc_second", "auc_ref_window"]]
        print("\n=== %s (direction-signed AUC; >0.5 supports the hypothesis; first = to 2021, second = 2022 on, "
              "ref = 2021-12 on)" % side.upper())
        print(x.join(e).sort_values("auc_180", ascending=False).round(2).to_string())


def _logit_z(y, controls: pd.DataFrame, x: pd.Series):
    j = controls.assign(x=x, y=y).dropna()
    if len(j) < 200 or j["y"].nunique() < 2:
        return np.nan, np.nan, len(j)
    X = j.drop(columns="y")
    X = (X - X.mean()) / X.std()
    try:
        m = sm.Logit(j["y"], sm.add_constant(X)).fit(disp=0, cov_type="HAC", cov_kwds={"maxlags": 90})
        m0 = sm.Logit(j["y"], sm.add_constant(X.drop(columns="x"))).fit(disp=0)
        return float(m.tvalues["x"]), float(m.prsquared - m0.prsquared), len(j)
    except Exception:
        return np.nan, np.nan, len(j)


def extra(h=180):
    """z of each feature in a logit (HAC errors) controlling for (a) BTC's own trend (ma200, mom180), 2018-2026,
    and (b) study 01's leverage measure, 2021-12 on."""
    f = build()
    li = leverage_inputs()
    lc = leverage_cycle(f["close"], li["btc_oi"], li["lev"])
    bottom, top, _ = targets(f, h)
    rows = []
    for side, y in (("bottom", bottom), ("top", top)):
        lev = (-lc["oi_chg90"]) if side == "bottom" else lc["lev_chg90"]
        for name, (fam, db, dt, *_r) in FEATURES.items():
            d = db if side == "bottom" else dt
            sgn = d if d not in (0, None) else 1
            x = sgn * f[name]
            z_tr, r2_tr, n_tr = _logit_z(y, f[["ma200", "mom180"]], x)
            yl = y.where(f.index >= LEV_START)
            z_lv, r2_lv, n_lv = _logit_z(yl, lev.rename("lev").to_frame(), x)
            rows.append(dict(side=side, feature=name, family=fam, z_given_trend=z_tr, r2_gain_trend=r2_tr,
                             days_trend=n_tr, z_given_leverage=z_lv, r2_gain_leverage=r2_lv, days_leverage=n_lv,
                             auc_lev_window=auc(x, yl)))
    inc = pd.DataFrame(rows)
    inc.to_csv(os.path.join(OUT, "incremental.csv"), index=False)
    return inc


def profiles(threshold=0.2, span=180):
    f = build()
    start = f["ma200"].first_valid_index()
    piv = zigzag(f["close"], threshold)
    piv = piv[(piv["date"] >= start) & (piv.index < len(piv) - 1)]
    prof = pivot_profiles(f.loc[f.index >= start, list(FEATURES)], piv, span)
    prof.to_csv(os.path.join(OUT, "profiles.csv"), index=False)
    nl, nh = (piv["kind"] == "low").sum(), (piv["kind"] == "high").sum()
    plot_pivot_profiles(prof, os.path.join(OUT, "profiles.png"),
                        "Macro paths around BTC 20 %% swing lows (%d) and highs (%d), 2018-2026; z-scores "
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
        print(extra().round(2).to_string())
    elif cmd == "profiles":
        prof, piv = profiles()
        print(piv.assign(date=piv.date.dt.date).to_string())
        s = prof[prof.offset.isin([-90, -30, 0, 30, 90])].pivot_table(index=["kind", "feature"], columns="offset",
                                                                       values="mean")
        print(s.round(2).to_string())
