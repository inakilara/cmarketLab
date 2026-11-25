# 04: Remaining ideas from the "macro & microstructure drivers" note

**Question.** The note lists drivers of BTC's cycle turns. Studies 01–03 had already tested open-interest
flushes, funding level and cross-section, liquidations, BTC/alt volume and OI rotation, rates, inflation, the
dollar, M2, the S&P 500 and the VIX. Do the remaining ideas mark mid/long-term tops or bottoms?

**Answer.** None of them adds a new rule. Two confirm what the leverage rule already says; the rest fail.

| Idea in the note | Feature | Result |
|---|---|---|
| Order imbalance (taker buy vs sell) | spot / perp imbalance, 30 and 90 d; spot minus perp | **no signal**; spot-led buying even points the wrong way |
| Funding > 0.05 % / 8 h = overcrowded longs | share of prints above 0.05 % in 30 d | **fails**: since 2022 BTC on Binance almost never prints above 0.05 %; 0.2 % of top-zone days |
| Negative funding = peak fear | share of negative prints in 30 d | a **bear-market** marker (24–26 % of prints in every bear reading), not a bottom marker |
| Funding level | BTC funding, 30 d, 2019 on | 0.73 for bottoms (p 0.11); adds to trend (z 3.3), not to leverage (z 0.6) |
| Perp premium | perp / spot basis, 30 d | 0.65 (p 0.46): not significant |
| Rising BTC dominance at bottoms | market-cap share, level and 90-d change | **unstable**: halves 0.68 / 0.38 |
| Falling dominance at late-bull froth | 90-d change on bull days | 0.75 at 180 d, 0.93 at 365 d (p 0.02), but wrong way in 2022–23; **every top-zone day already had it** |
| Price up + OI down = fragile rally | binary, 90 d | **wrong way** (0.40): such rallies were bull resets, not tops |
| Price up + OI up = confirmed trend | binary, 90 d | **wrong way** (0.38): all 106 top-zone days had it |
| OI growth vs price growth | OI 90-d change minus price 90-d change | 0.86 for bottoms, the same signal as the leverage rule (z 1.3 beyond it) |
| BTC as high-beta risk asset | 90-d correlation with the S&P 500 | no stable signal |
| Halving schedule | days since halving | descriptive only (3 cycles): see below |

## Data

- Binance API, no key: BTCUSDT spot klines (taker buy volume, 2017-08 on), USD-M perpetual klines and the full
  funding-rate history (`cmarketlab.data.funding_history`, 2019-09 on).
- Perps file: market caps for dominance, BTC open interest (2021-09 → 2026-10-01).
- FRED S&P 500, used from the day after each close.
- Targets and tests as in studies 01–03 (`cycle_targets`, direction-signed AUC, circular-shift p, halves, HAC logit
  beyond BTC's trend and beyond the leverage measure).
- Caveat: Binance ran zero-fee BTC spot trading in 2022-07 → 2023-03, which inflates spot volume then.

## Notes on the results

**Funding thresholds from the note are out of date for Binance BTC.** Prints above 0.05 % per 8 h were common in
2020–21 and in March 2024, and almost absent since. Binance's funding is anchored at 0.01 % per 8 h, so a
"hot" bull now shows as *many prints at the 0.01 % cap*, not as spikes. The continuous 30-day average carries the
information. Study 01 already showed that average to be coincident with price.

**Dominance falls at tops, but only where leverage is already hot.** On bull days with BTC's market-cap share down
more than 3 points over 90 days, a top within 15 % followed on 78 % of days (113 days; base 28 %), in episodes
2024-01, 2024-12 and 2025-07. All 106 top-zone days had dominance falling. Outside the top zone the same condition
hit 38 % of the time (26 days). It is a confirmation of the top zone, not an extra rule. The 2022–23 half points
the wrong way, and the universe's share drifts with listings.

**Price × OI.** The note's quadrant reads backwards at the cycle scale. "Price up with OI up" is the late-bull
build-up that the leverage rule flags as a top zone. "Price up with OI down" is the deleveraged bull reset that
came before further gains.

**Fact check: the October 2025 OI drop.** On 2025-10-10, aggregate open interest in the Binance crypto universe fell
$11.0 bn in one day (−34 %), and BTC's alone fell $3.6 bn. That is the largest one-day fall in the file. The note's
$20 bn figure is plausible across all exchanges.

## Halving timing (descriptive; 3 cycles)

Major turns (50 % zigzag on Binance BTC) against days since the preceding halving:

| Halving | Cycle top | Days after | Cycle low | Days after |
|---|---|---|---|---|
| 2016-07-09 | 2017-12-16 | 525 | 2018-12-15 | 889 |
| 2020-05-11 | 2021-11-08 | 546 | 2022-11-21 | 924 |
| 2024-04-20 | 2025-10-06 | 534 | 2026-06-30 (provisional) | 801 |

- Tops fell 525–546 days after the halving in all three cycles.
- The two complete lows came 889–924 days after, which for this cycle meant late Sep to late Oct 2026. The
  window passed with BTC rallying to 84k and then falling to a new low of 55.1k on 2026-11-21 (day 945).
- With three observations the regularity cannot be tested. It may be coincidence, or self-fulfilling. Treat it
  as context, not as a signal.

## Reproduce

```
.venv\Scripts\python.exe research\01_btc_cycle\04_flow_basis_dominance\features.py      # Binance klines + funding, features
.venv\Scripts\python.exe research\01_btc_cycle\04_flow_basis_dominance\run.py tests     # AUC tests
.venv\Scripts\python.exe research\01_btc_cycle\04_flow_basis_dominance\run.py extra     # beyond trend / leverage; by reading
.venv\Scripts\python.exe research\01_btc_cycle\04_flow_basis_dominance\run.py halving   # pivots vs halving dates
.venv\Scripts\python.exe research\01_btc_cycle\04_flow_basis_dominance\run.py oi_drops  # largest one-day OI falls
```

## Code added to the package

- `cmarketlab/data/binance.py`: `funding_history(symbol)`, the full Binance funding history, cached.
- `cmarketlab/indicators/flow.py`: taker imbalance, perp–spot basis, daily funding, share of funding prints
  beyond a threshold, market-cap dominance, rolling return correlation on common days.
