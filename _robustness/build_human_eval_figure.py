#!/usr/bin/env python3
"""Human-eval figure — grouped bars of the human verdict, one bar per paper.

Reads data/human_eval_findings.csv (from aggregate_human_eval.py) and draws a
single grouped bar chart: five verdict categories on the x-axis, and within
each category one bar per paper.

    correct                       (correct & relevant)
    correct but not relevant
    correct but severity overstated   (correct, severity miscalibrated high)
    unsure
    false

Output: figures/fig_human_eval.{png,pdf,svg}
Run:    python _robustness/build_human_eval_figure.py   (run aggregate first)
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
PALETTE = ["#3B7A9E", "#E1A33C", "#5FAE6E", "#B64342", "#7E5AA2"]   # one colour per paper (teal, amber, green, vermilion, violet)

# severity is shown inside each bar: low-severity findings as a lighter cap, the
# rest (medium + high) in the paper's full colour.
LOW_LIGHTEN = 0.68           # blend-toward-white factor for the low-severity segment (lighter)


def shade(hex_color: str, f: float) -> str:
    """Blend a hex colour toward white by factor f in [0,1] (0 = unchanged)."""
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    r, g, b = (round(c + (255 - c) * f) for c in (r, g, b))
    return f"#{r:02X}{g:02X}{b:02X}"

# verdict keys (CSV) in the requested display order, with x-axis labels.
# Categories with zero findings across all included papers are dropped.
# 'unsure' is omitted from the bars (a single finding) and noted in the caption instead.
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
    papers = sorted({r["paper"] for r in rows})            # e.g. ['1333', '1829', '2657']
    colors = {p: PALETTE[i % len(PALETTE)] for i, p in enumerate(papers)}
    n = {p: sum(1 for r in rows if r["paper"] == p) for p in papers}

    # counts[paper][verdict][group], group = 'low' severity vs 'rest' (medium + high)
    counts = {p: {k: {"rest": 0, "low": 0} for k in ORDER} for p in papers}
    for r in rows:
        if r["verdict"] in counts[r["paper"]]:
            grp = "low" if r["severity"] == "low" else "rest"
            counts[r["paper"]][r["verdict"]][grp] += 1

    def tot(p, k):
        return counts[p][k]["rest"] + counts[p][k]["low"]

    # keep only verdict categories that occur at least once (drops empty 'unsure' etc.)
    cats = [k for k in ORDER if sum(tot(p, k) for p in papers) > 0]
    x = np.arange(len(cats))
    bw = 0.8 / len(papers)                                 # group spans 0.8 of the unit, leaving a gap
    fig, ax = plt.subplots(figsize=(8.2, 4.6))
    fig.subplots_adjust(bottom=0.2, top=0.9, left=0.1, right=0.97)

    ax.set_xlim(-0.5, len(cats) - 0.5)                       # alternate shaded lanes separate the categories
    for c in range(1, len(cats), 2):
        ax.axvspan(c - 0.5, c + 0.5, color="#F4F1EC", zorder=0)

    for i, p in enumerate(papers):
        off = (i - (len(papers) - 1) / 2) * bw
        rest = np.array([100.0 * counts[p][k]["rest"] / n[p] for k in cats])   # medium + high
        low = np.array([100.0 * counts[p][k]["low"] / n[p] for k in cats])     # low severity
        ax.bar(x + off, rest, width=bw, color=colors[p], edgecolor="white",
               linewidth=1.2, zorder=3)
        ax.bar(x + off, low, width=bw, bottom=rest, color=shade(colors[p], LOW_LIGHTEN),
               edgecolor="white", linewidth=1.2, zorder=3)
        for xi, t in zip(x + off, rest + low):
            if t:
                ax.text(xi, t + 1.2, f"{t:.0f}%", ha="center", va="bottom",
                        fontsize=9.5, fontweight="bold", color=colors[p])

    ax.set_xticks(x)
    ax.set_xticklabels([LABEL[k] for k in cats], fontsize=9.5)
    ax.set_ylabel("Share of paper's findings (%)")
    ax.set_ylim(0, 100)                                       # full 0-100% scale, 100% at top
    ax.set_yticks(range(0, 101, 20))
    ax.set_title("human verdict on auditor findings (% of each paper's findings)", loc="left")
    paper_h = [Patch(facecolor=colors[p], edgecolor="white", label=f"#{p}  (n={n[p]})") for p in papers]
    sev_h = [Patch(facecolor="#5A5A5A", edgecolor="white", label="Medium / high"),
             Patch(facecolor=shade("#5A5A5A", LOW_LIGHTEN), edgecolor="white", label="Low (lighter)")]
    leg1 = ax.legend(handles=paper_h, loc="upper right", title="Paper (hue)",
                     title_fontsize=9, alignment="left")
    ax.add_artist(leg1)
    ax.legend(handles=sev_h, loc="upper right", bbox_to_anchor=(1.0, 0.52),
              title="Severity (shade)", title_fontsize=9, alignment="left")
    ax.tick_params(axis="x", length=0)

    stem = "fig_human_eval"
    for ext in ("png", "pdf", "svg"):
        fig.savefig(FIGS / f"{stem}.{ext}")
    plt.close(fig)
    print(f"wrote figures/{stem}.{{png,pdf,svg}}")


if __name__ == "__main__":
    main()
