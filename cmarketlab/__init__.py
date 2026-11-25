"""cmarketlab: reusable code for market analysis on perpetual futures data.

    cmarketlab.data        load, fetch, clean and transform data (no analysis)
    cmarketlab.indicators  market metrics and indicators computed from the data
    cmarketlab.models      statistical models of series (GARCH-family, regressions, regimes, ...)
    cmarketlab.backtest    turning signals into positions and P&L, cost models, performance metrics
    cmarketlab.labels      ex-post targets (swing pivots, forward outcomes) for evaluation only
    cmarketlab.evaluation  testing indicators against targets (AUC, conditional tables, episodes)
    cmarketlab.viz         plotting helpers shared by analyses

Analyses live in research/<NN_name>/ and import from here.
"""
