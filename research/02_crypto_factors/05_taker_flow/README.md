# 05: taker order flow

**Question.** Does aggressive buying versus selling (taker flow) drive next-week returns across coins? Is it
different from trend (ma50) and liquidation imbalance?

**Answer.**
- **Yes, strongly.** Coins where takers were net buyers over the last 7 days outperform coins with net taker
  selling. The spread is +83 % to +114 % a year net (t 3.7–4.2), positive in every year 2022–2026 in all three
  versions.
- **It overlaps heavily with liquidation imbalance.** A short liquidation is a forced taker buy. The two
  long-shorts correlate −0.68 to −0.76 (taker buying goes with shorts being liquidated).
- **It adds a little beyond ma50 + liquidations:**
  - spanning alpha t is 2.3 / 2.1 / 1.7;
  - in Fama–MacBeth, 7-day taker imbalance survives the full set of controls (t 2.8 / 2.2 / 1.6), and once it
    is in, liquidation imbalance drops to about zero.
- **As a composite leg** it lifts the Sharpe ratio only from 2.2 to 2.3. The flow is mostly already in the
  liquidation leg.

## Data

- **Source:** Binance USD-M daily klines (`fapi/v1/klines`), fields `taker_buy_quote_volume`, `quote_volume` and
  `trades`, fetched for all 673 coins ever in the universe. The perps file has no taker volume.
- **Cache:** `cache/binance_usdm_<SYM>USDT_1d.parquet`, built with `cmarketlab.data.usdm_daily_panel`.
- **Coverage** (`reports/coverage.csv`):
  - 99.3 % of universe coin-days (99.5 % of top-100 coin-days);
  - 3 symbols are no longer served: AERGO, BDXN, SXP;
  - kline volume equals the perps file's (median ratio 1.000, 5–95 % range 0.997–1.004);
  - the median daily imbalance is −2.5 %: takers sell slightly more than they buy.

## Characteristics (`cmarketlab/indicators/xsection.py`)

| Name | Definition |
|---|---|
| taker1 / taker7 / taker30 | (taker buys − taker sells) / volume over 1 / 7 / 30 days |
| taker_shift | taker7 minus the 60-day imbalance (a change in pressure) |
| flow_gap7 | rank of taker7 minus rank of the 7-day return: buying not yet in the price |
| tradesize30 | log average trade size (USD per trade), 30 days |

## Results

**Decile sorts** (net D10 − D1 at 4 bp per side, % a year, t; `reports/summary.csv`):

| Factor | top100 | oiw | top100_oiw | Capped ±50 % (t) | To end-2024 (t) |
|---|---|---|---|---|---|
| **taker7** | **+114 (4.2)** | **+83 (3.7)** | **+105 (4.0)** | 3.5 / 3.7 / 3.9 | 1.8 / 1.7 / 1.8 |
| taker30 | +104 (3.5) | +102 (3.7) | +109 (3.3) | 2.5 / 3.9 / 3.2 | 2.3 / 2.7 / 2.1 |
| taker1 | +62 (3.7) | +46 (2.9) | +58 (3.6) | 3.5 / 3.0 / 3.6 | 2.2 / 1.8 / 2.1 |
| flow_gap7 | +54 (2.6) | +42 (1.9) | +60 (2.4) | 1.7 / 1.9 / 1.8 | 2.7 / 1.1 / 1.7 |
| taker_shift | +35 (1.5) | +37 (2.0) | +42 (1.4) | | |
| tradesize30 | +2 (0.1) | −7 (−0.3) | +25 (0.8) | | |
| *ma50 (reference)* | +117 (3.0) | +71 (2.6) | +156 (3.3) | | 0.5 / 0.7 / 1.6 |
| *liq_imb7 (reference)* | −80 (−3.2) | −59 (−2.9) | −101 (−4.2) | | −1.3 / −2.1 / −2.7 |

- **Every year positive** for taker7 and taker30 (sum of daily returns, %; `reports/by_year_sum.csv`):

  | taker7 | 2022 | 2023 | 2024 | 2025 | 2026* |
  |---|---|---|---|---|---|
  | top100 | +31 | +52 | +68 | +241 | +165 |
  | oiw | +15 | +32 | +72 | +217 | +50 |
  | top100_oiw | +24 | +47 | +70 | +247 | +105 |

  \*2026 runs January to September.
- **Near-monotone deciles** (Spearman 0.88–0.98). Most of the spread is on the short side: D1, the heaviest net
  selling, earns −56 % to −66 % a year.
- **Unlike trend, it worked before 2025:** t 1.7–2.7 up to the end of 2024, against 0.5–1.6 for ma50.
- **taker30 trades least:** 18–21 % of each leg per day, against 38–41 % for taker7.
- **No trade-size effect.**

**Spanning** (daily net long-short on the market + ma50 + liquidation imbalance, HAC; `reports/spanning.csv`):

| | top100 | oiw | top100_oiw |
|---|---|---|---|
| taker7 alpha, % a year (t) | +37 (2.3) | +37 (2.1) | +28 (1.7) |
| loading on liquidations (t) | −0.72 (−13) | −0.72 (−15) | −0.60 (−12) |
| R² | 0.62 | 0.47 | 0.49 |

flow_gap7 is nearly uncorrelated with ma50 (0.0) and only weakly with liquidations, and keeps alpha t 2.2 / 1.7 /
2.0.

**Fama–MacBeth** (part 03's compact controls plus all taker measures, t; `reports/fmb.csv`):
- **taker7:** +2.8 / +2.2 / +1.6.
- **Liquidation imbalance:** +0.3 / −1.1 / −0.5, down from −1.5 / −2.3 without taker flow.
- **Leverage** stays: −1.8 / −3.3 / −3.2.
- **Other taker measures:** taker30 and taker_shift turn negative only because they are collinear with taker7.

**Composite** (top100_oiw, inverse-vol 180 d; `reports/combo.csv`):

| | % a year | Vol | Sharpe | t | Max drawdown | t to end-2024 |
|---|---|---|---|---|---|---|
| ma50 + liquidations | +124 | 57 | 2.18 | 4.7 | −31 % | 2.9 |
| + taker7 | +117 | 51 | 2.30 | 4.8 | −28 % | 2.8 |
| + flow_gap7 | +98 | 42 | 2.34 | 4.7 | −26 % | 3.1 |

## Reading

- Taker flow and liquidation imbalance measure the same thing: who is forced, or eager, to cross the spread.
  Coins under persistent selling pressure keep underperforming over the next week, and squeezed or bought coins
  keep outperforming.
- Taker volume comes from Binance itself. The liquidation fields come from a third-party aggregator. Taker7 is
  therefore the cleaner and more reproducible input, and it subsumes liquidations in the regressions.
- For a three-leg composite, flow_gap7 diversifies best: it is uncorrelated with ma50 and has the highest Sharpe
  and the lowest drawdown. It was picked after seeing the results.

## Reproduce

```
.venv\Scripts\python.exe research\02_crypto_factors\05_taker_flow\run.py fetch      # once, about 15 min
.venv\Scripts\python.exe research\02_crypto_factors\05_taker_flow\run.py check
.venv\Scripts\python.exe research\02_crypto_factors\05_taker_flow\run.py sorts      # about 8 min
.venv\Scripts\python.exe research\02_crypto_factors\05_taker_flow\run.py spanning
.venv\Scripts\python.exe research\02_crypto_factors\05_taker_flow\run.py fmb
.venv\Scripts\python.exe research\02_crypto_factors\05_taker_flow\run.py combo taker7,taker30,flow_gap7
```
