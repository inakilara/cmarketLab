"""BTC mid/long-term cycle extremes: hypothesis tests.

    python research/01_btc_cycle/01_cycle_extremes/run.py tests     -> reports/feature_tests.csv (every feature x side x horizon)
    python research/01_btc_cycle/01_cycle_extremes/run.py zones     -> reports/zones.csv, episodes.csv (the leverage-cycle rules)
    python research/01_btc_cycle/01_cycle_extremes/run.py chart     -> reports/leverage_cycle.png
    python research/01_btc_cycle/01_cycle_extremes/run.py current   -> latest reading

Targets (forward-looking, evaluation only), on day t with horizon h days:
    bottom side, on bear days (close < 200-day MA):  "bottom is near"  = lowest low over t+1..t+h > close_t x (1 - 15 %)
    top side,    on bull days (close > 200-day MA):  "top is near"     = highest high over t+1..t+h < close_t x (1 + 15 %)
AUC is signed by the hypothesis direction: > 0.5 supports it. p = circular-shift test (shifts >= 180 days).
"""
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from features import FEATURES, build  # noqa: E402

from cmarketlab.evaluation import episodes, feature_tests  # noqa: E402
from cmarketlab.indicators.cycle import THRESHOLDS, leverage_cycle  # noqa: E402
from cmarketlab.labels import cycle_targets, forward_outcomes, zigzag  # noqa: E402

OUT = os.path.join(HERE, "reports")
HORIZONS = (90, 180, 365)
MOVE = 0.15
PRICE_SPLIT = pd.Timestamp("2023-01-01", tz="UTC")
MARKET_SPLIT = pd.Timestamp("2024-01-01", tz="UTC")
MARKET_START = pd.Timestamp("2021-12-01", tz="UTC")


def targets(f, h, move=MOVE):
    return cycle_targets(f["close"], h, f["low"], f["high"], f["ma200"], move)


def tests(n_shift=400):
    f = build()
    tg = {h: targets(f, h)[:2] for h in HORIZONS}
    t = feature_tests(f, FEATURES, tg, family_start={"market": MARKET_START},
                      family_split={"market": MARKET_SPLIT, "price": PRICE_SPLIT}, ref_start=MARKET_START,
                      n_shift=n_shift)
    t = t.rename(columns={"auc_ref_window": "auc_market_window"})
    t.to_csv(os.path.join(OUT, "feature_tests.csv"), index=False)
    return t


def show(t):
    pd.set_option("display.width", 250)
    for side in ("bottom", "top"):
        x = t[t.side == side].pivot_table(index=["family", "feature"], columns="h", values=["auc", "p"])
        x.columns = ["%s_%d" % c for c in x.columns]
        e = t[(t.side == side) & (t.h == 180)].set_index(["family", "feature"])[
            ["direction", "days", "base_rate", "auc_first", "auc_second", "auc_market_window"]]
        print("\n=== %s (direction-signed AUC; >0.5 supports the hypothesis)" % side.upper())
        print(x.join(e).sort_values("auc_180", ascending=False).round(2).to_string())


ZONES = ["bottom_zone", "bear", "bear_building", "bull_reset", "bull", "top_zone"]
GROUPS = {"all bear": ["bottom_zone", "bear", "bear_building"], "all bull": ["bull_reset", "bull", "top_zone"]}


def readings(f):
    r = leverage_cycle(f["close"], f["btc_oi"], f["lev"])
    r.loc[f.index < MARKET_START, "reading"] = None
    return r


def zones():
    """Outcomes after each reading: P(no further fall > 15 %), P(no further rise > 15 %), median return."""
    f = build()
    r = readings(f)
    rows = []
    for h in HORIZONS:
        o = forward_outcomes(f["close"], h, f["low"], f["high"])
        ok = o["fwd_min"].notna()
        periods = (("all", ok), ("to 2023", ok & (f.index < MARKET_SPLIT)), ("2024 on", ok & (f.index >= MARKET_SPLIT)))
        for period, m in periods:
            for z in ZONES + list(GROUPS):
                sel = r["reading"].isin(GROUPS.get(z, [z])) & m
                if sel.sum() == 0:
                    continue
                oo = o[sel]
                rows.append(dict(h=h, period=period, reading=z, days=int(sel.sum()),
                                 episodes=len(episodes(sel, 60)),
                                 p_no_fall15=(oo["fwd_min"] > -MOVE).mean(), p_no_rise15=(oo["fwd_max"] < MOVE).mean(),
                                 med_ret=oo["fwd_ret"].median(), med_worst=oo["fwd_min"].median(),
                                 med_best=oo["fwd_max"].median()))
    t = pd.DataFrame(rows)
    t.to_csv(os.path.join(OUT, "zones.csv"), index=False)
    # first day of each episode of the four signal readings
    outs = {h: forward_outcomes(f["close"], h, f["low"], f["high"]) for h in HORIZONS}
    ep = []
    for z, kind in (("bottom_zone", "low"), ("top_zone", "high"), ("bear_building", "low"), ("bull_reset", "high")):
        for d in episodes(r["reading"] == z, 60):
            w = f["close"][d - pd.Timedelta(days=180):d + pd.Timedelta(days=180)]
            ext = w.idxmin() if kind == "low" else w.idxmax()
            row = dict(reading=z, date=d.date(), close=f["close"][d],
                       days_in_zone_next120=int((r["reading"][d:d + pd.Timedelta(days=120)] == z).sum()),
                       extreme_pm180=ext.date(), days_after_extreme=(d - ext).days,
                       close_vs_extreme=f["close"][d] / w[ext] - 1)
            for h in HORIZONS:
                o = outs[h].loc[d]
                row.update({"ret_%d" % h: o["fwd_ret"], "worst_%d" % h: o["fwd_min"], "best_%d" % h: o["fwd_max"]})
            ep.append(row)
    e = pd.DataFrame(ep)
    e.to_csv(os.path.join(OUT, "episodes.csv"), index=False)
    return t, e


