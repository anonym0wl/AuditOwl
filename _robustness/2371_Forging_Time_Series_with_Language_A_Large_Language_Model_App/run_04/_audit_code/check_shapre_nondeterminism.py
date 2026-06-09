"""Check (supports shapre-unseeded-nondeterministic): calculate_shapelet_recons_err
uses unseeded np.random (S/A/Offsets init in USIDL + np.random.permutation in
update_A_par + A_rand_init/Offsets_test in the caller). run_TSG_evaluation.py never
calls set_seed, so the SHAP-RE column is non-deterministic. We call the *actual repo
function* on identical inputs multiple times (no seeding in between, mirroring the
entry point) and record the spread. Read-only; writes a CSV under out/."""
import os
import sys
import numpy as np

HERE = os.path.dirname(__file__)
REPO = os.path.abspath(os.path.join(HERE, "..", "code", "SDForger__neurips_supplemental"))
sys.path.insert(0, REPO)

from utils.evaluation.shapelet_based_measures import calculate_shapelet_recons_err

OUT = os.path.join(HERE, "out")
os.makedirs(OUT, exist_ok=True)

# Build fixed univariate-shaped inputs: (n, length, 1) -- the function reshapes to
# (n, length) so the 3rd dim must be 1, matching the TSG (univariate/multisample) path.
base = np.random.RandomState(123)
n_ori, length = 30, 80
orig = base.rand(n_ori, length, 1)
gen = base.rand(40, length, 1)

# IMPORTANT: do NOT re-seed between calls -- mirror run_TSG_evaluation.py, which sets
# no seed at all. Use a small maxIter implicitly via the function defaults.
vals = []
for rep in range(5):
    v = calculate_shapelet_recons_err(orig.copy(), gen.copy())
    vals.append(float(v))

vals = np.array(vals)
rel_spread = (vals.max() - vals.min()) / (abs(vals.mean()) + 1e-12)

import csv
with open(os.path.join(OUT, "shapre_nondeterminism.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["rep", "shap_re"])
    for i, v in enumerate(vals):
        w.writerow([i, round(v, 6)])
    w.writerow(["min", round(float(vals.min()), 6)])
    w.writerow(["max", round(float(vals.max()), 6)])
    w.writerow(["relative_spread", round(float(rel_spread), 6)])

print("SHAP-RE across 5 unseeded repeats:", [round(v, 4) for v in vals])
print("relative_spread (max-min)/mean:", round(float(rel_spread), 4))
