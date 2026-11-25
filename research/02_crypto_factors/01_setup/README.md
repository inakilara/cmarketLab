# 01: setup and first factors (momentum, volume, funding)

**Purpose.** Build the decile-sort engine and check it end to end on a few factors, across all coins with equal
weights. The broad study is in parts 02–04 (see the [project README](../README.md)).

**Costs.** Rerun at 4 bp per side, the project's cost assumption. Net figures below are at 4 bp; gross figures do
not depend on costs.

## Findings so far

1. **Momentum works among liquid coins only.**
   - In the 100 most liquid coins, D10 − D1 earned +98 % a year for both 30-day and 90-day momentum (t 3.1 and
     2.8; net of 4 bp t 3.0 and 2.7). Alpha against the market is the same, and beta is slightly negative.
   - Weighting by open interest gives the same picture: mom30 +65 % (t 2.6).
   - Across all coins, equal-weighted, it disappears (mom30 +25 %, t 1.2). Pumps in small coins land in both
     extreme deciles and swamp it.
   - The effect sits in the tails: D10 +44 %, D1 −54 %, deciles 2–9 flat to negative.
   - It failed in the 2022 bear market (−50 %) and was strong in 2023–26. 2026 alone (+376 to +548 %) carries
     much of it.
2. **Funding is priced: the carry trade earns nothing.**
   - Sorted on funding, high-funding coins beat low-funding ones on *price* by about 75 % a year (t 2.9–3.5).
   - The funding paid offsets that almost exactly. The most negative-funding decile received about +50 % a year
     in funding and lost about −50 % on price.
   - On total return the spread is zero (t 0.0–0.4). Shorting high-funding coins to collect carry loses on price
     what it collects in funding.
3. **Volume: a small-coin effect that changes sign with weighting.**
   - Equal-weighted, high-volume coins underperform: −17 % a year (−36 % on price only, t −2.1).
   - Open-interest-weighted and in the top 100 the sign flips: +11 to +15 %, not significant.
   - Abnormal volume (vshock) and turnover (volume / OI) turn negative once ±50 % days are capped (t −1.3 to
     −1.4). Attention coins underperform apart from the pump days. This is not reliable yet.
4. **Short horizons do not survive costs.**
   - Daily reversal and 7-day momentum have no gross signal.
   - Rebalanced daily, costs of 4 bp take reversal to t −3.0 net.
5. **Long-horizon losers (mom180):**
   - Equal-weighted, past 180-day losers beat winners by 37 % a year (t −1.2).
   - The effect is driven by single pumps in crashed small coins. It is gone in the liquid and open-interest-weighted
     variants.

**What the setup run shows:**
- The choice of universe and weighting matters more than the factor. Every equal-weighted all-coin result must be
  checked against the open-interest-weighted, top-100 and capped variants.
- Most spreads were negative in 2022–23 and positive in 2024–26. That needs a look at the regime: 2022–23 had
  only 50–170 coins, so 5–17 per decile.
- Correlations of the long-short returns: the momentum horizons are related (0.35–0.67). Funding is negatively
  related to volume shock (−0.4). Turnover is the only factor with market beta (0.33).

Tables: `reports/summary.csv`, `deciles.csv`, `by_year.csv`, `robustness.csv`, `ls_correlation.csv`. Charts:
`reports/cumulative.png`, `deciles.png`.

**Next steps:**
- Make the liquid universe (top 100, or open-interest weights) the default.
- Look at liquid momentum by regime (bull / bear, BTC trend).
- Test funding as a price predictor: funding forecasts price, but not total return.
- Add a size factor (market cap / OI value), volatility, beta, skewness / MAX (lottery coins) and listing age.
- Add Fama–MacBeth regressions to see which characteristics survive together.

## Setup

**Universe**, on each day's close (`cmarketlab.data.crypto_universe`):
- crypto perps only (equity, commodity and index perps excluded);
- listed for at least 60 days;
- 30-day median daily volume of $1M or more.

It holds about 50 coins at the end of 2021 and 450 in 2026. Robustness checks use the 100 most liquid only.

**Returns** (`cmarketlab.factors.factor_panels`):
- The return of a long position: close-to-close price return minus that day's funding (positive funding is
  paid by longs). A short earns the negative.
- Funding is therefore part of every factor's return, not only the funding factors'. The "price only" variant
  removes it.
- Data: the Amberdata Binance perps file, 2021-09 → 2026-10-01, built into daily bars.

**Portfolios** (`cmarketlab.factors.quantile_portfolios`):
- At each close t, eligible coins are ranked on the signal into 10 deciles (1 = lowest). At least 5 coins per
  decile are required, so tests start in late 2021.
- A new cohort is formed every day and held buy-and-hold for 7 days (t+1 … t+7). Each day's decile return is
  the mean over the 7 live cohorts (overlapping portfolios, Jegadeesh–Titman). This avoids dependence on the
  rebalancing weekday.
- A coin that stops trading during the hold earns 0 from then on.
- Long-short = D10 − D1: one unit long, one unit short, always high minus low, whatever the sign of the effect.
- Equal weight within deciles. The robustness variant weights by 30-day mean open-interest value.
- Costs: 4 bp per unit traded on each side (the realistic shortfall on Binance), charged on turnover.
  Turnover is the new cohort's weights against those of the cohort formed 7 days earlier.

**Statistics** (`cmarketlab.factors.stats`):
- 365-day years.
- Annualised mean, Newey–West t (lags max(10, 2 × hold)), Sharpe, maximum drawdown.
- Alpha and beta against the equal-weighted universe return.
- Monotonicity: the Spearman correlation of decile number with the decile's mean return.
- Returns per calendar year.

**Robustness variants** (`run.py robust`):
- holding 1 and 30 days;
- quintiles;
- open-interest weights;
- the 100 most liquid coins;
- daily coin returns capped at ±50 %;
- price returns only (no funding);
- halves 2022–23 and 2024–26.

## Data caveat: extreme single-coin days

The universe has 172 coin-days with daily moves beyond ±80 %. They are real moves, with $300M–6.5B of volume
that day, mostly listing squeezes and delisting pumps (ALPACA +505 % on 2025-04-30, HYPER, HIFI, MYX, NFP).
With about 27 equal-weighted coins per decile, one such day moves a decile by 15 % or more. Returns beyond ±50 %
sum to about 26 times the net sum of all coin-day returns. Equal-weighted results must therefore be read next to
the capped and open-interest-weighted variants.

## Reproduce

```
.venv\Scripts\python.exe research\02_crypto_factors\01_setup\run.py baseline   # about 2 min
.venv\Scripts\python.exe research\02_crypto_factors\01_setup\run.py robust     # about 10 min
.venv\Scripts\python.exe research\02_crypto_factors\01_setup\run.py corr
```

To add a factor: write the characteristic in `cmarketlab/indicators/xsection.py` (a trailing wide panel) and add
a line to `FACTORS` in `factors.py`.

## Code added to the package

- `cmarketlab/indicators/xsection.py`: momentum, volume level, volume shock, turnover (volume / OI), funding
  carry.
- `cmarketlab/factors/`: `factor_panels` (returns, universe), `quantile_ranks`, `quantile_portfolios`
  (overlapping buy-and-hold deciles, turnover, costs), `perf`, `newey_west_t`, `alpha_beta`, `by_year`,
  `spread_summary`.
- `cmarketlab/viz/factors.py`: cumulative long-short and decile bar charts.
- `tests/test_factors.py`: hand-computed checks of the sort engine (daily and buy-and-hold cohorts, perfect
  foresight, delisting, costs, characteristics).
