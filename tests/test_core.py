import numpy as np
import pandas as pd
import pytest

from cmarketlab import indicators as ind
from cmarketlab.data import funding_per_hour, load_perps, panel, universe
from cmarketlab.paths import PERPS_1H


def toy():
    t = pd.date_range("2024-01-01", periods=48, freq="h", tz="UTC")
    a = pd.DataFrame({"symbol": "AAA", "date": t, "close": np.exp(np.linspace(0, 0.47, 48)), "volume": 10.0,
                      "funding_rate": np.where(t.hour % 8 == 0, 1e-4, np.nan)})
    b = a.iloc[24:].assign(symbol="BBB", volume=1.0)  # listed one day later
    return pd.concat([a, b], ignore_index=True)


def test_panel_and_funding():
    df = toy()
    c = panel(df, "close")
    assert c.shape == (48, 2) and c["BBB"].iloc[:24].isna().all()
    f = funding_per_hour(df)
    assert f["AAA"].sum() == pytest.approx(6e-4) and f["BBB"].iloc[:24].isna().all()
    assert ind.rolling_funding(f["AAA"], 24).iloc[-1] == pytest.approx(3e-4)
    assert ind.annualised_funding(f["AAA"], 24).iloc[-1] == pytest.approx(3e-4 * 365.25)


def test_returns_and_universe():
    df = toy()
    c = panel(df, "close")
    assert ind.log_returns(c["AAA"]).iloc[1:].to_numpy() == pytest.approx(np.full(47, 0.01))
    u = universe(df, min_quote_volume=5.0)
    assert u["AAA"].all() and not u["BBB"].any()


def test_liquidation_imbalance():
    lo = pd.Series([3.0, 0.0, 0.0])
    sh = pd.Series([1.0, 0.0, 0.0])
    x = ind.liquidation_imbalance(lo, sh, window=1)
    assert x.iloc[0] == pytest.approx(0.5) and np.isnan(x.iloc[1])


@pytest.mark.skipif(not PERPS_1H.exists(), reason="shared dataset not available")
def test_load_perps_filters():
    df = load_perps(["BTC", "XRP"], fields=["close"], start="2024-01-01", end="2024-01-02")
    assert set(df["symbol"]) == {"BTC", "XRP"} and len(df) == 48
