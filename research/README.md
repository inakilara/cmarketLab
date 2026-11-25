# Research

One folder per research project, numbered in the order they were started: `research/NN_project/`. A project that
needs several studies splits them into numbered parts, `research/NN_project/MM_part/`, with a project README that
brings their findings together.

| # | Analysis | Question | Status |
|---|---|---|---|
| 01 | [btc_cycle](01_btc_cycle/README.md) | When is BTC at or near a mid/long-term (~6-month) top or bottom? Four parts: price and microstructure, rotation and dispersion, macro, flow / basis / dominance | done 2026-11-24: leverage cycle (open-interest flush / build-up) plus rate expectations for bottoms; the rest coincident or failing |
| 02 | [crypto_factors](02_crypto_factors/README.md) | Which coin characteristics drive the cross-section of perp returns? Decile long-short portfolios and Fama-MacBeth on 50 characteristics, top-100 and OI-weighted | parts 01-05 done 2026-11-25: one trend factor (recent, regime-dependent); taker flow and liquidation imbalance robust (largely the same signal); OI leverage and OI growth negative in regressions; no risk / size / liquidity / funding premium |

## Layout of a project

```
research/NN_project/
    README.md        the question and the combined findings across parts
    MM_part/         one study (or put these files directly in the project folder when there is only one)
        README.md    question, data and window, method, results, conclusions (the write-up)
        features.py  the study's feature table
        run.py       the entry point (or several scripts: build.py, analyse.py, report.py)
        reports/     outputs: CSV / JSON tables (tracked), PNG figures (tracked), parquet / logs (git-ignored)
```

## Rules

- **Reusable code goes in the `cmarketlab` package, not here.** If a function would be useful to a second analysis,
  it belongs in the package:
  - `cmarketlab/data/`: loading, fetching, cleaning, transforming data;
  - `cmarketlab/indicators/`: market metrics and indicators;
  - `cmarketlab/models/`: models of series (GARCH / EGARCH, regressions, regimes, forecasts);
  - `cmarketlab/labels/`: ex-post targets (swing pivots, forward outcomes), for evaluation only;
  - `cmarketlab/evaluation/`: testing indicators against targets (AUC, shift tests, episodes);
  - `cmarketlab/backtest/`: signals to positions and P&L, costs, performance metrics;
  - `cmarketlab/viz/`: shared plotting helpers.

  The analysis folder keeps only what is specific to that question: its parameters, the glue, the write-up.
- **No look-ahead.** Indicators and signals use trailing data only; state the in-sample / out-of-sample split.
- **Data:** read `C:\ClaudeSandbox\shared-data\` in place (read-only); derived data goes to `cmarketLab/cache/`
  or the analysis's `reports/`.
- **Run** from the repository root: `.venv\Scripts\python.exe research\NN_project\MM_part\run.py`.
- When a project starts, add its row to the table above; update its status as parts finish.
