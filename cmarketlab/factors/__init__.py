"""Cross-sectional factor research: quantile-sorted portfolios, long-short spreads and their statistics.

    panels      daily total-return panel (price + funding) and universe for the perps file
    sorts       quantile assignment and overlapping buy-and-hold portfolio returns (Jegadeesh-Titman)
    stats       performance, Newey-West t, alpha / beta vs a market factor, per-year breakdown
    fmb         Fama-MacBeth regressions on rank-scaled characteristics
"""
from .panels import FactorPanels, factor_panels
from .sorts import SortResult, quantile_portfolios, quantile_ranks
from .fmb import cs_rank, fama_macbeth, forward_returns
from .stats import alpha_beta, by_year, newey_west_t, perf, spread_summary

__all__ = ["cs_rank", "fama_macbeth", "forward_returns", "FactorPanels", "factor_panels", "quantile_portfolios", "quantile_ranks", "SortResult", "alpha_beta",
           "by_year", "newey_west_t", "perf", "spread_summary"]
