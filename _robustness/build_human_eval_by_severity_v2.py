#!/usr/bin/env python3
"""Human-eval by severity, v2: medium+high joined into one panel vs low.

A two-panel variant of build_human_eval_by_severity.py. Instead of three panels
(high / medium / low), medium and high are JOINED into a single "medium & high"
panel; the "low" panel sits below on its own. Plain grouped bars per paper.

Same conventions as the 3-panel version: verdict categories on x, one bar per
paper, COUNTS on y (thin per-cell n make within-stratum % misleading), 'unsure'
omitted from the bars but still counted in each panel's n.

Output: figures/fig_human_eval_by_severity_v2.{png,pdf,svg}
Run:    python _robustness/build_human_eval_by_severity_v2.py   (run aggregate first)
"""
from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt

RB = Path(__file__).resolve().parent
DATA = RB / "data"
FIGS = RB / "figures"
FIGS.mkdir(parents=True, exist_ok=True)

# ---- shared style (matches build_human_eval_by_severity.py) ----
_avail = {f.name for f in fm.fontManager.ttflist}
_FONT = next((f for f in ("Arial", "Helvetica", "Liberation Sans", "DejaVu Sans") if f in _avail), "sans-serif")
INK, MUTE = "#333333", "#767676"
plt.rcParams.update({
    "font.family": "sans-serif", "font.sans-serif": [_FONT, "DejaVu Sans", "Liberation Sans"],
    "font.size": 11, "text.color": INK, "axes.labelcolor": INK, "xtick.color": INK, "ytick.color": INK,
    "axes.titlesize": 11.5, "axes.titleweight": "bold", "axes.titlecolor": INK, "axes.titlepad": 6,
    "axes.edgecolor": "#4D4D4D", "axes.linewidth": 1.6,
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": False,
    "xtick.major.width": 1.3, "ytick.major.width": 1.3,
    "figure.dpi": 300, "savefig.dpi": 300, "savefig.bbox": "tight",
    "savefig.facecolor": "white", "figure.facecolor": "white",
    "legend.frameon": False, "legend.fontsize": 9.5,
    "svg.fonttype": "none", "pdf.fonttype": 42, "ps.fonttype": 42,
})
PALETTE = ["#3B7A9E", "#E1A33C", "#5FAE6E", "#B64342", "#7E5AA2"]   # teal, amber, green, vermilion, violet

# 'unsure' omitted from the bars (single finding); per-panel n still counts it.
ORDER = ["correct_relevant", "correct_not_relevant", "correct_wrong_severity", "false"]
LABEL = {
    "correct_relevant": "correct &\nrelevant",
    "correct_not_relevant": "correct but\nnot relevant",
    "correct_wrong_severity": "correct but\nseverity overstated",
    "false": "false",
}
SEVS = ["high", "medium", "low"]
# panels: (title, severities folded into this panel); medium + high joined.
PANELS = [("medium & high", ["high", "medium"]), ("low", ["low"])]
GROUP_OF = {"high": "medium & high", "medium": "medium & high", "low": "low"}


def load() -> list[dict]:
    with (DATA / "human_eval_findings.csv").open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def main():
    rows = load()
    papers = sorted({r["paper"] for r in rows})
    colors = {p: PALETTE[i % len(PALETTE)] for i, p in enumerate(papers)}

    # counts[paper][verdict][severity]; n_grp = true panel size (incl. omitted 'unsure')
    counts = {p: {k: {s: 0 for s in SEVS} for k in ORDER} for p in papers}
    n_grp = {title: 0 for title, _ in PANELS}
    for r in rows:
        s, p, v = r["severity"], r["paper"], r["verdict"]
        if s in SEVS:
            n_grp[GROUP_OF[s]] += 1
            if v in counts[p]:
                counts[p][v][s] += 1

    cats = [k for k in ORDER if sum(counts[p][k][s] for p in papers for s in SEVS) > 0]
    x = np.arange(len(cats))
    bw = 0.8 / len(papers)
    ymax = max(sum(counts[p][k][s] for s in sevs) for _, sevs in PANELS for p in papers for k in cats)

    fig, axes = plt.subplots(len(PANELS), 1, figsize=(8.6, 7.6))
    fig.subplots_adjust(left=0.09, right=0.97, top=0.9, bottom=0.09, hspace=0.5)

    for ax, (title, sevs) in zip(axes, PANELS):
        ax.set_xlim(-0.5, len(cats) - 0.5)                   # alternate shaded lanes separate the categories
        for c in range(1, len(cats), 2):
            ax.axvspan(c - 0.5, c + 0.5, color="#F4F1EC", zorder=0)
        for i, p in enumerate(papers):
            off = (i - (len(papers) - 1) / 2) * bw
            vals = np.array([sum(counts[p][k][s] for s in sevs) for k in cats])
            ax.bar(x + off, vals, width=bw, color=colors[p], edgecolor="white",
                   linewidth=1.1, zorder=3, label=(f"#{p}" if ax is axes[0] else None))
            for xi, t in zip(x + off, vals):
                if t:
                    ax.text(xi, t + ymax * 0.02, str(int(t)), ha="center", va="bottom",
                            fontsize=8.5, fontweight="bold", color=colors[p])
        ax.set_ylim(0, ymax + max(1.0, ymax * 0.16))
        ax.set_yticks(range(0, ymax + 1, max(1, ymax // 4)))
        ax.set_ylabel("Findings")
        ax.set_title(f"{title} severity  (n={n_grp[title]})", loc="left")
        ax.set_xticks(x)
        ax.set_xticklabels([LABEL[k] for k in cats], fontsize=9.5)
        ax.tick_params(axis="x", length=0, labelbottom=True)

    fig.suptitle("human verdict on auditor findings — medium & high vs low",
                 x=0.09, ha="left", fontsize=12.5, fontweight="bold")
    axes[0].legend(loc="upper right", ncol=1, title="Paper", title_fontsize=9, alignment="left")

    stem = "fig_human_eval_by_severity_v2"
    for ext in ("png", "pdf", "svg"):
        fig.savefig(FIGS / f"{stem}.{ext}")
    plt.close(fig)
    print(f"wrote figures/{stem}.{{png,pdf,svg}}  ·  "
          + " ".join(f"{t}={n_grp[t]}" for t, _ in PANELS))


if __name__ == "__main__":
    main()
