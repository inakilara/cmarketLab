# cmarketLab

Market analysis based on perpetual futures data (Binance USDT perps, hourly, 2021-09 → 2026-10).

```
cmarketlab/            reusable package
    data/              load, fetch, clean, transform data
    indicators/        market metrics and indicators
    models/            models of series (GARCH / EGARCH, regressions, regimes, ...)
    labels/            ex-post targets (swing pivots, forward outcomes), for evaluation only
    evaluation/        testing indicators against targets (AUC, shift tests, episodes)
    backtest/          positions, P&L, costs, performance metrics
    viz/               plotting helpers
research/              one folder per project: research/NN_project/[MM_part/] (index in research/README.md)
tests/                 tests of the package
cache/                 derived data (git-ignored)
```

## Setup

```
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m pip install -e .
.venv\Scripts\python.exe -m pytest
```

## Example

```python
from cmarketlab.data import load_perps, panel, funding_per_hour
from cmarketlab import indicators as ind

df = load_perps(["BTC", "ETH", "XRP"], start="2024-01-01")
vol = ind.realised_vol(panel(df, "close"))                    # 30-day annualised, per symbol
carry = ind.annualised_funding(funding_per_hour(df), 24 * 7)  # trailing 7-day funding, per year
```

Data is read in place from `C:\ClaudeSandbox\shared-data\` (read-only).
