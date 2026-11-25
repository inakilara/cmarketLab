"""Price-action measures on daily closes (Series or wide DataFrame; window in rows = days). Trailing only."""
import numpy as np


def drawdown(close, window: int | None = 365):
    """close / trailing max - 1 (<= 0); window None = all history."""
    peak = close.cummax() if window is None else close.rolling(window, min_periods=1).max()
    return close / peak - 1


def rally(close, window: int | None = 365):
    """close / trailing min - 1 (>= 0)."""
    low = close.cummin() if window is None else close.rolling(window, min_periods=1).min()
    return close / low - 1


def _days_since(x, window, fn):
    def one(s):
        return s.rolling(window, min_periods=1).apply(lambda a: fn(a[::-1]), raw=True)  # ties: latest occurrence
    return x.apply(one) if hasattr(x, "columns") else one(x)


def days_since_high(close, window: int = 365):
    """Days since the highest close of the trailing `window` days (0 = new high today)."""
    return _days_since(close, window, np.argmax)


def days_since_low(close, window: int = 365):
    """Days since the lowest close of the trailing `window` days (0 = new low today)."""
    return _days_since(close, window, np.argmin)


def ma_ratio(close, n: int = 200):
    """log(close / n-day simple moving average)."""
    return np.log(close / close.rolling(n, min_periods=n).mean())


def momentum(close, n: int):
    """n-day log return."""
    return np.log(close / close.shift(n))


def vol_ratio(close, short: int = 30, long: int = 365):
    """Short-window realised vol / long-window realised vol (daily log returns)."""
    r = np.log(close).diff()
    return r.rolling(short, min_periods=short).std() / r.rolling(long, min_periods=long // 2).std()
