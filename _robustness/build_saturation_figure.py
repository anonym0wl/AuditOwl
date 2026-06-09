#!/usr/bin/env python3
"""Plot of the discovery / saturation table: fraction of distinct candidate findings
recovered when the findings of K independent audit reports are unioned.

Two curves (mean over the 5 papers, exact via 1 - C(R-d,K)/C(R,K)):
  - all distinct candidates (the full union, det>=1)        -> no 'real' assumption (non-circular shape)
  - corroborated only (det>=2, a proxy for genuine defects)  -> climbs faster
Inset bars: expected NEW distinct candidates added by each additional report (full union).

Output: _robustness/figures/fig_saturation.{png,pdf,svg}
Run:    python _robustness/build_saturation_figure.py
"""
from __future__ import annotations
import sys
from math import comb
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

RB = Path(__file__).resolve().parent
sys.path.insert(0, str(RB))
import build_robustness_figure as B  # noqa: E402
import analyze as A  # noqa: E402

TEAL, AMB, GREY, INK, MUTE = B.TEAL, B.AMB, B.GREY, B.INK, B.MUTE
MERGED, PAPERS = B.MERGED, B.PAPERS


def det_counts(paper):
    runs = A.load_runs(RB / paper); R = len(runs)
    fr = {}
    for ri, run in enumerate(runs):
        for idx in range(len(run["findings"])):
            fr[f"r{ri+1:02d}#{idx}"] = ri
    return [len({fr[f] for f in c["fids"] if f in fr}) for c in MERGED[paper]], R


def curve(ds, R):
    return np.array([np.mean([1 - (comb(R - d, K) / comb(R, K) if R - d >= K else 0.0) for d in ds]) for K in range(1, R + 1)])


def main():
    full, corr, sizes = [], [], []
    for p in PAPERS:
        ds, R = det_counts(p)
        full.append(curve(ds, R)); corr.append(curve([d for d in ds if d >= 2], R)); sizes.append(len(ds))
    full = np.array(full).mean(0); corr = np.array(corr).mean(0)
    msize = float(np.mean(sizes)); Kx = np.arange(1, 11)

    fig, ax = plt.subplots(figsize=(7.4, 5.2))
    fig.subplots_adjust(left=0.10, right=0.97, top=0.93, bottom=0.12)
    ax.plot(Kx, corr, color=AMB, lw=2.0, marker="s", ms=4.5, zorder=3, label="Corroborated only (≥2 reports agree)")
    ax.plot(Kx, full, color=TEAL, lw=2.6, marker="o", ms=5, zorder=4, label="All distinct candidates (full union)")
    for K in (1, 3, 5):
        ax.annotate(f"{100*full[K-1]:.0f}%", xy=(K, full[K - 1]), xytext=(K + 0.12, full[K - 1] - 0.085),
                    fontsize=10, color=TEAL, weight="bold")
    ax.set_xticks(Kx); ax.set_xlim(0.7, 10.3); ax.set_ylim(0, 1.03)
    ax.set_xlabel("Number of audit reports unioned (K)")
    ax.set_ylabel("Fraction of distinct candidate findings recovered")
    ax.legend(loc="lower right", fontsize=9.5)

    # inset: new distinct candidates added by each additional report (full union)
    ins = ax.inset_axes([0.56, 0.18, 0.40, 0.34])
    cum = full * msize
    marg = np.diff(np.concatenate([[0], cum]))
    ins.bar(Kx, marg, width=0.7, color=GREY, edgecolor="white", zorder=3)
    for k in (0, 1, 2):
        ins.text(k + 1, marg[k] + 0.1, f"{marg[k]:.1f}", ha="center", fontsize=7.5, color=INK)
    ins.set_xticks([1, 3, 5, 7, 10]); ins.set_ylim(0, marg.max() * 1.2)
    ins.set_xlabel("Kth report", fontsize=7.5); ins.set_ylabel("New found", fontsize=7.5)
    ins.tick_params(labelsize=7)
    ins.set_title("diminishing returns", fontsize=8, loc="left", color=MUTE)

    FIGS = RB / "figures"
    for n in ("fig_saturation.png",):
        fig.savefig(FIGS / n); fig.savefig(FIGS / n.replace(".png", ".pdf")); fig.savefig(FIGS / n.replace(".png", ".svg"))
    plt.close(fig)
    print("wrote figures/fig_saturation.{png,pdf,svg}")
    print("  full-union recall  K=1/3/5/10: %.0f/%.0f/%.0f/%.0f%%" % tuple(100 * full[[0, 2, 4, 9]]))
    print("  corroborated      K=1/3/5/10: %.0f/%.0f/%.0f/%.0f%%" % tuple(100 * corr[[0, 2, 4, 9]]))


if __name__ == "__main__":
    main()
