"""Small-multiple charts of feature paths around cycle pivots (evaluation.pivot_profiles output)."""
from __future__ import annotations

import numpy as np

INK, MUTED, GRID = "#1f2328", "#6e7781", "#d8dee4"
LOW, HIGH = "#1f77b4", "#d1651b"


def plot_pivot_profiles(prof, path, title, cols: int = 5, labels: dict | None = None):
    """One panel per feature: mean z-score path around swing lows (blue) and highs (orange); x = days from pivot."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    names = list(dict.fromkeys(prof["feature"]))
    rows = int(np.ceil(len(names) / cols))
    fig, axes = plt.subplots(rows, cols, figsize=(3.2 * cols, 2.6 * rows + 0.6), sharex=True, sharey=True,
                             squeeze=False)
    for ax, name in zip(axes.flat, names):
        for kind, c in (("low", LOW), ("high", HIGH)):
            q = prof[(prof["kind"] == kind) & (prof["feature"] == name)]
            ax.plot(q["offset"], q["mean"], color=c, lw=1.5, label="around swing %ss" % kind)
        ax.axvline(0, color=MUTED, lw=0.8)
        ax.axhline(0, color=GRID, lw=0.8)
        ax.set_title((labels or {}).get(name, name), fontsize=9, color=INK, loc="left")
        ax.tick_params(colors=MUTED, labelsize=7)
        ax.spines[["top", "right"]].set_visible(False)
        ax.spines[["left", "bottom"]].set_color(GRID)
    for ax in axes.flat[len(names):]:
        ax.set_visible(False)
    axes.flat[0].legend(fontsize=7, frameon=False, loc="upper left")
    for ax in axes[-1]:
        ax.set_xlabel("days from pivot", fontsize=7, color=MUTED)
    fig.suptitle(title, x=0.01, ha="left", color=INK, fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    fig.savefig(path, dpi=120, bbox_inches="tight")
    plt.close(fig)
