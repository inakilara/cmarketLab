# 02: univariate decile sorts on 50 characteristics

**Question.** Which single characteristics sort next-week returns, among liquid coins (top100, equal weight) and
in the whole universe weighted by open interest (oiw)?

**Answer.**
- One trend cluster: 14–90-day momentum, close vs MA, RSI, Bollinger, stochastic, signed volume, share of up
  days.
- One robust microstructure factor: liquidation imbalance.
- Nothing from risk, lottery, size, liquidity or total-return funding.

## Method

- **Catalogue:** `../common.py` (`CATALOGUE`). Each characteristic is in `cmarketlab/indicators/xsection.py`.
- **Portfolios:** deciles held 7 days as overlapping cohorts; D10 − D1 net of 4 bp per side; Newey–West t.
- **Alpha:** against the top-100 equal-weighted market or the OI-weighted market.
- **Verdict:**
  - **robust:** net |t| ≥ 2 in both versions with the same sign, and the same sign in both halves;
  - **candidate:** |t| ≥ 2 in one version, with the same sign in the other.
- **Robustness for non-weak factors** (`run.py robust`):
  - daily coin returns capped at ±50 %;
  - holding 14 and 30 days;
  - the sample ending 2024-12-31.

Overview chart: `reports/tstats.png`.

## Results (net D10 − D1, % a year, t)

| Factor | Family | top100 | oiw | Capped ±50 % (t) | To 2024 (t) | Verdict |
|---|---|---|---|---|---|---|
| mom30 | momentum | +95 (3.0) | +61 (2.4) | 2.6 / 2.7 | 0.8 / 0.8 | candidate |
| mom60 | momentum | +110 (2.8) | +57 (2.1) | 2.2 / 2.1 | 0.0 / −0.2 | candidate |
| mom90 | momentum | +96 (2.7) | +48 (1.7) | 2.3 / 1.9 | 1.2 / 0.3 | candidate |
| mom14 | momentum | +70 (2.4) | +61 (2.5) | 2.1 / 2.6 | 0.2 / 1.0 | candidate |
| resmom30 | momentum | +55 (2.0) | +37 (1.7) | 1.5 / 1.5 | 0.5 / 0.3 | candidate |
| upshare30 | momentum | +51 (2.1) | +38 (1.9) | 1.7 / 1.9 | 0.3 / 1.3 | candidate |
| ma50 | technical | +117 (3.0) | +71 (2.6) | 2.7 / 2.8 | 0.5 / 0.7 | candidate |
| rsi14 | technical | +90 (3.2) | +60 (2.7) | 2.8 / 2.7 | 0.6 / 0.7 | candidate |
| stoch14 | technical | +57 (2.6) | +67 (3.4) | 2.8 / 3.9 | 0.1 / 1.6 | candidate |
| bb20 | technical | +56 (2.6) | +55 (2.9) | 2.1 / 2.7 | 0.5 / 0.8 | candidate |
| obv30 | technical | +77 (2.8) | +82 (2.8) | 2.0 / 2.2 | 0.4 / 0.9 | candidate |
| **liq_imb7** | perp | **−80 (−3.2)** | **−59 (−2.9)** | −2.7 / −2.9 | −1.3 / −2.1 | **robust** |
| fund7_px (price only) | perp | +67 (1.9) | +79 (2.4) | 1.6 / 2.0 | −0.3 / −0.2 | candidate |

- The trend factors are "candidate", not "robust", only because the 2022–23 half is about zero. The by-year table
  shows −35 to −60 % in 2022 and large gains in 2025–26.
- **Liquidation imbalance** = (long − short liquidations) / total over 7 days. The deciles run from +26 / +30 % a
  year (D1, mostly shorts liquidated) down to −48 / −23 % (D10, mostly longs liquidated). The long-short spread
  is negative in every full year 2022–2026 in both versions.
- **No signal (|t| < 2 in both versions):**
  - short-term reversal, 7-day and 180-day momentum, 180-day-high proximity;
  - realised, idiosyncratic and range volatility; beta and downside beta; skewness; MAX and MIN (lottery);
  - size (OI and market cap), listing age, volume, Amihud, the Abdi–Ranaldo spread, turnover, volume shock;
  - open-interest change, leverage, funding level and change (total return), long and short liquidations
    separately;
  - MACD, MA cross, close location, price–volume correlation, volatility squeeze.

## Reproduce

```
.venv\Scripts\python.exe research\02_crypto_factors\02_univariate\run.py sorts    # about 10 min
.venv\Scripts\python.exe research\02_crypto_factors\02_univariate\run.py robust   # about 15 min
.venv\Scripts\python.exe research\02_crypto_factors\02_univariate\run.py show
```

Outputs:
- `reports/summary.csv` (one row per factor × version);
- `deciles.csv`, `by_year.csv`, `robustness.csv`;
- `ls_daily.parquet` (daily net long-short returns, used by parts 03–04);
- `tstats.png`, `deciles.png`.
