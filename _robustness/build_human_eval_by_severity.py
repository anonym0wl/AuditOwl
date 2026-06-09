#!/usr/bin/env python3
"""Human-eval figure, stratified by (auditor-assigned) severity.

Decomposes fig_human_eval into three panels — high / medium / low severity —
each a grouped bar chart of the human verdict, one bar per paper.

NB on the y-axis: per (paper, severity) cells are thin (some papers have only
0-1 findings at a given severity), so a *within-stratum percentage* would be
degenerate (one finding -> 0% or 100%). We therefore plot raw COUNTS here and
keep percentages for the un-stratified fig_human_eval. The severity label is an
LLM-assigned, subjective tag — this view is exploratory, not a headline figure.

Output: figures/fig_human_eval_by_severity.{png,pdf,svg}
Run:    python _robustness/build_human_eval_by_severity.py   (run aggregate first)
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

# ---- shared style (matches build_human_eval_figure.py) ----
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

SEVERITIES = ["high", "medium", "low"]               # panel order (most -> least severe)
# 'unsure' is omitted from the bars (a single finding) and noted in the caption instead;
# per-severity n totals below still include it so panel sizes stay truthful.
ORDER = ["correct_relevant", "correct_not_relevant", "correct_wrong_severity", "false"]
LABEL = {
    "correct_relevant": "correct &\nrelevant",
    "correct_not_relevant": "correct but\nnot relevant",
    "correct_wrong_severity": "correct but\nseverity overstated",
    "unsure": "unsure",
    "false": "false",
}


def load() -> list[dict]:
    with (DATA / "human_eval_findings.csv").open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def main():
    rows = load()
    papers = sorted({r["paper"] for r in rows})
    colors = {p: PALETTE[i % len(PALETTE)] for i, p in enumerate(papers)}
    n_total = {p: sum(1 for r in rows if r["paper"] == p) for p in papers}

    # counts[severity][paper][verdict]
    counts = {s: {p: {k: 0 for k in ORDER} for p in papers} for s in SEVERITIES}
    n_sev = {s: 0 for s in SEVERITIES}
    for r in rows:
        s, p, v = r["severity"], r["paper"], r["verdict"]
        if s in counts:
            n_sev[s] += 1                              # true stratum size (incl. omitted 'unsure')
            if v in counts[s][p]:
                counts[s][p][v] += 1                   # only plotted verdicts get a bar

    # keep verdict categories that occur at least once anywhere (consistent x across panels)
    cats = [k for k in ORDER if any(counts[s][p][k] for s in SEVERITIES for p in papers)]
    x = np.arange(len(cats))
    bw = 0.8 / len(papers)
    ymax = max(counts[s][p][k] for s in SEVERITIES for p in papers for k in cats)

    fig, axes = plt.subplots(len(SEVERITIES), 1, figsize=(8.6, 10.4))
    fig.subplots_adjust(left=0.09, right=0.97, top=0.92, bottom=0.07, hspace=0.55)

    for ax, s in zip(axes, SEVERITIES):
        ax.set_xlim(-0.5, len(cats) - 0.5)                   # alternate shaded lanes separate the categories
        for c in range(1, len(cats), 2):
            ax.axvspan(c - 0.5, c + 0.5, color="#F4F1EC", zorder=0)
        for i, p in enumerate(papers):
            vals = [counts[s][p][k] for k in cats]
            off = (i - (len(papers) - 1) / 2) * bw
            bars = ax.bar(x + off, vals, width=bw, color=colors[p], edgecolor="white",
                          linewidth=1.1, zorder=3, label=f"#{p}  (n={n_total[p]})")
            for b, v in zip(bars, vals):
                if v:
                    ax.text(b.get_x() + b.get_width() / 2, v + ymax * 0.02, str(v),
                            ha="center", va="bottom", fontsize=8.5, fontweight="bold",
                            color=colors[p])
        ax.set_ylim(0, ymax + max(1.0, ymax * 0.16))
        ax.set_yticks(range(0, ymax + 1, max(1, ymax // 4)))
        ax.set_ylabel("Findings")
        ax.set_title(f"{s}-severity  (n={n_sev[s]})", loc="left")
        ax.set_xticks(x)
        ax.set_xticklabels([LABEL[k] for k in cats], fontsize=9.5)
        ax.tick_params(axis="x", length=0, labelbottom=True)

    axes[0].legend(loc="upper right", ncol=1)
    fig.suptitle("human verdict on auditor findings, stratified by severity (counts)",
                 x=0.09, ha="left", fontsize=12.5, fontweight="bold")

    stem = "fig_human_eval_by_severity"
    for ext in ("png", "pdf", "svg"):
        fig.savefig(FIGS / f"{stem}.{ext}")
    plt.close(fig)
    print(f"wrote figures/{stem}.{{png,pdf,svg}}  ·  "
          + " ".join(f"{s}={n_sev[s]}" for s in SEVERITIES))


if __name__ == "__main__":
    main()
