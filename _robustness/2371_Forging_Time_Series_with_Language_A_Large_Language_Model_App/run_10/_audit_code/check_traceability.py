"""Deterministic traceability checks: baseline code presence, multi-dataset driver,
Figure-2 kNN accuracy code, channel-averaging in TTM metric.
Supports findings: baselines-not-in-repo, no-multidataset-driver,
fig2-knn-accuracy-missing, ttm-metric-averages-all-channels."""
import os, re, glob

ROOT = os.path.join(os.path.dirname(__file__), "..", "code", "SDForger__neurips_supplemental")
pyfiles = glob.glob(os.path.join(ROOT, "**", "*.py"), recursive=True)
nbfiles = glob.glob(os.path.join(ROOT, "**", "*.ipynb"), recursive=True)
alltext = ""
for f in pyfiles:
    alltext += open(f, errors="ignore").read() + "\n"

# 1) baseline implementations
baselines = ["timevae", "timevqvae", "rtsgan", "sdegan", r"\bls4\b", "cosci"]
print("=== Baseline implementation references in *.py ===")
for b in baselines:
    n = len(re.findall(b, alltext, re.I))
    print(f"  {b}: {n} match(es)")

# 2) driver looping over datasets / a list of >1 dataset
print("\n=== Multi-dataset driver ===")
loop_hits = re.findall(r"for .*data_name|datasets\s*=\s*\[", alltext)
print(f"  loop-over-datasets patterns found: {len(loop_hits)} -> {loop_hits[:3]}")

# 3) Figure-2 kNN accuracy in notebook
print("\n=== Figure-2 kNN classifier (acc 0.81) ===")
import json
hit = False
for nf in nbfiles:
    nb = json.load(open(nf))
    txt = "\n".join("".join(c.get("source", [])) for c in nb["cells"])
    if re.search(r"KNeighbor|accuracy_score|0\.81|scikit-fda|skfda", txt, re.I):
        hit = True
print(f"  kNN/accuracy code in notebooks: {hit}")
print(f"  scikit-fda referenced anywhere in py: {bool(re.search('skfda|scikit-fda', alltext, re.I))}")

# 4) TTM metric averages over all channels (target+controls)
ttm = open(os.path.join(ROOT, "utils", "evaluation", "utils_ttm.py")).read()
print("\n=== TTM metric channel loop ===")
m = re.search(r"for channel in range\(0, pred_val\.shape\[2\]\)", ttm)
print(f"  loops over ALL pred_val channels: {bool(m)}")
print(f"  avg_rmse = np.mean(rmse_list) over all channels: {bool(re.search(r'avg_rmse = np.mean.rmse_list.', ttm))}")