def show_zones(t, e):
    pd.set_option("display.width", 250)
    order = ZONES + list(GROUPS)
    x = t[t.period == "all"].pivot_table(index="reading", columns="h",
                                         values=["days", "p_no_fall15", "p_no_rise15", "med_ret"])
    x.columns = ["%s_%d" % c for c in x.columns]
    print(x.reindex(order).round(2).to_string())
    y = t[(t.h == 180) & (t.period != "all")].pivot_table(index="reading", columns="period",
                                                          values=["days", "p_no_fall15", "p_no_rise15"])
    print(y.reindex(order).round(2).to_string())
    print(e.round(2).to_string())


def chart():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch
    f = build()
    r = readings(f)
    s = f.index >= MARKET_START
    f, r = f[s], r[s]
    ink, muted, grid = "#1f2328", "#6e7781", "#d8dee4"
    col = {"bottom_zone": "#1f77b4", "bear_building": "#9ab8d8", "top_zone": "#d1651b", "bull_reset": "#f0b98c"}
    lab = {"bottom_zone": "bottom zone: bear, BTC OI 90 d <= -15 %",
           "bear_building": "bear, leverage still building (BTC OI 90 d >= +10 %)",
           "top_zone": "top zone: bull, OI / mcap 90 d > +15 % on >= 30 of 60 d",
           "bull_reset": "bull, deleveraged (BTC OI 90 d <= -10 %)"}
    fig, ax = plt.subplots(2, 1, figsize=(13, 8), sharex=True, gridspec_kw=dict(height_ratios=[3, 2], hspace=0.08))
    for z, c in col.items():
        on = (r["reading"] == z).values
        ax[0].fill_between(f.index, 0, 1, where=on, transform=ax[0].get_xaxis_transform(), color=c,
                           alpha=0.4 if z in ("bottom_zone", "top_zone") else 0.3, linewidth=0)
    ax[0].plot(f.index, f["close"], color=ink, lw=1.5)
    piv = zigzag(f["close"], 0.2)
    for kind, mk in (("low", "^"), ("high", "v")):
        p = piv[piv.kind == kind]
        ax[0].scatter(p["date"], p["price"], marker=mk, s=45, color=muted, zorder=3, edgecolor="white", linewidth=1)
    ax[0].set_yscale("log")
    ax[0].set_ylabel("BTC (USD, log scale)", color=muted)
    ax[0].set_title("BTC and the leverage-cycle readings (readings 2021-12 to 2026-09-30; BTC price to %s)"
                    % f["close"].last_valid_index().date(), loc="left", color=ink)
    handles = [Patch(color=col[z], alpha=0.6, label=lab[z]) for z in col] + [
        plt.Line2D([], [], marker="^", ls="", color=muted, label="20 % swing low / high (known only afterwards)")]
    ax[0].legend(handles=handles, loc="upper left", fontsize=8, frameon=False)
    ax[1].plot(f.index, 100 * f["btc_oi_chg90"], color="#1f77b4", lw=1.5,
               label="BTC open interest (in BTC), 90-day change")
    ax[1].plot(f.index, 100 * f["lev_chg90"], color="#d1651b", lw=1.5,
               label="market open interest / market cap, 90-day change")
    ax[1].axhline(100 * THRESHOLDS["bottom_oi"], color="#1f77b4", lw=1, ls="--")
    ax[1].axhline(100 * THRESHOLDS["top_lev"], color="#d1651b", lw=1, ls="--")
    ax[1].axhline(0, color=muted, lw=0.8)
    ax[1].set_ylabel("% (log change)", color=muted)
    ax[1].legend(loc="lower right", fontsize=8, frameon=False)
    for a in ax:
        a.grid(axis="y", color=grid, lw=0.6)
        a.spines[["top", "right"]].set_visible(False)
        a.spines[["left", "bottom"]].set_color(grid)
        a.tick_params(colors=muted, labelsize=8)
    fig.savefig(os.path.join(OUT, "leverage_cycle.png"), dpi=130, bbox_inches="tight")


def current():
    f = build()
    r = readings(f).dropna(subset=["oi_chg90"])
    print(r.tail(1).T.to_string())
    print(r["reading"].iloc[-120:].value_counts().to_string())


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    cmd = sys.argv[1] if len(sys.argv) > 1 else "tests"
    if cmd == "tests":
        show(tests())
    elif cmd == "show":
        show(pd.read_csv(os.path.join(OUT, "feature_tests.csv")))
    elif cmd == "zones":
        show_zones(*zones())
    elif cmd == "chart":
        chart()
    elif cmd == "current":
        current()
