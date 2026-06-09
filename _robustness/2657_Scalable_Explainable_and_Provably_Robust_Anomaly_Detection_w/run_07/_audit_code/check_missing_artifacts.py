"""Deterministically checks which paper-described procedures have NO implementing code in the repo.

Supports findings: missing-csm-epoch-selection, missing-explainability-code,
missing-statistical-tests. Greps the repo for the keywords each procedure would need.
Read-only. Output -> out/missing_artifacts.csv
"""
import os, re, csv, glob

REPO = os.path.join(os.path.dirname(__file__), "..", "code", "ZhongLIFR__TCCM-NIPS")
REPO = os.path.abspath(REPO)

py_files = glob.glob(os.path.join(REPO, "**", "*.py"), recursive=True)

def grep(patterns):
    """Return list of (file, lineno, line) where any regex in `patterns` (case-insensitive) matches."""
    hits = []
    rgx = [re.compile(p, re.I) for p in patterns]
    for f in py_files:
        with open(f, "r", errors="replace") as fh:
            for i, line in enumerate(fh, 1):
                if any(r.search(line) for r in rgx):
                    hits.append((os.path.relpath(f, REPO), i, line.strip()))
    return hits

checks = {
    # CSM / unsupervised epoch selection (paper App. B.6): margin criterion T(f), search over candidate epochs
    "csm_epoch_selection": ["contrast score", "score margin", r"\bCSM\b",
                            "select.*epoch", "epoch.*select", "candidate epoch",
                            "internal evaluation", "loss curve", "convergence threshold"],
    # Explainability MNIST (Fig 4) + synthetic attribution Table 3 (ExactMatch / Jaccard)
    "explainability_attribution": ["jaccard", "exact.?match", "\\bmnist\\b.*train|train.*\\bmnist\\b",
                                   "importance", "attribution", "feature.?contribution", "top.?k.*feature"],
    # Friedman / Nemenyi critical-difference (Fig 21-22, App D.5)
    "statistical_tests": ["friedman", "nemenyi", "critical.?difference", "posthoc", "scikit_posthocs", "wilcoxon"],
}

rows = []
for name, pats in checks.items():
    hits = grep(pats)
    # filter out incidental dataset-name matches (e.g. '24_mnist' in a dataset list / hyperparam table)
    real = [h for h in hits if not re.search(r"_mnist|'.*mnist.*'|\"24_mnist\"|24_mnist", h[2])]
    rows.append({
        "procedure": name,
        "n_keyword_hits": len(hits),
        "n_hits_after_filtering_dataset_names": len(real),
        "implementing_code_present": "YES" if real else "NO",
        "example_hits": " | ".join(f"{f}:{ln}:{txt[:60]}" for f, ln, txt in real[:3]),
    })

out = os.path.join(os.path.dirname(__file__), "out", "missing_artifacts.csv")
with open(out, "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)

for r in rows:
    print(r)
print("Total .py files scanned:", len(py_files))
print("Wrote", out)
