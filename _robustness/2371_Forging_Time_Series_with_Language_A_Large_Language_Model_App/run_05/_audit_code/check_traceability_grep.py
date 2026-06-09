"""Deterministic grep-style traceability checks over the supplemental .py files.
Confirms which headline computations are ABSENT from the repo:
 - normalized averages / average rank (Tables 1 & 2)
 - kNN classifier accuracy 0.81 (Figure 2)
 - any baseline (TimeVAE/TimeVQVAE/RTSGAN/SDEGAN/LS4) generation code
Outputs out/traceability_grep.csv."""
import os, re, csv

SUP = os.path.join(os.path.dirname(__file__), "..", "code",
                   "SDForger__neurips_supplemental")

py_files = []
for dp, _, fns in os.walk(SUP):
    for fn in fns:
        if fn.endswith(".py"):
            py_files.append(os.path.join(dp, fn))

def search(patterns):
    hits = []
    for p in py_files:
        try:
            txt = open(p, errors="ignore").read()
        except Exception:
            continue
        for pat in patterns:
            for m in re.finditer(pat, txt, re.I):
                ln = txt[:m.start()].count("\n") + 1
                hits.append(f"{os.path.relpath(p, SUP)}:{ln}:{m.group(0)[:40]}")
    return hits

checks = {
    "rank_or_normalized_avg": [r"rankdata", r"\.rank\(", r"normalized", r"argsort.*rank", r"avg_rank"],
    "knn_classifier_fig2":    [r"KNeighbors", r"\bclassifier\b", r"skfda", r"\baccuracy\b", r"\.score\("],
    "baseline_generation":    [r"TimeVAE", r"TimeVQVAE", r"RTSGAN", r"RtsGAN", r"SdeGAN", r"\bLS4\b"],
}

os.makedirs(os.path.join(os.path.dirname(__file__), "out"), exist_ok=True)
out = os.path.join(os.path.dirname(__file__), "out", "traceability_grep.csv")
with open(out, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["check", "n_hits", "present", "examples"])
    for name, pats in checks.items():
        hits = search(pats)
        row = [name, len(hits), bool(hits), " | ".join(hits[:5])]
        w.writerow(row); print(row)
