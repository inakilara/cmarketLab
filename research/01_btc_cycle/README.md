# Project 01: BTC mid/long-term cycle tops and bottoms

**Question.** When is BTC at, or near, the top or bottom of a mid/long-term cycle (about 6 months)? The aim is a
rule set that can say "bearish, but the bottom is in or close" or "bullish, but the top is in or close", without
trading short-term moves.

**Answer.** Leverage is the core signal and rate expectations are the best complement. Almost everything else
tested is coincident or fails.

| Part | Question | Result |
|---|---|---|
| [01_cycle_extremes](01_cycle_extremes/README.md) | Price action and market-wide perp microstructure | **leverage cycle works** on both sides; price-only, funding, liquidations and breadth do not |
| [02_rotation_dispersion](02_rotation_dispersion/README.md) | BTC ↔ alt flows, funding cross-section, return dispersion | coincident with turns; all-coin return dispersion helps for bottoms but depends on the universe |
| [03_macro](03_macro/README.md) | Inflation, rates, liquidity, equities | **2-year yield falling and core inflation cooling mark bottoms**; tops weak |
| [04_flow_basis_dominance](04_flow_basis_dominance/README.md) | Order flow, basis, funding thresholds, dominance, price × OI, halving | no new rule; dominance and price + OI only confirm the top zone |

## The rule set

All changes are over 90 days. "Bear" and "bull" mean BTC below or above its 200-day moving average. Hit rates are
the share of days with no further 15 % move against the reading within 180 days.

**Bottoms (on bear days)**

| Signal | Condition | Hit rate | Usual rate on bear days | Source |
|---|---|---|---|---|
| **Leverage flushed** (bottom zone) | BTC open interest, in BTC, down ≥ 15 % | **97 %** (117 days, 4 episodes) | 33 % | part 01 |
| **Cuts priced** | 2-year Treasury yield down ≥ 25 bp | **86 %** (245 days, 4 of 7 episodes) | 31 % | part 03 |
| Either of the two | | 93 % (196 days, 2021-12 on) | | part 03 |
| Disinflation | core CPI YoY falling over 180 days | AUC 0.78 | | part 03 |

The two main signals rarely coincide: only 19 % of leverage-flush days also had cuts priced. Each one catches
bottoms the other misses. Rate signals fail when yields fall because of a shock (COVID, October 2025), not because
inflation is cooling.

**Warnings (bear continues)**

| Condition | Hit rate |
|---|---|
| Open interest still building (≥ +10 %) | 7 % |
| Open interest still building, and neither the 2-year yield nor core CPI falling | **3 %** |
| Neutral bear with no cuts priced | 25 % (75 % fell another 15 % or more) |
| 2-year yield up ≥ 25 bp | 16 % |

**Tops (on bull days)**

| Signal | Condition | Hit rate | Usual rate on bull days |
|---|---|---|---|
| **Leverage build-up** (top zone) | market open interest / market cap up > 15 %, on ≥ 30 of the last 60 days | **84 %** (106 days, 2 episodes) | 27 % |
| Confirmations, coincident with the top zone | BTC dominance falling (all top-zone days), volume rotating to altcoins (BTC 23 % of volume against 33–35 %), price and open interest both rising | no extra information beyond the top zone | |
| Macro | core CPI re-accelerating | weak (AUC 0.67) | |

The rules are implemented in `cmarketlab.indicators.cycle.leverage_cycle`. The TradingView version is in
`01_cycle_extremes/tradingview/`.

## What did not work

- **Price only:** drawdown depth, distance from moving averages, time since the high or low, momentum.
- **Funding:** level, share negative, dispersion, the note's 0.05 % threshold. Funding moves with the turns
  rather than ahead of them.
- **Liquidations:** capitulation spikes.
- **Breadth:** new highs and lows, altcoin froth, new listings.
- **Order flow:** taker imbalance, spot vs perp.
- **Other market measures:** perp premium, BTC–S&P 500 correlation.
- **Macro:** fed funds, real rates, yield curve, M2, VIX, S&P 500 trend.

## Limits

- The leverage data starts in 2021-12: 4 bottom episodes and 2 top episodes. Macro goes back to 2018 with
  7 rate episodes.
- Treat the rule set as a strong hypothesis, not a proven system.
- The shared perps file ends on 2026-10-01. Reading the leverage rule today needs a data refresh.
- Halving timing (tops 525–546 days after a halving, lows 889–924 days after) rests on three cycles. Use it as
  context only.

## Shared setup

- **Data:** Binance only (Amberdata perps file, Binance API) plus FRED.
- **Targets:** `cmarketlab.labels.cycle_targets`.
- **Tests:** `cmarketlab.evaluation.feature_tests` (direction-signed AUC, circular-shift p, halves).
- **Running:** each part has its own `features.py` and `run.py`, run from the repository root, for example:

```
.venv\Scripts\python.exe research\01_btc_cycle\01_cycle_extremes\run.py zones
```
