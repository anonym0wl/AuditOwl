#!/usr/bin/env python3
"""Illustrative 3-run Venn of an auditor's finding sets for ONE paper.

A true 10-way Venn is unreadable, so this draws 3 representative runs (the triple
whose mean pairwise Jaccard is closest to the paper's overall mean) to visualise the
shared-core-vs-run-unique structure. It is ILLUSTRATIVE (3 of 10 runs); the rigorous
aggregate is the detection-rate histogram (panel b of fig_robustness_stability).

Output: _robustness/figures/fig_venn_<num>.{png,pdf,svg}
Run:    python _robustness/build_venn.py [paper_number]   (default 1333)
"""
from __future__ import annotations
import sys
from itertools import combinations
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle

RB = Path(__file__).resolve().parent
sys.path.insert(0, str(RB))
import build_robustness_figure as B  # noqa: E402 (style + helpers)
import analyze as A  # noqa: E402

TEAL, AMB, PURP, INK, MUTE = B.TEAL, B.AMB, B.PURP, B.INK, B.MUTE
MERGED = B.MERGED
PAPERS = B.PAPERS


def run_sets(paper):
    runs = A.load_runs(RB / paper); R = len(runs)
    fr = {}
    for ri, run in enumerate(runs):
        for idx in range(len(run["findings"])):
            fr[f"r{ri+1:02d}#{idx}"] = ri
    sets = [set() for _ in range(R)]
    for ci, c in enumerate(MERGED[paper]):
        for f in c["fids"]:
            if f in fr:
                sets[fr[f]].add(ci)
    return sets


def jac(a, b):
    u = len(a | b); return len(a & b) / u if u else 1.0


def representative_triple(sets):
    R = len(sets)
    mean_j = np.mean([jac(sets[i], sets[j]) for i, j in combinations(range(R), 2)])
    best = None
    for tri in combinations(range(R), 3):
        mj = np.mean([jac(sets[a], sets[b]) for a, b in combinations(tri, 2)])
        if best is None or abs(mj - mean_j) < best[0]:
            best = (abs(mj - mean_j), tri, mj)
    return best[1], mean_j, best[2]


def main():
    num = sys.argv[1] if len(sys.argv) > 1 else "1333"
    paper = next(p for p in PAPERS if p.startswith(num + "_"))
    sets = run_sets(paper)
    tri, mean_j, mj = representative_triple(sets)
    Aset, Bset, Cset = (sets[t] for t in tri)
    rA, rB, rC = (f"run {t+1:02d}" for t in tri)
    reg = {
        "A": len(Aset - Bset - Cset), "B": len(Bset - Aset - Cset), "C": len(Cset - Aset - Bset),
        "AB": len((Aset & Bset) - Cset), "AC": len((Aset & Cset) - Bset), "BC": len((Bset & Cset) - Aset),
        "ABC": len(Aset & Bset & Cset),
    }

    fig, ax = plt.subplots(figsize=(6.4, 6.0))
    r = 0.62
    cA, cB, cC = (-0.34, 0.22), (0.34, 0.22), (0.0, -0.38)
    for c, col in ((cA, TEAL), (cB, AMB), (cC, PURP)):
        ax.add_patch(Circle(c, r, facecolor=col, edgecolor=col, alpha=0.32, lw=1.5, zorder=2))
        ax.add_patch(Circle(c, r, facecolor="none", edgecolor=col, lw=2.0, zorder=3))
    pos = {"A": (-0.66, 0.52), "B": (0.66, 0.52), "C": (0.0, -0.80),
           "AB": (0.0, 0.56), "AC": (-0.46, -0.30), "BC": (0.46, -0.30), "ABC": (0.0, -0.02)}
    for k, (x, y) in pos.items():
        big = (k == "ABC")
        ax.text(x, y, str(reg[k]), ha="center", va="center",
                fontsize=20 if big else 14, weight="bold",
                color="#2f6b2f" if big else INK, zorder=5)
    ax.text(cA[0] - 0.18, cA[1] + r + 0.06, rA, ha="center", color=TEAL, fontsize=12, weight="bold")
    ax.text(cB[0] + 0.18, cB[1] + r + 0.06, rB, ha="center", color="#9c6f12", fontsize=12, weight="bold")
    ax.text(cC[0], cC[1] - r - 0.10, rC, ha="center", color=PURP, fontsize=12, weight="bold")

    total = sum(reg.values())
    ax.text(0, 1.30, f"{num}: three representative audit runs of the same paper",
            ha="center", fontsize=12.5, weight="bold", color=INK)
    ax.text(0, 1.14, f"{total} distinct issues across the 3 runs  ·  {reg['ABC']} found by all three (shared core)  ·  "
            f"{reg['A'] + reg['B'] + reg['C']} found by only one",
            ha="center", fontsize=9.5, color=MUTE)
    ax.text(0, -1.28, "Illustrative: 3 of the 10 runs (the triple whose mean pairwise Jaccard ≈ the paper's overall mean, "
            f"{mean_j:.2f}).\nThe rigorous aggregate over all 10 runs is the detection-rate histogram.",
            ha="center", fontsize=8, color=MUTE, style="italic")
    ax.set_xlim(-1.25, 1.25); ax.set_ylim(-1.45, 1.45); ax.set_aspect("equal"); ax.axis("off")

    FIGS = RB / "figures"
    for n in (f"fig_venn_{num}.png",):
        fig.savefig(FIGS / n, bbox_inches="tight"); fig.savefig(FIGS / n.replace(".png", ".pdf"), bbox_inches="tight"); fig.savefig(FIGS / n.replace(".png", ".svg"), bbox_inches="tight")
    plt.close(fig)
    print(f"wrote figures/fig_venn_{num}.{{png,pdf,svg}}  | runs {[t+1 for t in tri]}  regions {reg}")


if __name__ == "__main__":
    main()
