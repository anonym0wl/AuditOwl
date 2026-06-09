"""Checks the repo for any implementation of the unsupervised CSM / Improved Contrast
Score Margin epoch-selection method (Appendix B.6). Supports finding: csm-epoch-selection-missing.
Read-only; greps source files only.
"""
import os, re

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "code", "ZhongLIFR__TCCM-NIPS"))
patterns = [r"\bCSM\b", r"contrast.?score", r"score.?margin", r"\bmu_O\b", r"select.?epoch",
            r"epoch.?select", r"candidate.?epoch", r"T\(f\)", r"unsupervised.*select"]
rx = re.compile("|".join(patterns), re.IGNORECASE)

hits = []
for root, _, files in os.walk(REPO):
    if ".git" in root:
        continue
    for fn in files:
        if not (fn.endswith(".py") or fn.endswith(".sh")):
            continue
        p = os.path.join(root, fn)
        try:
            with open(p, encoding="utf-8", errors="ignore") as f:
                for ln, line in enumerate(f, 1):
                    if rx.search(line):
                        hits.append((os.path.relpath(p, REPO), ln, line.strip()))
        except Exception as e:
            print("skip", p, e)

print(f"CSM/epoch-selection pattern hits: {len(hits)}")
for h in hits:
    print(" ", h)

# Also confirm epochs are simply hardcoded in functions.py
fpath = os.path.join(REPO, "FMAD", "functions.py")
with open(fpath) as f:
    src = f.read()
print("\ndetermine_FMAD_hyperparameters present:", "def determine_FMAD_hyperparameters" in src)
print("epoch_size hardcoded count (elif/if branches):", src.count("epoch_size ="))

out = os.path.join(os.path.dirname(__file__), "out", "csm_absent.txt")
with open(out, "w") as f:
    f.write(f"csm_pattern_hits={len(hits)}\n")
    f.write(f"hits={hits}\n")
    f.write(f"determine_FMAD_hyperparameters_present={'def determine_FMAD_hyperparameters' in src}\n")
    f.write(f"hardcoded_epoch_branches={src.count('epoch_size =')}\n")
print("wrote", out)
