# 03: Macro and traditional-market indicators at BTC tops and bottoms

**Question.** Can inflation, interest rates and other traditional-market indicators mark BTC's mid/long-term tops
and bottoms?

**Answer.** Partly, and mostly for bottoms.

- **Rate expectations: the best macro marker of a bottom.**
  - In a BTC bear market, once the bond market starts pricing rate cuts (the 2-year Treasury yield down 25 bp or
    more over 90 days), BTC fell less than 15 % further within 180 days on 86 % of days (base 31 %).
  - It worked in both 2018–21 and 2022–26.
  - Counted by episode it is 4 hits in 7. The misses came when yields fell because of a shock (COVID in 2019–20,
    October 2025), not because inflation cooled.
  - The reverse is a clean warning: a bear market with the 2-year yield *rising* 25 bp or more saw a further 15 %
    fall within 180 days on 84 % of days.
- **Inflation is the other clear bottom marker.** Core inflation falling over the last 6 months marks bottoms
  (AUC 0.78, p < 0.01), with equal strength in both halves.
- **Both add information beyond BTC's own trend.** Beyond the leverage rule (2022–26 only) they add little; the
  leverage rule stays first.
- **Tops: macro is weak.** Re-accelerating core inflation is the only consistent sign (AUC 0.67, p 0.05).
- **Coincident only:** the S&P 500, the VIX and the dollar move *with* BTC's turns.
- **Wrong way or one episode:** fed funds, real rates, the yield curve and M2 levels either point the wrong way
  or reflect only the 2022 hiking cycle.

## Data

- **Data:**
  - BTC: Binance daily, 2017-08 → 2026-11 (as in studies 01–02).
  - Macro: FRED (St. Louis Fed) public CSV, fetched with `cmarketlab.data.fred`.
- **Publication lag.** Each series is used only from the day it would have been published
  (`cmarketlab.data.known_daily`):

  | Series | Lag after the observation date |
  |---|---|
  | CPI, core CPI | 45 days |
  | M2 | 55 days |
  | broad dollar | 7 days |
  | Fed balance sheet, TGA | 2 days |
  | yields, fed funds, reverse repo, VIX, S&P 500 | 1 day |

- **Revisions.** FRED serves today's revised values, not the vintage known at the time. That is small for CPI,
  yields and the Fed balance sheet, larger for M2.
- **Dropped.** The high-yield credit spread is on FRED only from 2023-11.
- **Window.** Evaluation runs 2018-03 → 2026: about 1,400 bear days and 1,600 bull days, the longest window of the
  three studies.

## Targets and tests

- **Targets:** as in study 01 (`cmarketlab.labels.cycle_targets`). Bottom near: on bear days (BTC below its
  200-day MA), the lowest low of the next *h* days is within 15 % of the close. Top near: the mirror image on bull
  days.
- **Tests:**
  - Direction-signed AUC with a circular-shift p-value (shifts of 180 days or more). Halves: 2018–21 and 2022–26.
  - Value added: logistic regressions with HAC errors, controlling for (a) BTC's trend (close vs 200-day MA,
    180-day return) over 2018–2026, and (b) study 01's leverage measure over 2021-12 → 2026.
  - Paths around 47 BTC swing pivots of 20 % or more.

## Hypotheses and results

AUC at 180 days, signed by the hypothesis direction (shift-test p in brackets). For "no prior" features an AUC
below 0.5 means *low* values go with the extreme. Full results: `reports/feature_tests.csv`,
`reports/incremental.csv`.

