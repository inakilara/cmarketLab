"""Study 04: order flow, basis / funding thresholds, BTC dominance, price x OI, BTC-S&P correlation, halving timing.

    python research/01_btc_cycle/04_flow_basis_dominance/run.py tests     -> reports/feature_tests.csv (AUC vs study-01 targets)
    python research/01_btc_cycle/04_flow_basis_dominance/run.py extra     -> reports/incremental.csv, by_reading.csv
    python research/01_btc_cycle/04_flow_basis_dominance/run.py halving   -> reports/halving.csv (cycle pivots vs halving dates)
    python research/01_btc_cycle/04_flow_basis_dominance/run.py oi_drops  -> largest one-day drops in aggregate OI value
"""
import os
import sys

import numpy as np
import pandas as pd
import statsmodels.api as sm

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from features import FEATURES, HALVINGS, build  # noqa: E402

from cmarketlab.evaluation import auc, feature_tests  # noqa: E402
from cmarketlab.labels import cycle_targets, zigzag  # noqa: E402

OUT = os.path.join(HERE, "reports")
HORIZONS = (90, 180, 365)
LEV_START = pd.Timestamp("2021-12-01", tz="UTC")
FAM_START = {"flow_spot": None, "flow_perp": pd.Timestamp("2019-10-01", tz="UTC"),
             "basis": pd.Timestamp("2019-10-01", tz="UTC"), "dominance": LEV_START, "price_oi": LEV_START,
             "cross_asset": None}
FAM_SPLIT = {k: pd.Timestamp("2022-01-01" if v is None or v < LEV_START else "2024-01-01", tz="UTC")
             for k, v in FAM_START.items()}


def targets(f, h):
    return cycle_targets(f["close"], h, f["low"], f["high"], f["ma200"])


def tests(n_shift=400):
    f = build()
    tg = {h: targets(f, h)[:2] for h in HORIZONS}
    t = feature_tests(f, FEATURES, tg, family_start={k: v for k, v in FAM_START.items() if v is not None},
                      family_split=FAM_SPLIT, ref_start=LEV_START, n_shift=n_shift)
    t.to_csv(os.path.join(OUT, "feature_tests.csv"), index=False)
    return t


def show(t):
    for side in ("bottom", "top"):
        x = t[t.side == side].pivot_table(index=["family", "feature"], columns="h", values=["auc", "p"])
        x.columns = ["%s_%d" % c for c in x.columns]
        e = t[(t.side == side) & (t.h == 180)].set_index(["family", "feature"])[
            ["direction", "days", "base_rate", "auc_first", "auc_second", "auc_ref_window"]]
        print("\n=== %s (direction-signed AUC; >0.5 supports the hypothesis)" % side.upper())
        print(x.join(e).sort_values("auc_180", ascending=False).round(2).to_string())


def _logit_z(y, controls, x):
    j = controls.assign(x=x, y=y).dropna()
    if len(j) < 200 or j["y"].nunique() < 2 or j["x"].nunique() < 2:
        return np.nan, len(j)
    X = j.drop(columns="y")
    X = (X - X.mean()) / X.std()
    try:
        m = sm.Logit(j["y"], sm.add_constant(X)).fit(disp=0, cov_type="HAC", cov_kwds={"maxlags": 90})
        return float(m.tvalues["x"]), len(j)
    except Exception:
        return np.nan, len(j)


def extra(h=180):
    f = build()
    bottom, top, _ = targets(f, h)
    rows = []
    for side, y in (("bottom", bottom), ("top", top)):
        lev = (-f["oi_chg90"]) if side == "bottom" else f["lev_chg90"]
        for name, (fam, db, dt, *_r) in FEATURES.items():
            d = db if side == "bottom" else dt
            if d is None:
                continue
            x = (d or 1) * f[name]
            yl = y.where(f.index >= LEV_START)
            z_tr, n_tr = _logit_z(y, f[["ma200", "mom180"]], x)
            z_lv, n_lv = _logit_z(yl, lev.rename("lev").to_frame(), x)
            rows.append(dict(side=side, feature=name, z_given_trend=z_tr, days_trend=n_tr,
                             z_given_leverage=z_lv, days_leverage=n_lv, auc_lev_window=auc(x, yl)))
    inc = pd.DataFrame(rows)
    inc.to_csv(os.path.join(OUT, "incremental.csv"), index=False)
    order = ["bottom_zone", "bear_building", "bear", "bull_reset", "bull", "top_zone"]
    g = f[f.index >= LEV_START].groupby("reading")[list(FEATURES)].mean().reindex(order)
    g.insert(0, "days", f[f.index >= LEV_START].groupby("reading").size().reindex(order))
    g.to_csv(os.path.join(OUT, "by_reading.csv"))
    return inc, g


def halving():
    """Major cycle pivots (50 % zigzag on Binance BTC, 2017-08 on) against days since the preceding halving."""
    f = build()
    piv = zigzag(f["close"], 0.5)
    pos = HALVINGS.searchsorted(pd.DatetimeIndex(piv["date"]), side="right") - 1
    piv["halving"] = HALVINGS[pos].date
    piv["days_after_halving"] = (pd.DatetimeIndex(piv["date"]) - HALVINGS[pos]).days
    piv.to_csv(os.path.join(OUT, "halving.csv"), index=False)
    return piv


def oi_drops(n=10):
    from cmarketlab.data import crypto_universe, daily_panel, load_daily
    d = load_daily()
    d = d[d["hours"] == 24]
    u = crypto_universe(d)
    oi = daily_panel(d, "oi_value").reindex(columns=u.columns)
    tot = oi.where(u.astype(bool)).sum(axis=1)
    btc = oi["BTC"]
    t = pd.DataFrame({"total_oi_bn": tot / 1e9, "total_chg_bn": tot.diff() / 1e9,
                      "total_chg_pct": tot.pct_change() * 100, "btc_oi_bn": btc / 1e9, "btc_chg_bn": btc.diff() / 1e9})
    return t.nsmallest(n, "total_chg_bn")


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
    elif cmd == "halving":
        print(halving().to_string())
    elif cmd == "oi_drops":
        print(oi_drops().round(2).to_string())
