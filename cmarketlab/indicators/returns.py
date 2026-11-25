"""Return and volatility measures."""
import numpy as np

HOURS_PER_YEAR = 24 * 365.25


def log_returns(close, periods: int = 1):
    """log(close_t / close_{t-periods})."""
    return np.log(close).diff(periods)


def realised_vol(close, window: int = 24 * 30, annualise: bool = True, min_periods: int | None = None):
    """Rolling std of hourly log returns over `window` hours, annualised by default."""
    r = log_returns(close)
    v = r.rolling(window, min_periods=min_periods or window // 2).std()
    return v * np.sqrt(HOURS_PER_YEAR) if annualise else v


def zscore(x, window: int, min_periods: int | None = None):
    """(x - rolling mean) / rolling std, trailing only."""
    roll = x.rolling(window, min_periods=min_periods or window // 2)
    return (x - roll.mean()) / roll.std()

