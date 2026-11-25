"""Transforms of macro series held as daily "as known" values (cmarketlab.data.known_daily). Day-based windows,
so they work the same for daily, weekly and monthly source series."""
import numpy as np


def change_days(s, days: int, log: bool = False):
    """Change over `days` calendar rows (daily index): difference, or log change."""
    return np.log(s).diff(days) if log else s.diff(days)


def growth(s, days: int = 365, annualise: bool = False):
    """Percentage growth over `days` (365 = year on year); annualised to a yearly rate if asked."""
    g = s / s.shift(days)
    return g ** (365.25 / days) - 1 if annualise else g - 1


def net_liquidity(fed_assets_mn, tga_mn, rrp_bn):
    """Fed net liquidity, USD bn: Fed balance sheet - Treasury General Account - overnight reverse repo."""
    return fed_assets_mn / 1e3 - tga_mn / 1e3 - rrp_bn


def above_ma(s, n: int = 200):
    """log(s / n-day moving average)."""
    return np.log(s / s.rolling(n, min_periods=n).mean())