| Hypothesis | Feature | Bottoms | Halves | Tops | Verdict |
|---|---|---|---|---|---|
| Cooling inflation allows easing / re-acceleration ends rallies | core CPI YoY, 180-day change | **0.78 (0.00)**; 0.90 at 365 d | 0.80 / 0.81 | **0.67 (0.05)**; halves 0.68 / 0.68 | **supported** both sides; beyond trend z 1.5 / 1.8 |
| | core CPI 3-month annualised | 0.54 | | 0.50 | no signal |
| | CPI / core YoY level | 0.39 / 0.50 | | 0.59 / 0.54 | no signal |
| Market pricing cuts / hikes | 2-year yield, 90-day change | **0.77 (0.01)** | 0.90 / 0.76 | 0.57 (0.60); 0.63 (0.05) at 90 d | **supported for bottoms**; beyond trend z 2.2; beyond leverage z 1.1 |
| | 2-year yield, 180-day change | 0.68 (0.21) | 0.79 / 0.70 | 0.44 | weaker |
| Policy cycle | fed funds 180-day change | 0.49 | | 0.46 | no signal: the Fed acts late |
| | fed funds level; real policy rate | 0.76 (0.00); 0.71 (0.02) | 0.61 / 0.95; 0.63 / 0.80 | 0.45; 0.52 | mostly the single 2022–24 hiking cycle |
| Cost of holding non-yielding assets | real 10-year yield, 180-day change | 0.56 | | 0.40 | rejected |
| Curve | 10y–2y level; 180-day change | 0.31 (0.22); 0.71 (0.22) | | 0.59; 0.38 | not significant |
| Global liquidity | broad dollar, 90-day change | 0.64 (0.17) | 0.54 / 0.71 | 0.63 (0.17); 0.68 (0.04) at 90 d | weak, right direction |
| | Fed net liquidity, 90-day change | 0.61 (0.29) | 0.49 / 0.69 | 0.53 | weak; beyond trend z 2.5 (bottoms) |
| | M2 YoY | **0.20** (wrong way) | 0.43 / 0.04 | 0.44 | rejected: M2 contracting in 2022–23 coincided with the bottom |
| Risk appetite | VIX, 30-day mean | 0.55 | 0.78 / 0.30 | 0.57 | no stable signal |
| | S&P 500 vs 200-day MA | 0.45 | 0.29 / 0.61 | 0.44 | no stable signal |

About 6 of the 120 tests (20 features × 2 sides × 3 horizons) would reach p < 0.05 by chance. The two inflation
and 2-year-yield results hold at all horizons and in both halves.

## A usable rule: bear market + rate expectations

Bear days (BTC below its 200-day MA), 2018-03 → 2026; outcome over the next 180 days:

| Condition on the day | Days | Episodes | No further 15 % fall | 2018–21 | 2022–26 | Median return |
|---|---|---|---|---|---|---|
| **2-year yield down > 25 bp in 90 days** | 245 | 7 | **86 %** | 83 % | 91 % | +63 % |
| 2-year yield down at all | 450 | 8 | 59 % | 63 % | 55 % | +41 % |
| core CPI YoY falling and 2-year yield falling | 272 | 6 | 68 % | 89 % | 59 % | +45 % |
| all bear days | 1,412 | | 31 % | 29 % | 33 % | +6 % |
| core CPI YoY rising | 863 | 9 | 17 % | 20 % | 13 % | −17 % |
| **2-year yield up > 25 bp in 90 days** | 586 | 4 | **16 %** | 1 % | 21 % | −18 % |
| neither falling (2-year yield and core CPI) | 685 | 6 | **10 %** | 8 % | 12 % | −25 % |

**Threshold sensitivity.** A 2-year yield drop of 0 / 10 / 25 / 50 / 75 bp gives 59 / 68 / 86 / 90 / 89 % at
180 days, and 65–90 % at 90 days. The result is not knife-edge above 25 bp.

**Episodes** (first day after 60 quiet days; 2-year yield down more than 25 bp; bear market):

