import numpy as np
import pandas as pd
import pytest

from cmarketlab.factors import newey_west_t, quantile_portfolios, quantile_ranks
from cmarketlab.indicators import xsection as xs


def _panel(days=60, names=20, seed=0):
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2024-01-01", periods=days, freq="D", tz="UTC")
    cols = ["C%02d" % i for i in range(names)]
    ret = pd.DataFrame(rng.normal(0, 0.03, (days, names)), index=idx, columns=cols)
    sig = pd.DataFrame(rng.normal(size=(days, names)), index=idx, columns=cols)
    uni = pd.DataFrame(True, index=idx, columns=cols)
    return ret, sig, uni


def test_quantile_ranks_balanced():
    _, sig, uni = _panel(names=20)
    q = quantile_ranks(sig, uni, n=4, min_names=4)
    assert (q.apply(lambda r: r.value_counts(), axis=1) == 5).all().all()
    # higher signal -> higher quantile
    row = sig.iloc[0]
    assert q.iloc[0][row.idxmax()] == 4 and q.iloc[0][row.idxmin()] == 1


def test_hold1_equals_next_day_mean():
    ret, sig, uni = _panel()
    res = quantile_portfolios(sig, ret, uni, n=4, hold=1, min_names=4)
    q = quantile_ranks(sig, uni, n=4, min_names=4)
    t = ret.index[10]
    names = q.loc[ret.index[9]].eq(4)
    assert res.returns.loc[t, 4] == pytest.approx(ret.loc[t, names].mean())
    assert res.ls.loc[t] == pytest.approx(ret.loc[t, names].mean() - ret.loc[t, q.loc[ret.index[9]].eq(1)].mean())


def test_buy_and_hold_cohorts():
    ret, sig, uni = _panel()
    H = 3
    res = quantile_portfolios(sig, ret, uni, n=2, hold=H, min_names=2)
    q = quantile_ranks(sig, uni, n=2, min_names=2)
    j = 20
    t = ret.index[j]
    cohort = []
    for h in range(1, H + 1):
        m = q.iloc[j - h].eq(2)
        g = (1 + ret.iloc[j - h + 1:j][m.index[m]]).prod()      # growth before day t
        w = g / g.sum()
        cohort.append((w * ret.loc[t, m.index[m]]).sum())
    assert res.returns.loc[t, 2] == pytest.approx(np.mean(cohort))


def test_perfect_foresight_is_monotone_and_positive():
    ret, _, uni = _panel(days=200, names=50)
    sig = ret.shift(-1)                                          # tomorrow's return, known today (cheat)
    res = quantile_portfolios(sig, ret, uni, n=5, hold=1, cost_bps=0)
    m = res.returns[[1, 2, 3, 4, 5]].mean()
    assert m.is_monotonic_increasing and res.ls.mean() > 0.03
    assert res.net_ls.equals(res.ls)


def test_missing_return_earns_zero_and_costs_reduce():
    ret, sig, uni = _panel()
    ret.iloc[30:, 0] = np.nan                                    # C00 delisted
    res = quantile_portfolios(sig, ret, uni.where(ret.notna(), False), n=4, hold=5, min_names=4, cost_bps=10)
    assert res.ls.notna().all()
    assert (res.net_ls <= res.ls + 1e-15).all()


def test_characteristics_trailing():
    ret, _, _ = _panel()
    close = (1 + ret).cumprod()
    m = xs.momentum(close, 5, skip=1)
    assert m.iloc[10, 0] == pytest.approx(np.log(close.iloc[9, 0] / close.iloc[5, 0]))
    assert xs.funding_carry(ret, 7).iloc[10, 0] == pytest.approx(ret.iloc[4:11, 0].mean() * 365.25)


def test_newey_west_t_close_to_ols_for_iid():
    x = pd.Series(np.random.default_rng(1).normal(0.1, 1, 5000))
    assert newey_west_t(x, 5) == pytest.approx(x.mean() / x.std() * np.sqrt(len(x)), rel=0.1)


def test_new_characteristics():
    rng = np.random.default_rng(0)
    idx = pd.date_range("2024-01-01", periods=200, freq="D", tz="UTC")
    r = pd.DataFrame(rng.normal(0, 0.03, (200, 5)), index=idx)
    m = r.mean(axis=1)
    r2 = r.add(2 * m, axis=0)                                   # beta = 1/5*... + 2 -> about 2.2 vs m
    b = xs.rolling_beta(r2, m, 90).iloc[-1]
    assert ((b > 1.5) & (b < 3.5)).all()
    assert np.allclose(xs.max_return(r, 30).iloc[-1], r.iloc[-30:].max())
    assert np.allclose(xs.max_return(r, 30, k=3).iloc[-1], r.iloc[-30:].apply(lambda c: c.nlargest(3).mean()))
    c = (1 + r).cumprod()
    assert xs.rsi(c).stack().dropna().between(0, 100).all()
    assert xs.stochastic_k(c, c * 1.01, c * 0.99).stack().dropna().between(0, 1).all()
    sv = xs.signed_volume(r, r.abs() * 0 + 1, 30)
    assert sv.iloc[-1, 0] == pytest.approx(np.sign(r.iloc[-30:, 0]).mean())
    # spread estimator: zero when the close sits at the mid-range
    assert xs.chl_spread(c, c * 1.01, c / 1.01).iloc[-1].abs().max() < 1e-8


def test_fama_macbeth_recovers_slope():
    from cmarketlab.factors import cs_rank, fama_macbeth
    rng = np.random.default_rng(3)
    idx = pd.date_range("2024-01-01", periods=400, freq="D", tz="UTC")
    cols = ["C%02d" % i for i in range(60)]
    x = pd.DataFrame(rng.normal(size=(400, 60)), index=idx, columns=cols)
    z = pd.DataFrame(rng.normal(size=(400, 60)), index=idx, columns=cols)
    uni = pd.DataFrame(True, index=idx, columns=cols)
    fwd = 0.02 * cs_rank(x, uni) + rng.normal(0, 0.01, (400, 60))     # top-minus-bottom = 2 % per period
    S, summ = fama_macbeth({"x": x, "z": z}, fwd, uni, every=7, winsor=0, h=7)
    assert S["x"].mean() == pytest.approx(0.02, abs=0.002)
    assert abs(summ.loc["z", "t_nw"]) < 3 and summ.loc["x", "t_nw"] > 10


def test_taker_flow_characteristics():
    idx = pd.date_range("2024-01-01", periods=10, freq="D", tz="UTC")
    qv = pd.DataFrame({"A": 100.0, "B": 100.0}, index=idx)
    tb = pd.DataFrame({"A": 75.0, "B": 25.0}, index=idx)              # A: 75 % taker buys, B: 25 %
    imb = xs.taker_imbalance(tb, qv, 3)
    assert np.allclose(imb["A"].dropna(), 0.5) and np.allclose(imb["B"].dropna(), -0.5)
    assert np.allclose(xs.taker_shift(tb, qv, 2, 5).dropna(), 0.0)    # constant flow: no shift
    tr = pd.DataFrame({"A": 10.0, "B": 50.0}, index=idx)
    ts = xs.trade_size(qv, tr, 5).dropna()
    assert np.allclose(ts["A"], np.log(10.0)) and np.allclose(ts["B"], np.log(2.0))
    assert xs.taker_imbalance(tb, qv * 0, 3).isna().all().all()        # no volume -> NaN, not inf
