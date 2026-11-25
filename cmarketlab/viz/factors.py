"""Charts for factor sorts: cumulative long-short returns and mean return by quantile."""
from __future__ import annotations

import numpy as np

INK, MUTED, GRID = "#1f2328", "#6e7781", "#d8dee4"
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]  # fixed order


def _style(ax):
    ax.tick_params(colors=MUTED, labelsize=7)
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color(GRID)
    ax.grid(axis="y", color=GRID, lw=0.5)


def plot_cumulative(groups: dict, path: str, title: str, ylabel: str = "cumulative log return"):
    """groups = {panel title: {series name: daily return Series}}; one panel per group, cumulative log returns."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    k = len(groups)
    fig, axes = plt.subplots(1, k, figsize=(4.6 * k, 3.4), sharey=True, squeeze=False)
    for ax, (name, series) in zip(axes[0], groups.items()):
        for c, (lab, s) in zip(SERIES, series.items()):
            s = s.dropna()
            ax.plot(s.index, np.log1p(s.clip(lower=-0.99)).cumsum(), color=c, lw=1.5, label=lab)
        ax.axhline(0, color=MUTED, lw=0.8)
        ax.set_title(name, fontsize=9, color=INK, loc="left")
        ax.legend(fontsize=7, frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.1),
                  ncol=min(len(series), 4))
        _style(ax)
    axes[0][0].set_ylabel(ylabel, fontsize=8, color=MUTED)
    fig.suptitle(title, x=0.01, ha="left", color=INK, fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(path, dpi=120, bbox_inches="tight")
    plt.close(fig)


def plot_tstats(table, path: str, title: str, value: str = "net_t", group: str = "family",
                 series: str = "version", ref=(2, 3)):
    """Dot plot of a statistic per factor (rows, grouped by `group`), one marker colour per `series` value."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    order = list(dict.fromkeys(table["factor"]))
    fams = table.drop_duplicates("factor").set_index("factor")[group]
    sers = list(dict.fromkeys(table[series]))
    fig, ax = plt.subplots(figsize=(7.5, 0.24 * len(order) + 1.4))
    y = {f: len(order) - i for i, f in enumerate(order)}
    for x in ref:
        for s in (-x, x):
            ax.axvline(s, color=GRID, lw=0.8, ls="--" if x == ref[0] else ":")
    ax.axvline(0, color=MUTED, lw=0.8)
    for k, s in enumerate(sers):
        d = table[table[series] == s]
        ax.scatter(d[value], [y[f] + (0.15 if k == 0 else -0.15) for f in d["factor"]], s=22, color=SERIES[k],
                   label=s, zorder=3, edgecolors="white", linewidths=0.6)
    prev = None
    for f in order:
        if prev is not None and fams[f] != fams[prev]:
            ax.axhline(y[f] + 0.5, color=GRID, lw=0.8)
        prev = f
    ax.set_yticks([y[f] for f in order])
    ax.set_yticklabels(["%s  (%s)" % (f, fams[f]) for f in order], fontsize=7, color=INK)
    ax.set_xlabel("%s of D10 - D1 (dashed: 2, dotted: 3)" % value, fontsize=8, color=MUTED)
    ax.legend(fontsize=7, frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.06), ncol=len(sers))
    _style(ax)
    ax.grid(False)
    ax.set_title(title, fontsize=10, color=INK, loc="left")
    fig.tight_layout()
    fig.savefig(path, dpi=120, bbox_inches="tight")
    plt.close(fig)


def plot_quantile_means(means: dict, path: str, title: str, cols: int = 4):
    """means = {factor: Series indexed 1..n of annualised mean returns}; one bar panel per factor."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    names = list(means)
    rows = int(np.ceil(len(names) / cols))
    fig, axes = plt.subplots(rows, cols, figsize=(3.2 * cols, 2.5 * rows + 0.6), squeeze=False, sharey=True)
    for ax, name in zip(axes.flat, names):
        m = means[name]
        ax.bar(m.index.astype(int), 100 * m.values, width=0.7, color=SERIES[0])
        ax.axhline(0, color=MUTED, lw=0.8)
        ax.set_xticks(m.index.astype(int))
        ax.set_title(name, fontsize=9, color=INK, loc="left")
        _style(ax)
    for ax in axes.flat[len(names):]:
        ax.set_visible(False)
    for ax in axes[:, 0]:
        ax.set_ylabel("% per year", fontsize=7, color=MUTED)
    for ax in axes[-1]:
        ax.set_xlabel("decile (1 = lowest signal)", fontsize=7, color=MUTED)
    fig.suptitle(title, x=0.01, ha="left", color=INK, fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(path, dpi=120, bbox_inches="tight")
    plt.close(fig)