| Date | BTC | 2-year yield change, 90 d | Next 180 d: worst / return |
|---|---|---|---|
| 2018-12-25 | 3.7k | −0.28 | −11 % / +191 % ✓ |
| 2019-10-03 | 8.2k | −0.29 | −56 % / −22 % ✗ (COVID crash inside the window) |
| 2020-02-28 | 8.7k | −0.50 | −58 % / +32 % ✗ (crash first, then the rebound) |
| 2023-01-12 | 18.8k | −0.27 | −1 % / +62 % ✓ |
| 2024-07-10 | 57.7k | −0.35 | −15 % / +77 % ✓ (borderline) |
| 2025-03-11 | 82.9k | −0.26 | −10 % / +34 % ✓ |
| 2025-10-17 | 106.4k | −0.47 | −44 % / −30 % ✗ |

**By episode: 4 of 7 hits, against 31 % for a random bear day.** The day-level 86 % is higher because the good
episodes lasted longer (67–78 days in the zone, against 4–55 for the misses).

- **When it works:** yields fall because inflation is cooling and cuts are coming (2018-12, 2023-01, 2024-07,
  2025-03).
- **When it fails:** yields fall because of a shock (COVID), and BTC takes the shock first.

**With the leverage rule** (2021-12 → 2026-09):

| Leverage reading | 2-year yield falling | Neither 2-year yield nor core CPI falling |
|---|---|---|
| bottom zone | 90 % (42 d) | 100 % (5 d) |
| bear (no leverage signal) | 46 % (136 d) | 31 % (83 d) |
| bear, leverage building | 50 % (32 d) | **3 %** (219 d) |

So the rate signal mainly separates the bad cases: leverage still building, with no rate relief, almost never
bottomed.

**Tops (weak).** On bull days, core CPI YoY up more than 0.5 pp over 180 days was followed by a top within 15 % on
54 % of days (125 days; base 25 %). There are too few episodes for a rule.

## How macro moves around BTC's turns

From `reports/profiles.png`: mean z-scores around 23 swing lows and 24 swing highs, 2018–2026.

- **2-year yield:** it rises into BTC lows (+0.2 z from 90 to 30 days before), then falls after them (−0.2 z at
  +30 days). This is the same pattern as the rule.
- **VIX:** lowest right at BTC highs (−0.35 z, complacency), and spikes just after lows.
- **S&P 500:** strongest at BTC highs and drops sharply at BTC lows. It moves with BTC, not ahead of it.
- **Dollar:** rises in the months after BTC highs.
- **Inflation, fed funds, real rates, curve, M2:** the same path around lows and highs. They are too slow to time
  swings of a few months. Their value is in telling which *regime* a bear market is in.

## Limits

- **Few macro regimes.** 2018–26 holds about two easing and two tightening phases (2019 cuts, 2020 shock,
  2022–23 hikes, 2024–25 cuts). The slow variables have only a handful of independent episodes; the rule above
  has 7.
- **Shock-driven falls in yields** look like "cuts priced" but are not bullish at first.
- **Revised data.** FRED's latest values are used; for CPI and yields the difference from what was known at the
  time is negligible.
- **US-centric.** Global liquidity (other central banks, China) is not included.

## Reproduce

```
.venv\Scripts\python.exe research\01_btc_cycle\03_macro\features.py      # FRED download (cached in cache/), feature table
.venv\Scripts\python.exe research\01_btc_cycle\03_macro\run.py tests     # AUC tests (about 4 min)
.venv\Scripts\python.exe research\01_btc_cycle\03_macro\run.py extra     # beyond BTC trend; beyond leverage
.venv\Scripts\python.exe research\01_btc_cycle\03_macro\run.py profiles  # paths around pivots, chart
```

## Code added to the package

- `cmarketlab/data/macro.py`: FRED download with cache; `known_daily` applies each series' publication lag.
- `cmarketlab/indicators/macro.py`: growth (YoY, annualised), changes, Fed net liquidity, MA ratio.
- `cmarketlab/indicators/cycle.py`: `leverage_inputs()`, the leverage series for any study.
- `cmarketlab/evaluation/signals.py`: `pivot_profiles`.
- `cmarketlab/viz/profiles.py`: `plot_pivot_profiles` (study 02 uses both too).
