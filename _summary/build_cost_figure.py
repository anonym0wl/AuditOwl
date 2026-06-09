#!/usr/bin/env python3
"""Per-paper compute figure: tokens and wall-clock, audit + verification.

Two panels, one bar per paper (sorted by total tokens, descending):
  a. tokens (millions)     bar = audit (base) + verification (stacked on top)
  b. wall-clock (minutes)  bar = audit (base) + verification (stacked on top)

Pure renderer. Reads the shipped, de-identified, per-paper aggregate from
`_summary/data/compute_cost.json` (audit/verify tokens, active wall-minutes, cost,
and has_code per paper, plus totals) and draws the figure. No raw session logs are
needed or shipped: compute_cost.json IS the committed data layer, so the figure
reproduces from a fresh clone with no extra inputs.

Run:     python _summary/build_cost_figure.py
Outputs: _summary/figures/fig_compute_cost.{png,pdf,svg}
"""
from __future__ import annotations
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
FIGS = ROOT / "_summary" / "figures"
DATA = ROOT / "_summary" / "data"

data = json.loads((DATA / "compute_cost.json").read_text())
rows = data["per_paper"]                 # one dict per sampled paper
tot = data["totals"]

n_nocode_total = sum(1 for r in rows if not r["has_code"])
print(f"papers: {len(rows)} ({n_nocode_total} no-code, zeroed)")
print(f"audit tokens {tot['audit_tokens']/1e6:,.0f}M | verify tokens {tot['verify_tokens']/1e6:,.0f}M "
      f"| total {(tot['audit_tokens']+tot['verify_tokens'])/1e6:,.0f}M")

# ---- figure ---------------------------------------------------------------
_avail = {fnt.name for fnt in fm.fontManager.ttflist}
_FONT = next((f for f in ("Arial", "Helvetica", "Liberation Sans", "DejaVu Sans")
              if f in _avail), "sans-serif")
INK, MUTE = "#333333", "#767676"
plt.rcParams.update({
    "font.family": "sans-serif", "font.sans-serif": [_FONT, "DejaVu Sans"],
    "font.size": 14, "text.color": INK, "axes.labelcolor": INK,
    "xtick.color": INK, "ytick.color": INK,
    "axes.titlesize": 14, "axes.titleweight": "bold", "axes.titlecolor": INK,
    "axes.edgecolor": "#4D4D4D", "axes.linewidth": 1.0,
    "xtick.labelsize": 12.5, "ytick.labelsize": 12.5,
    "axes.spines.top": False, "axes.spines.right": False,
    "figure.dpi": 300, "savefig.dpi": 300, "savefig.bbox": "tight",
    "savefig.facecolor": "white", "figure.facecolor": "white",
    "legend.frameon": False, "svg.fonttype": "none",
    "pdf.fonttype": 42, "ps.fonttype": 42,
})
AUDIT_C = "#3775BA"        # sky blue, the audit pass
VERIFY_C = "#E1A33C"       # amber, verification stacked on top

# one shared x-order: by total tokens (audit+verify), descending (lightest right)
order = sorted(range(len(rows)),
               key=lambda i: rows[i]["audit_tokens"] + rows[i]["verify_tokens"],
               reverse=True)
at = np.array([rows[i]["audit_tokens"] for i in order]) / 1e6      # millions
vt = np.array([rows[i]["verify_tokens"] for i in order]) / 1e6
aw = np.array([rows[i]["audit_wall_min"] for i in order])
vw = np.array([rows[i]["verify_wall_min"] for i in order])
x = np.arange(len(order))

# No-code papers are zeroed in the data, so they sort to the trailing end; count
# them from has_code for the "N no code" bracket under the empty region.
n_nocode = sum(1 for i in order if not rows[i]["has_code"])
n_code = len(order) - n_nocode

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9.6, 6.0))
fig.subplots_adjust(left=0.10, right=0.97, top=0.95, bottom=0.10, hspace=0.32)


def panel(ax, base, top, ylabel, unit):
    ax.bar(x, base, width=0.9, color=AUDIT_C, edgecolor="none", label="Audit")
    ax.bar(x, top, bottom=base, width=0.9, color=VERIFY_C, edgecolor="none",
           label="Verification")
    ax.set_xlim(-1, len(order))
    ax.set_ylabel(ylabel, fontsize=16)
    ax.set_xticks([])
    ax.set_ylim(0, (base + top).max() * 1.14)
    mean = (base + top)[:n_code].mean() if n_code else 0      # mean over audited papers
    ax.axhline(mean, color=MUTE, lw=1.0, ls="--", zorder=0)
    ax.text(len(order) - 1, mean, f"mean {mean:,.1f}{unit} ", ha="right",
            va="bottom", fontsize=14, color=MUTE)
    # bracket grouping the zeroed no-code papers at the trailing end
    if n_nocode:
        y0, y1 = ax.get_ylim()
        tick = (y1 - y0) * 0.05
        xl, xr = n_code - 0.5, len(order) - 0.5
        yb = -tick * 1.3
        ax.plot([xl, xl, xr, xr], [yb + tick, yb, yb, yb + tick],
                color=MUTE, lw=1.0, clip_on=False, zorder=5)
        ax.text((xl + xr) / 2, yb - tick * 0.6, f"{n_nocode} no code",
                ha="center", va="top", fontsize=14, color=MUTE)


panel(ax1, at, vt, "Tokens (M)", "M")
panel(ax2, aw, vw, "Time (min)", "m")
ax1.legend(loc="upper right", ncol=2, fontsize=14, handlelength=1.1,
           labelspacing=0.3, columnspacing=1.4)

FIGS.mkdir(parents=True, exist_ok=True)
for ext in ("png", "pdf", "svg"):
    fig.savefig(FIGS / f"fig_compute_cost.{ext}")
plt.close(fig)
print("wrote figures/fig_compute_cost.{png,pdf,svg}")
