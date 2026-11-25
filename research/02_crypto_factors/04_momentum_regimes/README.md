# 04: when does cross-sectional trend pay?

**Question.** Momentum and the trend measures lost money in 2022 and won big in 2025–26. In which market states
do they work?

**Answer.**
- Trend works in rising, calm markets.
- It fails in bear-market rebounds (the momentum crash), in high-dispersion markets and when BTC's 90-day trend
  is down (oiw).
- Volatility scaling does not fix it.

## Method

- **Data:** daily net D10 − D1 returns from part 02, for both versions.
- **States:** read at the previous close:
  - BTC vs its 200-day MA, and BTC's 90-day return;
  - the market's 30-day return;
  - bear plus 7-day rebound (market 90-day return < 0, last 7 days up);
  - terciles of cross-sectional return dispersion and of market volatility;
  - project 01's leverage-cycle reading.

## Results (30-day momentum; % a year, t; `reports/regimes.csv`)

| State | top100 | oiw |
|---|---|---|
| market 30-day return up | +128 (2.7) | +123 (3.2) |
| market 30-day return down | +69 (1.7) | +14 (0.4) |
| BTC 90-day return up | +89 (2.5) | +117 (3.1) |
| BTC 90-day return down | +100 (2.0) | +6 (0.2) |
| bear + 7-day rebound | +47 (0.9) | −6 (−0.1) |
| other days | +113 (3.1) | +86 (2.8) |
| market vol low tercile | +188 (2.8) | +113 (2.4) |
| dispersion high tercile | +87 (1.2) | +2 (0.0) |
| leverage reading: bottom zone (117 d) | +335 (2.9) | +197 (2.0) |
| leverage reading: plain bear (320 d) | +90 (1.0) | −32 (−0.5) |

- The MA-ratio factor has the same pattern: +493 % / +299 % a year in the top zone (t 1.8 / 3.8), against about
  zero in a plain bear market (oiw).
- **Volatility scaling** (target 50 % a year from the trailing 30-day vol) leaves the Sharpe ratio about unchanged
  (1.0–1.4) and cuts the maximum drawdown only modestly, from −61 to −66 % to −45 to −60 % (`reports/vol_scaled.csv`).
- **By year** (`reports/by_year.csv`): every trend measure lost 33–61 % in 2022. They earned modest gains in
  2023–24 and large gains in 2025–26.
- **Practical reading:**
  - run trend when the market's 30-day return is positive or BTC's 90-day trend is up;
  - stand aside in bear-market rebounds.

  This switch was chosen in-sample; it needs out-of-sample confirmation.

## Reproduce

```
.venv\Scripts\python.exe research\02_crypto_factors\04_momentum_regimes\run.py
```
