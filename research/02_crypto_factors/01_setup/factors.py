"""Factor definitions for project 02. Each signal is a wide daily panel known at day t's close; portfolios are
formed at that close and earn returns from day t+1 (cmarketlab.factors.quantile_portfolios).

FACTORS: name -> (family, builder(panels) -> signal panel, description). Deciles are sorted ascending on the signal,
and the long-short spread is always decile 10 minus decile 1 (high minus low), whatever the sign of the effect.
"""
from cmarketlab.indicators import xsection as xs

FACTORS = {
    # momentum / reversal (price only; total returns are used for the portfolios)
    "rev1":     ("momentum", lambda P: xs.momentum(P.close, 1), "last day's return (short-term reversal)"),
    "mom7":     ("momentum", lambda P: xs.momentum(P.close, 7, skip=1), "return t-7 .. t-1"),
    "mom30":    ("momentum", lambda P: xs.momentum(P.close, 30, skip=1), "return t-30 .. t-1"),
    "mom90":    ("momentum", lambda P: xs.momentum(P.close, 90, skip=1), "return t-90 .. t-1"),
    "mom180":   ("momentum", lambda P: xs.momentum(P.close, 180, skip=7), "return t-180 .. t-7"),
    # volume
    "vol30":    ("volume", lambda P: xs.volume_level(P.quote_volume, 30), "log mean daily volume, 30 d (size)"),
    "vshock":   ("volume", lambda P: xs.volume_shock(P.quote_volume, 7, 90),
                 "log 7-d / 90-d mean volume (abnormal attention)"),
    "turn30":   ("volume", lambda P: xs.turnover(P.quote_volume, P.oi_value, 30),
                 "log volume / open interest, 30 d (churn)"),
    # funding
    "fund1":    ("funding", lambda P: xs.funding_carry(P.funding, 1), "last day's funding, annualised"),
    "fund7":    ("funding", lambda P: xs.funding_carry(P.funding, 7), "funding, 7-day mean, annualised"),
    "fund30":   ("funding", lambda P: xs.funding_carry(P.funding, 30), "funding, 30-day mean, annualised"),
}


def oi_weight(P, n: int = 30):
    """Value weight: trailing mean open interest value (what can actually be traded)."""
    return P.oi_value.rolling(n, min_periods=n // 2).mean()
