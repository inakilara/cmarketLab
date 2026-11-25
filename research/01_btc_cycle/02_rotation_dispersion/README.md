# 02: BTC ↔ alt flows, funding cross-section and return dispersion through the cycle

**Question.** How do three things behave over BTC's mid/long-term cycle, and do they help call its tops and
bottoms beyond study 01's leverage rule?

1. volume and leverage flows between BTC and altcoins;
2. the market's average funding and its cross-sectional dispersion;
3. the cross-sectional dispersion of returns (a "cross-sectional volatility").

**Answer.**

- **None of the three is a robust timing signal on its own.**
  - Funding and rotation describe the cycle well, but they move *with* the turns rather than ahead of them.
  - Return dispersion across the whole market does predict bottoms, and adds to the leverage rule. But it works
    only when the broad tail of small coins is included, and fails among the 20–100 most liquid coins after
    2023. It is a lead to follow up, not a rule.
- **What the data shows through the cycle:**
  - **Funding** peaks at swing highs and bottoms out at swing lows.
  - **Money concentrates in BTC** (rising share of volume and open interest) into lows, and moves to altcoins into
    highs.
  - **Altcoins** lag into lows and lead after them.
  - **The top zone of study 01** comes with a clear rotation into altcoins: BTC's share of volume is 23 %, against
    33–35 % in other phases.

## Data and method

- **Data:** all Binance, the same as study 01.
  - BTC daily price from the public API.
  - Market panels from the Amberdata perps file, 2021-12 → 2026-09.
  - Same crypto universe: 140–490 coins a day, no TradFi or index perps.
- **Targets:** the same as study 01, built with `cmarketlab.labels.cycle_targets`.
  - Bottom near, on bear days: the lowest low of the next *h* days is within 15 % of the close.
  - Top near, on bull days: the highest high is within 15 %.
  - *h* = 90, 180 or 365 days.
- **Tests:**
  1. Direction-signed AUC with a circular-shift p-value (`cmarketlab.evaluation.feature_tests`).
  2. Value added beyond leverage: a logistic regression of the target on study 01's leverage measure plus the
     feature, with HAC errors (`reports/incremental.csv`). Also the feature's AUC within thirds of the leverage
     measure.
  3. Feature paths around the 19 BTC swing pivots of 20 % or more, 2022–2026 (`reports/profiles.png`).
  4. Means by study 01's reading (`reports/by_reading.csv`).

## Features and hypotheses

Directions were stated before testing. Definitions are in `features.py`; the indicator code is in
`cmarketlab/indicators/market.py`.

| Group | Feature | Hypothesis: bottom / top |
|---|---|---|
| Flows | BTC share of market volume, 30 d; its 90-day change | flight to BTC near bottoms / money leaves BTC for alts near tops |
| | volume share outside BTC + ETH, 30 d; its 90-day change | alt speculation dead / peaking |
| | BTC share of market open interest; its 90-day change | leverage migrates to alts late in the cycle |
| | median alt 90-day return minus BTC's | alts capitulated / altseason |
| Funding | median coin's funding, 30 d (equal-weighted); OI-weighted funding | washed out / hot |
| | cross-sectional spread of 30-day funding (robust std) | (no prior) / froth spreads unevenly at tops |
| | median alt funding minus BTC funding | alt leverage premium gone / high |
| Dispersion | spread of daily returns across coins, 30-day mean | (no prior) / coins diverge at tops |
| | spread of 30-day returns; spread / BTC vol; 90-day change | same; the ratio: everything moves together at capitulation |

## Results

**AUC at 180 days** (direction-signed, > 0.5 supports the hypothesis; shift-test p in brackets). Full table:
`reports/feature_tests.csv`.

| Feature | Bottoms | Tops | Comment |
|---|---|---|---|
| BTC volume share | 0.60 (0.53) | 0.74 (0.20); 0.97 (0.03) at 365 d | tops: low BTC share before tops, mostly 2024+ (halves 0.47 / 0.79) |
| BTC OI share | 0.46 | 0.70 (0.25) | tops only, not significant |
| alt volume share, changes | 0.35–0.46 | 0.53 | no signal |
| alt minus BTC return | 0.57 | 0.63 | no signal (as in study 01) |
| OI-weighted funding | 0.63 (0.88) | 0.58 | no signal (as in study 01) |
| median funding | **0.31** (0.20) | 0.60 | wrong way for bottoms |
| funding dispersion | 0.37 (0.27) | 0.70 (0.14) | tops: right way in both halves (0.68 / 0.67), not significant |
| alt minus BTC funding | **0.21** (0.06); 0.11 (0.04) at 365 d | 0.58 | **reversed**: a *wide* alt premium came with bottoms near |
| return dispersion, daily, all coins | **0.24** (0.03); 0.20 (0.00) at 365 d | 0.63 (0.28) | **low dispersion → bottom near**, both halves (0.16 / 0.15 in the signed form) |
| return dispersion, 30 d | 0.32 (0.15) | 0.62 | same direction, weaker |
| dispersion / BTC vol | 0.54 | 0.58 | no signal |

For the "no prior" features an AUC below 0.5 means *low* values go with the extreme being near. Across 15
features × 2 sides × 3 horizons, about 4 results at p < 0.05 are expected by chance alone. Only return dispersion
(bottoms) is consistent across horizons and halves.

**Beyond the leverage rule** (`reports/incremental.csv`; 180 days; z of the feature in a logit with study 01's
leverage measure):

