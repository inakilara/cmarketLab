# cmarketLab

Market analysis based on perpetual futures data. Python 3.12, own venv: `.venv\Scripts\python.exe`.

## Where code goes

- **`cmarketlab/`** is the reusable package (installed editable in the venv, so `import cmarketlab` works from
  anywhere):
  - `data/`: load / fetch / clean / transform data;
  - `indicators/`: market metrics and indicators;
  - `models/`: modelling of series (GARCH, EGARCH, regressions, regimes, ...);
  - `labels/`: ex-post targets (pivots, forward outcomes), evaluation only, never signal inputs;
  - `evaluation/`: AUC, circular-shift tests, quantile tables, episodes;
  - `backtest/`: positions, P&L, costs, performance metrics;
  - `viz/`: plotting helpers.

  Add a new subpackage when a new kind of reusable code appears.
- **`research/NN_project/`**: one folder per research project, split into `MM_part/` studies when needed (see `research/README.md`). Keep analysis-specific glue there
  and move anything a second analysis could use into the package, with a test in `tests/`.
- Indicator and model functions take a Series or a wide DataFrame (index = UTC hour, columns = symbols) and
  return the same shape; trailing data only.

## Data

- Main dataset: `C:\ClaudeSandbox\shared-data\binance-perps-1h\binance_perps_1h.parquet` (897 Binance USDT
  perps, hourly, 2021-09 → 2026-10; read its README for units). Read it in place with `cmarketlab.data.load_perps`,
  filtering symbols / fields / dates: the full table is about 1.4 GB in memory and RAM is 7.8 GB.
- Derived data: `cache/` (git-ignored) or the analysis's `reports/`. Never write to `shared-data/`.

## Checks

`.venv\Scripts\python.exe -m pytest`
