#!/usr/bin/env python3
"""Explain the auditor's 'missing robustness' using the human-validated findings.

Reads data/human_eval_findings.csv. Each finding carries a detection count =
how many of the 10 audit runs surfaced it. The distribution of that count over
the human-judged findings shows WHY a single audit run is not reproducible:

  * most findings sit in a low-detection tail (surfaced by only 1-3 of 10 runs),
  * and that tail is almost entirely human-confirmed CORRECT (real defects),
  * so a single run recovers only a fraction of the real findings.

The figure is a stacked histogram: x = # of 10 runs that surfaced the finding,
bars stacked by human verdict. Annotations give the per-run recall and the
share of findings in the flaky tail vs the fully-reproducible core.

Output: figures/fig_human_eval_robustness.{png,pdf,svg}
Run:    python _robustness/build_human_eval_robustness.py   (run aggregate first)
"""
from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

RB = Path(__file__).resolve().parent
DATA = RB / "data"
FIGS = RB / "figures"
FIGS.mkdir(parents=True, exist_ok=True)

# ---- shared style (matches build_robustness_figure.py) ----
_avail = {f.name for f in fm.fontManager.ttflist}
_FONT = next((f for f in ("Arial", "Helvetica", "Liberation Sans", "DejaVu Sans") if f in _avail), "sans-serif")
INK, MUTE = "#333333", "#767676"
plt.rcParams.update({
    "font.family": "sans-serif", "font.sans-serif": [_FONT, "DejaVu Sans", "Liberation Sans"],
    "font.size": 11, "text.color": INK, "axes.labelcolor": INK, "xtick.color": INK, "ytick.color": INK,
    "axes.titlesize": 12.5, "axes.titleweight": "bold", "axes.titlecolor": INK, "axes.titlepad": 8,
    "axes.edgecolor": "#4D4D4D", "axes.linewidth": 1.6,
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": False,
    "xtick.major.width": 1.3, "ytick.major.width": 1.3,
    "figure.dpi": 300, "savefig.dpi": 300, "savefig.bbox": "tight",
    "savefig.facecolor": "white", "figure.facecolor": "white",
    "legend.frameon": False, "legend.fontsize": 9.5,
    "svg.fonttype": "none", "pdf.fonttype": 42, "ps.fonttype": 42,
})
VERM, AMB, GRN, TEAL = "#B64342", "#E1A33C", "#5FAE6E", "#3B7A9E"

# verdict stack: correct (bottom) -> false (top); only present ones are drawn
STACK = ["correct_relevant", "correct_not_relevant", "correct_wrong_severity", "unsure", "false"]
COLOR = {"correct_relevant": GRN, "correct_not_relevant": AMB,
         "correct_wrong_severity": TEAL, "unsure": "#9AA6B2", "false": VERM}
LABEL = {"correct_relevant": "Correct", "correct_not_relevant": "Correct, not relevant",
         "correct_wrong_severity": "Correct, severity overstated",
         "unsure": "Unsure", "false": "False"}


def load() -> list[dict]:
    with (DATA / "human_eval_findings.csv").open(encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    for r in rows:
        r["detection"] = int(r["detection"])
        r["detection_total"] = int(r["detection_total"])
    return rows


def main():
    rows = load()
    R = max(r["detection_total"] for r in rows)        # 10 runs
    n = len(rows)
    npapers = len({r["paper"] for r in rows})
    bins = np.arange(1, R + 1)

    # counts[verdict][detection]
    present = [v for v in STACK if any(r["verdict"] == v for r in rows)]
    counts = {v: np.zeros(R, dtype=int) for v in present}
    for r in rows:
        if r["verdict"] in counts:
            counts[r["verdict"]][r["detection"] - 1] += 1

    # headline robustness stats, straight from the data
    det = np.array([r["detection"] for r in rows])
    per_run_recall = float(np.mean(det / R))           # E[fraction recovered by 1 run]
    le3 = int((det <= 3).sum())
    full = int((det == R).sum())
    correct_in_tail = sum(1 for r in rows if r["detection"] <= 3 and r["is_correct"] == "1")

    fig, ax = plt.subplots(figsize=(8.8, 4.9))
    fig.subplots_adjust(bottom=0.15, top=0.9, left=0.1, right=0.97)

    # shade the flaky tail (<= 3 of 10 runs)
    ax.axvspan(0.4, 3.5, color="#F4F1EC", zorder=0)

    bottom = np.zeros(R)
    for v in present:
        ax.bar(bins, counts[v], width=0.82, bottom=bottom, color=COLOR[v],
               edgecolor="white", linewidth=1.0, zorder=3, label=LABEL[v])
        bottom += counts[v]

    totals = bottom.astype(int)
    for x, t in zip(bins, totals):
        if t:
            ax.text(x, t + 0.12, str(t), ha="center", va="bottom", fontsize=9, color=MUTE)

    ymax = int(totals.max())
    ax.set_xticks(bins)
    ax.set_xlim(0.4, R + 0.6)
    ax.set_ylim(0, ymax + 1.6)
    ax.set_xlabel("Audit runs (of 10) that surfaced the finding  —  detection / reproducibility")
    ax.set_ylabel("Number of distinct findings")
    ax.set_title("Why one audit run misses most real findings", loc="left")

    # bracket label over the flaky tail
    ax.text(2.0, ymax + 1.25, "flaky tail (≤3 runs)", ha="center", va="center", fontsize=9,
            color=MUTE, style="italic")
    ax.annotate("", xy=(0.6, ymax + 0.95), xytext=(3.4, ymax + 0.95),
                arrowprops=dict(arrowstyle="-", color=MUTE, lw=1.0))

    # headline stat box
    txt = (f"a single run recovers only ~{per_run_recall*100:.0f}% of the {n} findings\n"
           f"{le3}/{n} ({le3/n*100:.0f}%) surfaced by ≤3 of 10 runs  "
           f"({correct_in_tail} of those human-confirmed correct)\n"
           f"only {full}/{n} ({full/n*100:.0f}%) surfaced by all 10 runs")
    ax.text(0.975, 0.97, txt, transform=ax.transAxes, ha="right", va="top",
            fontsize=9.2, color=INK,
            bbox=dict(boxstyle="round,pad=0.5", fc="white", ec="#C7CED6", lw=1.2))

    ax.legend(loc="upper right", bbox_to_anchor=(0.975, 0.66), title=f"Human verdict ({npapers} papers, n={n})",
              title_fontsize=8.5)

    stem = "fig_human_eval_robustness"
    for ext in ("png", "pdf", "svg"):
        fig.savefig(FIGS / f"{stem}.{ext}")
    plt.close(fig)
    print(f"wrote figures/{stem}.{{png,pdf,svg}}")
    print(f"  per-run recall ~{per_run_recall*100:.0f}% · ≤3 runs: {le3}/{n} · all 10: {full}/{n}")


if __name__ == "__main__":
    main()
