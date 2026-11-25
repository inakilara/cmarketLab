# 03: which characteristics survive together

**Question.** Are part 02's survivors different factors or one? Do characteristics that fail in decile sorts
still price returns across the whole cross-section?

**Answer.**
- The trend measures are a single factor.
- Beyond trend, positioning prices returns: open-interest leverage, 7-day open-interest growth and liquidation
  imbalance. All three predict lower returns.

## Method

- **Fama–MacBeth** (`cmarketlab.factors.fama_macbeth`):
  - weekly, non-overlapping cross-sections of 7-day forward total returns, winsorised at 1 / 99 %;
  - characteristics ranked to [−0.5, 0.5], missing set to 0, so a slope is the top-minus-bottom return with the
    other characteristics fixed;
  - top100: OLS; oiw: WLS weighted by OI value;
  - 252 weeks; Newey–West t with 4 lags.
- **Spanning:** daily net long-short returns of the part-02 survivors regressed on the market and on all other
  survivors (HAC errors).

## Results

**Spanning.**
- Each trend long-short is explained by the others: R² 0.66–0.93, and alpha t falls from 2–3.4 to between −1
  and +1.5. Momentum, MA ratio, RSI, Bollinger, stochastic and MA cross are one factor. Signed volume (obv30)
  keeps the most of its own information (R² 0.44–0.60, alpha t 1.4–1.8).
- Liquidation imbalance keeps alpha t −1.5 (top100) and −2.1 (oiw).
- Price-only funding is unrelated to the others (R² 0.1–0.16).

**Compact Fama–MacBeth** (one per cluster, plus the perp measures; `reports/fmb_compact.csv`), t-statistics:

| Characteristic | top100 | oiw | 2022–23 (top100 / oiw) | 2024–26 (top100 / oiw) |
|---|---|---|---|---|
| leverage (OI / market cap) | **−2.2** | **−3.1** | −1.2 / −1.9 | −1.9 / −2.5 |
| OI change, 7 d | **−2.8** | **−2.0** | −3.9 / −2.5 | −1.7 / −0.7 |
| liquidation imbalance | −1.5 | **−2.3** | 0.5 / −0.7 | −2.0 / −2.3 |
| residual momentum, 30 d | −2.3 | −2.3 | | |
| size (OI value) | −0.5 | −2.8 | | |
| RSI, MA ratio, signed volume, vol, beta, age, turnover, funding, long liquidations | \|t\| < 1.7 | | | |

- **Leverage and OI growth** do nothing in decile sorts, but price the whole cross-section. Their effect is in
  the middle of the distribution, not the tails. They are the regression counterpart of project 01's market
  leverage cycle: crowded, fast-growing positioning predicts lower returns.
- **The trend coefficients are unstable** once they enter together (collinear). Residual momentum turns negative
  given raw trend, so it should not be read on its own. Use one trend measure.
- **Size** changes sign between versions and methods: no reliable size effect.

The univariate Fama–MacBeth (`reports/fmb_univariate.csv`) agrees:
- long liquidations / OI: t −3.4 / −2.7;
- liquidation imbalance: −3.0 / −3.7;
- leverage: −2.7 / −2.5;
- stochastic: +2.0 / +4.3.

## Reproduce

```
.venv\Scripts\python.exe research\02_crypto_factors\03_multivariate\run.py fmb        # univariate + all survivors
.venv\Scripts\python.exe research\02_crypto_factors\03_multivariate\run.py compact    # one per cluster
.venv\Scripts\python.exe research\02_crypto_factors\03_multivariate\run.py spanning
```
