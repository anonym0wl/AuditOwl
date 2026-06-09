"""Deterministic inventory checks for TCCM repo. Supports several findings:
- model index ranges / counts
- dataset counts (paper says 47 datasets, 45 detectors)
- existence of Full_experiments.py referenced by run_knn.sh
- existence of any statistical-test / explanation / epoch-selection code
"""
import os, re, sys
ROOT = os.path.join(os.path.dirname(__file__), "..", "code", "ZhongLIFR__TCCM-NIPS")
ROOT = os.path.abspath(ROOT)

out = open(os.path.join(os.path.dirname(__file__), "out", "inventory.txt"), "w")
def p(*a):
    print(*a); print(*a, file=out)

# Count datasets per split dir
for split in ["small","medium","high_dim","large","contamination"]:
    d = os.path.join(ROOT, "datasets", split)
    n = len([f for f in os.listdir(d) if f.endswith(".npz")]) if os.path.isdir(d) else 0
    p(f"datasets/{split}: {n} npz files")

# total unique datasets across the 4 main splits (paper says 47)
mains = set()
dup = []
for split in ["small","medium","high_dim","large"]:
    d = os.path.join(ROOT, "datasets", split)
    for f in os.listdir(d):
        if f.endswith(".npz"):
            if f in mains: dup.append((split,f))
            mains.add(f)
p(f"TOTAL unique main-split datasets: {len(mains)} (paper claims 47)")
p(f"datasets appearing in >1 split (duplicates): {dup}")

# Full_experiments.py existence (referenced in run_knn.sh)
p("Full_experiments.py exists:", os.path.isfile(os.path.join(ROOT,"Full_experiments.py")))
p("FullExperiments.py exists:", os.path.isfile(os.path.join(ROOT,"FullExperiments.py")))

# grep for stat-test / explanation / epoch-selection / CSM
patterns = {
  "friedman": r"friedman",
  "nemenyi": r"nemenyi",
  "critical_difference/CD": r"critical[_ ]?difference|\bcd[_ ]?diagram",
  "CSM/contrast score margin": r"\bcsm\b|contrast score margin",
  "epoch selection": r"select.*epoch|epoch.*select",
  "Jaccard (explanation)": r"jaccard",
  "ExactMatch (explanation)": r"exact[_ ]?match",
  "explanation/feature contribution": r"feature.contrib|top.?k.*feature|anomalous dimension",
}
pyfiles = []
for dp,_,fs in os.walk(ROOT):
    for f in fs:
        if f.endswith(".py"): pyfiles.append(os.path.join(dp,f))
p(f"\n# .py files scanned: {len(pyfiles)}")
for name,pat in patterns.items():
    hits = []
    rgx = re.compile(pat, re.I)
    for pf in pyfiles:
        try:
            txt = open(pf, errors="ignore").read()
        except: continue
        if rgx.search(txt):
            hits.append(os.path.relpath(pf, ROOT))
    p(f"pattern [{name}]: hits in {hits if hits else 'NONE'}")

out.close()
print("DONE")