- **Bottoms:**
  - Daily return dispersion adds the most: z −3.4, pseudo-R² +0.16, AUC 0.12–0.14 within each third of leverage.
    It stays strong with BTC's own 30-day volatility also in the model (z −4.9). So it is not a disguised "calm
    market" effect: BTC volatility alone has AUC 0.42, p 0.66.
  - The alt-minus-BTC funding gap also adds (z +2.7 to +3.1, the reversed sign).
- **Tops:** funding dispersion, BTC OI share, median funding and the alt funding premium add a little
  (z 2.0–2.9). None is significant alone.

**Practical cut: bear days, by dispersion** (all-coin daily dispersion in thirds; cut points 2.16 % and 2.45 %
daily; 180 days):

| Study 01 reading | Low dispersion | Mid | High |
|---|---|---|---|
| bottom zone | 100 % (79 d) | 100 % (18 d) | 80 % (20 d) |
| bear (no leverage signal) | **86 %** (72 d, 4 episodes) | 33 % (136 d) | **6 %** (95 d) |
| bear, leverage building | 8 % | 10 % | 1 % |
| all bear days | 54 % | 27 % | 11 % |

The share is how often BTC did not fall a further 15 % within 180 days. All bear days, by half: to 2023 46 / 10 /
0 %; 2024 on 98 / 43 / 18 %.

**But it depends on which coins are included:**

| Dispersion measured on | AUC 180 d | To 2023 | 2024 on |
|---|---|---|---|
| all coins in the universe | 0.76 (p 0.03) | 0.84 | 0.85 |
| coins listed ≥ 180 days | 0.78 (p 0.08) | 0.80 | 0.82 |
| top 100 by liquidity | 0.58 | 0.82 | 0.37 |
| top 50 | 0.56 | 0.84 | 0.20 |
| top 20 | 0.53 | 0.79 | 0.19 |

(AUC with low dispersion counted as the bottom signal.)

- **Among established, liquid coins:** low dispersion marked bottoms only in 2022–23.
- **Among all coins** (and among those listed over 180 days): it held in 2024–26 as well. The information sits in
  the broad tail of small and mid caps.
- **Plausible reading:** speculation in small caps (large idiosyncratic pumps and dumps) means the bear is not
  exhausted, while a quiet tail means apathy.
- **Caveat:** the dispersion level also drifts with the market's composition: 2026 had record listings. Fixed
  thresholds are not safe.

## How the cycle shows up in these measures

From `reports/profiles.png` (mean z-score paths around 9 swing lows and 10 swing highs) and
`reports/by_reading.csv`:

| | Into swing lows | Into swing highs | Top zone (study 01) vs other bull days |
|---|---|---|---|
| Funding (weighted, median) | falls to its minimum *at* the low (−0.7 z), recovers after | peaks *at* the high (+0.5 z), falls after | +8 % a year weighted, about the same as other bull days |
| BTC share of OI | rises into the low (+0.6 z at the low) | falls into the high (−0.3 z), rises after | 33 % vs 36–38 % |
| BTC share of volume | rises at and after the low | rises after the high | **23 %** vs 33–34 % |
| Alts vs BTC (90 d) | alts lag into the low (−0.6 z), lead after (+0.8 z at +90 d) | | alts relatively strong |
| Funding dispersion | slightly higher at the low | lower at the high (−0.4 z) | lowest of all phases (4.5 % vs 9–12 % in bear phases) |
| Return dispersion | flat | flat | similar |

**Reading the cycle:**

- **Into a low:** leverage and attention retreat to BTC, alt funding and prices capitulate, and funding turns
  negative.
- **Into a high:** money and leverage rotate into altcoins and funding runs hot.
- These are coincident thermometers. By the time funding is at its extreme, the turn is happening, which is why
  their forward-looking tests are weak.
- **Funding dispersion is structurally higher in bear markets** (9–12 % a year) than in bull markets (5 %). In
  bulls most coins sit near Binance's default funding rate. In bears, funding diverges coin by coin.

## Limits

- **Short sample:** 2021-12 → 2026-09, the same as study 01. 19 swing pivots, 4–6 independent bear episodes.
- **Many tests:** 15 features were tested. Only the dispersion result is consistent across horizons and halves,
  and it is sensitive to the universe.
- **The funding-gap result is unexplained:** its sign was opposite to the hypothesis. Treat it as unexplained
  until it is seen again in new data.
- **No new rule is added to the leverage cycle.** If dispersion is used, use it as context on bear days where
  leverage gives no reading, measured on the whole crypto universe.

## Reproduce

```
.venv\Scripts\python.exe research\01_btc_cycle\02_rotation_dispersion\features.py      # feature table -> cache/ (about 10 s)
.venv\Scripts\python.exe research\01_btc_cycle\02_rotation_dispersion\run.py tests     # AUC tests (about 3 min)
.venv\Scripts\python.exe research\01_btc_cycle\02_rotation_dispersion\run.py extra     # beyond leverage; means by reading
.venv\Scripts\python.exe research\01_btc_cycle\02_rotation_dispersion\run.py profiles  # paths around pivots, chart
```

## Code added to the package

- `cmarketlab/indicators/market.py`: `volume_share`, `oi_share`, `funding_cross_section` (median and robust
  spread), `return_dispersion`.
- `cmarketlab/data/universe.py`: `crypto_universe(top_n=...)`, the n most liquid coins each day.
- `cmarketlab/labels/cycles.py`: `cycle_targets`, study 01's targets made reusable.
- `cmarketlab/evaluation/signals.py`: `feature_tests`, study 01's test loop made reusable.
