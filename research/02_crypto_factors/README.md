# Project 02: cross-sectional factors in Binance perpetuals

**Question.** Which coin characteristics drive the cross-section of returns in the Binance USDT-perp universe?
Method: decile sorts and the long-short (D10 − D1) factor-mimicking portfolio, checked with Fama–MacBeth
regressions.

## Conventions (all parts)

- **Returns:** a long position earns the price return minus funding. The data runs 2021-12 → 2026-10-01 (perps
  file, daily).
- **Portfolios:** deciles formed at each close and held 7 days, as overlapping daily cohorts. Long-short is always
  D10 − D1.
- **Costs:** **4 bp per side**, charged on turnover.
- **Statistics:** Newey–West t.
- **Two versions of every test:**
  - **top100:** the 100 most liquid coins each day (30-day median volume), equal weight within deciles;
  - **oiw:** the whole crypto universe (listed 60 days or more, 30-day median volume of $1M or more), weighted by
    30-day mean open-interest value.
- **Verdict per factor:**
  - **robust:** net |t| ≥ 2 in both versions with the same sign, and the same sign in both halves (2022–23,
    2024–26);
  - **candidate:** |t| ≥ 2 in one version, with the same sign in the other.

  With about 50 characteristics, two or three would pass |t| ≥ 2 by chance. A t of 3 is the safer bar.

| Part | What | Main result |
|---|---|---|
| [01_setup](01_setup/README.md) | Build and check the engine on momentum, volume and funding (all coins, equal weight) | Equal-weighted results are dominated by single-coin pumps; use the liquid or open-interest-weighted versions |
| [02_univariate](02_univariate/README.md) | Deciles on 50 characteristics in six families (momentum, risk, size and liquidity, perp microstructure, technical, funding) | One trend cluster (t 2–3.4) and one robust microstructure factor, liquidation imbalance |
| [03_multivariate](03_multivariate/README.md) | Fama–MacBeth and spanning tests | The trend measures are one factor. Open-interest leverage, open-interest growth and liquidation imbalance price returns beyond it |
| [04_momentum_regimes](04_momentum_regimes/README.md) | When trend pays | Up-trending, calm markets; it fails in bear-market rebounds and was flat until 2024 |
| [05_taker_flow](05_taker_flow/README.md) | Taker buy/sell imbalance from Binance klines; adds a third version, top100_oiw (top 100, OI-weighted) | 7-day taker imbalance t 3.7–4.2, positive every year; overlaps strongly with liquidation imbalance and replaces it in regressions |

## Findings

1. **Trend (momentum) is the strongest effect, but it is recent and regime-dependent.**
   - The measures move together: 14–90-day returns, close vs the 50-day MA, RSI, Bollinger %B, stochastic,
     signed volume, share of up days. Their long-short returns explain each other (R² 0.7–0.9).
   - Best single versions: 30-day momentum +95 % a year net (t 3.0, top100) and +61 % (t 2.4, oiw); close vs the
     50-day MA +117 % (t 3.0) and +71 % (t 2.6).
   - They survive returns capped at ±50 % (t 2.1–2.8).
   - **They earned nothing from 2021-12 to the end of 2024** (t −0.3 to 1.6). They lost 35–60 % in 2022 and won big
     in 2025–26.
   - Trend pays when the market is in an uptrend and calm, and fails in bear-market rebounds (the classic
     momentum crash). Scaling by volatility changes little.
2. **Liquidation imbalance is the most robust new factor.**
   - Coins whose last 7 days of liquidations were mostly **shorts** (squeezed) outperform coins where mostly
     **longs** were liquidated: −80 % a year for D10 − D1 (t −3.2, top100) and −59 % (t −2.9, oiw).
   - The spread is negative in every full year 2022–2026 in both versions, survives capped returns and 14-day and
     30-day holds, and is nearly monotone across deciles.
   - It is partly a trend effect, since squeezes happen in rising coins. Beyond the trend factors its alpha
     t is −1.5 (top100) and −2.1 (oiw).
3. **Perp positioning prices returns in the regressions, not in the extreme deciles.**
   - Fama–MacBeth, with trend, size, volatility and the other characteristics held fixed:
     - **leverage** (open-interest value / market cap): t −2.2 / −3.1;
     - **7-day open-interest growth**: t −2.8 / −2.0;
     - **liquidation imbalance**: t −1.5 / −2.3.
   - Crowded, fast-growing positioning predicts lower returns over the next week.
   - Decile spreads miss these because the effect runs through the middle of the distribution, not the tails.
4. **Funding is priced.**
   - Total-return funding sorts are flat.
   - High-funding coins outperform on price (t 1.9–2.4), which pays for the funding. That too is a 2025–26
     effect.
5. **No premium for risk, lottery, size or liquidity.**
   - Volatility, idiosyncratic volatility, beta, downside beta, skewness, largest daily return (MAX), size, age,
     Amihud illiquidity, the high-low spread estimate, turnover and volume shocks all show |t| < 1.8 in sorts.
   - Short-term reversal and 7-day momentum don't work either.
   - Size flips sign between sorts and regressions.

6. **Taker order flow (part 05) is the strongest single signal.**
   - Coins with net taker buying over 7 days beat net-selling coins by +83 % to +114 % a year (t 3.7–4.2).
   - It is positive every year and already worked before 2025 (t 1.7–2.7).
   - It is largely the same information as liquidation imbalance (correlation about −0.7) and replaces it in
     Fama–MacBeth.
   - Top-100 coins weighted by open interest is the best version for ma50 and liquidations. ma50 +
     liquidations, inverse-vol weighted, reaches Sharpe 2.2; adding a taker leg takes it to 2.3.

## Caveats

- **Short history:** 4.8 years with one bear market (2022) and one long bull (2023–26). The momentum result rests
  mostly on 2025–26.
- **No survivorship correction beyond the file:** the perps file includes some delisted contracts, not all.
- **Turnover and costs:** trend factors trade 25–45 % of each leg per day, so at 4 bp per side costs take about
  4–7 % a year. Liquidation imbalance trades 42 % per day (about 6 % a year).

## Next

- A tradable composite: trend plus liquidation imbalance, with a regime switch from part 04 and the project 01
  leverage reading.
- Out-of-sample check when the perps data is refreshed past 2026-10.
- Hourly data for faster microstructure signals (liquidation bursts, funding spikes, open-interest jumps).

## Layout

```
02_crypto_factors/
  common.py              characteristic catalogue (CATALOGUE), versions, costs: shared by parts 02-04
  01_setup/              first engine check (its own factors.py, run.py)
  02_univariate/run.py   sorts | robust | show
  03_multivariate/run.py fmb | compact | spanning
  04_momentum_regimes/run.py
  05_taker_flow/run.py   fetch | check | sorts | spanning | fmb | combo
```

Run order: part 02 `sorts`, then `robust`; part 03 `fmb`, `compact`, `spanning`; part 04. Each reads part 02's
`reports/summary.csv` and `ls_daily.parquet`.

Package code: `cmarketlab/factors/` (panels, sorts, stats, fmb), `cmarketlab/indicators/xsection.py`
(characteristics), `cmarketlab/viz/factors.py`. Tests: `tests/test_factors.py`.
