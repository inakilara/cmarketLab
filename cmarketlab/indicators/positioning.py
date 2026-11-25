"""Positioning measures: open interest and liquidations."""
import numpy as np


def oi_change(open_interest, window: int = 24):
    """Log change of open interest (base units, so price moves do not enter) over `window` hours."""
    return np.log(open_interest).diff(window)


def liquidation_imbalance(long_liq, short_liq, window: int = 24):
    """(long - short) / (long + short) liquidated USD over `window` hours, in [-1, 1]; NaN when none.

    +1: only longs were liquidated (forced selling); -1: only shorts (forced buying).
    """
    lo = long_liq.rolling(window, min_periods=1).sum()
    sh = short_liq.rolling(window, min_periods=1).sum()
    tot = lo + sh
    return ((lo - sh) / tot).where(tot > 0)
