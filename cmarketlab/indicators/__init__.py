"""Market metrics and indicators. Functions take pandas Series / wide DataFrames (index = time, one column per
symbol) and return the same shape, so they work on one symbol or a whole panel. Trailing data only.

    returns      log returns, realised vol, z-scores
    funding      rolling / annualised funding (hourly input)
    positioning  open-interest change, liquidation imbalance (single symbol)
    trend        drawdown, rally, days since high / low, MA ratio, momentum, vol ratio (daily price action)
    market       whole-market breadth, funding, leverage, liquidations, alt strength, correlation, volume
    cycle        leverage-cycle reading of BTC tops / bottoms (study research/01_btc_cycle/01_cycle_extremes)
"""
from . import cycle, flow, market, trend, xsection
from .funding import annualised_funding, rolling_funding
from .positioning import liquidation_imbalance, oi_change
from .returns import log_returns, realised_vol, zscore

__all__ = ["cycle", "market", "trend", "annualised_funding", "rolling_funding", "liquidation_imbalance", "oi_change",
           "log_returns", "realised_vol", "zscore"]
