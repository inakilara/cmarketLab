import numpy as np
import pandas as pd
import pytest

from cmarketlab.data import non_crypto
from cmarketlab.evaluation import auc, episodes, shift_test
from cmarketlab.indicators import trend as tr
from cmarketlab.indicators.cycle import leverage_cycle
from cmarketlab.labels import forward_outcomes, zigzag

IDX = pd.date_range("2024-01-01", periods=10, freq="D", tz="UTC")


def test_zigzag_and_forward():
    c = pd.Series([100, 120, 140, 100, 90, 95, 130, 125, 150, 140.0], index=IDX)
    z = zigzag(c, 0.3)
    assert list(z["kind"]) == ["low", "high", "low", "high"]
    assert list(z["price"]) == [100, 140, 90, 150]
    o = forward_outcomes(c, 2)
    assert o["fwd_ret"].iloc[0] == pytest.approx(0.4)
    assert o["fwd_min"].iloc[2] == pytest.approx(90 / 140 - 1)
    assert o["fwd_max"].iloc[0] == pytest.approx(0.4) and np.isnan(o["fwd_min"].iloc[-2])


def test_trend():
    c = pd.Series([1, 3, 2, 4, 1.0], index=IDX[:5])
    assert tr.drawdown(c, None).iloc[-1] == pytest.approx(-0.75)
    assert list(tr.days_since_high(c, 3)) == [0, 0, 1, 0, 1]
    assert list(tr.days_since_low(c, 5)) == [0, 1, 2, 3, 0]


def test_auc_episodes_shift():
    x = pd.Series(np.arange(10.0), index=IDX)
    y = pd.Series([0, 0, 0, 0, 0, 1, 1, 1, 1, 1.0], index=IDX)
    assert auc(x, y) == 1.0 and auc(-x, y) == 0.0
    s = pd.Series([1, 1, 0, 0, 0, 1, 0, 0, 0, 1], index=IDX).astype(bool)
    assert list(episodes(s, gap=2).day) == [1, 6, 10]
    obs, p, null = shift_test(x, y, n=20, min_shift=2)
    assert obs == 1.0 and 0 < p <= 1


def test_leverage_cycle_readings():
    n = 400
    t = pd.date_range("2022-01-01", periods=n, freq="D", tz="UTC")
    close = pd.Series(np.r_[np.full(250, 100.0), np.linspace(100, 50, 150)], index=t)  # falls below its MA
    oi = pd.Series(np.r_[np.full(300, 1000.0), np.linspace(1000, 600, 100)], index=t)    # OI flushed at the end
    r = leverage_cycle(close, oi, oi / 1e5)
    assert r["reading"].iloc[-1] == "bottom_zone"
    assert r["oi_chg90"].iloc[-1] < -0.15 and r["ma200"].iloc[-1] < 0


def test_non_crypto():
    days = pd.date_range("2025-12-15", periods=28, freq="D", tz="UTC")
    wk = days.day_of_week >= 5
    d = pd.concat([pd.DataFrame({"symbol": "STOCK", "date": days, "quote_volume": np.where(wk, 1.0, 10.0)}),
                   pd.DataFrame({"symbol": "COIN", "date": days, "quote_volume": np.where(wk, 8.0, 10.0)}),
                   pd.DataFrame({"symbol": "BTCDOM", "date": days, "quote_volume": 10.0})])
    assert non_crypto(d) == {"STOCK", "BTCDOM"}


def test_rotation_and_dispersion():
    from cmarketlab.indicators import market as mk
    t = pd.date_range("2024-01-01", periods=40, freq="D", tz="UTC")
    cols = ["BTC", "AAA", "BBB", "CCC"]
    mask = pd.DataFrame(True, index=t, columns=cols)
    qv = pd.DataFrame({"BTC": 3.0, "AAA": 1.0, "BBB": 1.0, "CCC": 1.0}, index=t)
    assert mk.volume_share(qv, mask, ["BTC"], 5).iloc[-1] == pytest.approx(0.5)
    assert mk.oi_share(qv, mask, ["BTC"], 3).iloc[-1] == pytest.approx(0.5)
    fund = pd.DataFrame({"BTC": 1e-4, "AAA": 2e-4, "BBB": 3e-4, "CCC": 4e-4}, index=t)
    med, spread = mk.funding_cross_section(fund, mask, 10)
    assert med.iloc[-1] == pytest.approx(2.5e-4 * 365.25)
    assert spread.iloc[-1] == pytest.approx(1.5e-4 * 365.25 / 1.349)
    g = np.array([0.0, 0.01, 0.02, 0.03])  # constant daily log growth per coin
    close = pd.DataFrame(np.exp(np.outer(np.arange(40), g)), index=t, columns=cols)
    assert mk.return_dispersion(close, mask, 1, 5).iloc[-1] == pytest.approx(0.015 / 1.349)


def test_universe_top_n():
    from cmarketlab.data import crypto_universe
    t = pd.date_range("2024-01-01", periods=80, freq="D", tz="UTC")
    d = pd.concat([pd.DataFrame({"symbol": s, "date": t, "close": 1.0, "quote_volume": v})
                   for s, v in (("AAA", 5e6), ("BBB", 3e6), ("CCC", 2e6))], ignore_index=True)
    u = crypto_universe(d, top_n=2)
    assert u.iloc[-1].to_dict() == {"AAA": True, "BBB": True, "CCC": False}


def test_macro_known_daily_and_transforms(monkeypatch):
    from cmarketlab.data import macro
    from cmarketlab.indicators import macro as mc
    obs = pd.Series([100.0, 101.0, 102.0],
                    index=pd.to_datetime(["2024-01-01", "2024-02-01", "2024-03-01"], utc=True), name="CPIAUCSL")
    monkeypatch.setattr(macro, "fred", lambda i, refresh=False: obs.copy())
    idx = pd.date_range("2024-01-01", "2024-04-30", freq="D", tz="UTC")
    k = macro.known_daily(["CPIAUCSL"], idx)  # 45-day publication lag
    assert np.isnan(k.loc["2024-02-14", "CPIAUCSL"])          # January's value not yet published
    assert k.loc["2024-02-15", "CPIAUCSL"] == 100.0
    assert k.loc["2024-04-14", "CPIAUCSL"] == 101.0 and k.loc["2024-04-15", "CPIAUCSL"] == 102.0
    s = pd.Series([100.0, 110.0, 121.0], index=idx[:3])
    assert mc.growth(s, 1).iloc[-1] == pytest.approx(0.10)
    assert mc.net_liquidity(8e6, 7e5, 300.0) == pytest.approx(8000 - 700 - 300)
