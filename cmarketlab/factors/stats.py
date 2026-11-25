"""Statistics for daily factor returns (365-day years: crypto trades every day)."""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm

DAYS = 365


def newey_west_t(x: pd.Series, lags: int = 10) -> float:
    """t-statistic of the mean with Newey-West (HAC) errors."""
    x = x.dropna()
    if len(x) < 30:
        return np.nan
    m = sm.OLS(x.values, np.ones(len(x))).fit(cov_type="HAC", cov_kwds={"maxlags": lags})
    return float(m.tvalues[0])


def perf(x: pd.Series, lags: int = 10) -> dict:
    """Annualised mean and vol, Sharpe, NW t of the mean, max drawdown (cumulative simple returns), hit rate."""
    x = x.dropna()
    if len(x) == 0:
        return {}
    eq = (1 + x).cumprod()
    sd = x.std()
    return dict(days=len(x), start=x.index[0].date(), ann_mean=x.mean() * DAYS, ann_vol=sd * np.sqrt(DAYS),
                sharpe=x.mean() / sd * np.sqrt(DAYS) if sd > 0 else np.nan, t_nw=newey_west_t(x, lags),
                max_dd=float((eq / eq.cummax() - 1).min()), hit=float((x > 0).mean()))


def alpha_beta(x: pd.Series, mkt: pd.Series, lags: int = 10) -> dict:
    """x = a + b mkt; annualised alpha, its NW t, beta."""
    j = pd.concat([x.rename("x"), mkt.rename("m")], axis=1).dropna()
    m = sm.OLS(j["x"], sm.add_constant(j["m"])).fit(cov_type="HAC", cov_kwds={"maxlags": lags})
    return dict(alpha=float(m.params["const"]) * DAYS, t_alpha=float(m.tvalues["const"]), beta=float(m.params["m"]))


def by_year(x: pd.Series) -> pd.Series:
    """Compounded return per calendar year."""
    x = x.dropna()
    return (1 + x).groupby(x.index.year).prod() - 1


def spread_summary(res, mkt: pd.Series | None = None, lags: int | None = None) -> dict:
    """One-row summary of a SortResult: LS gross / net performance, alpha vs mkt, turnover, monotonicity
    (Spearman correlation of quantile number with the quantile's mean return)."""
    lags = lags or max(10, 2 * res.hold)
    g, nt = perf(res.ls, lags), perf(res.net_ls, lags)
    qm = res.returns[list(range(1, res.n + 1))].mean() * DAYS
    lo, hi = res.legs[1], res.legs[0]
    row = dict(days=g.get("days"), start=g.get("start"), ls_ann=g.get("ann_mean"), ls_t=g.get("t_nw"),
               ls_sharpe=g.get("sharpe"), ls_vol=g.get("ann_vol"), ls_maxdd=g.get("max_dd"),
               net_ann=nt.get("ann_mean"), net_t=nt.get("t_nw"), net_sharpe=nt.get("sharpe"),
               turnover_day=float((res.turnover[hi] + res.turnover[lo]).mean()),
               mono=float(pd.Series(qm.values).corr(pd.Series(np.arange(1, res.n + 1)), method="spearman")),
               q_low=float(qm.loc[lo]), q_high=float(qm.loc[hi]),
               names_per_q=float(res.names.reindex(res.ls.dropna().index).mean().mean()))
    if mkt is not None:
        row.update(alpha_beta(res.ls, mkt, lags))
    return row
