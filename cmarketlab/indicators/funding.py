"""Funding-rate measures. Input: hourly funding paid by longs (data.funding_per_hour), decimal of notional."""
from .returns import HOURS_PER_YEAR


def rolling_funding(fph, window: int = 24):
    """Funding paid by longs over the trailing `window` hours (sum of events)."""
    return fph.rolling(window, min_periods=window).sum()


def annualised_funding(fph, window: int = 24 * 7):
    """Trailing funding carry as a decimal of notional per year paid by longs (positive = longs pay shorts)."""
    return rolling_funding(fph, window) * HOURS_PER_YEAR / window
