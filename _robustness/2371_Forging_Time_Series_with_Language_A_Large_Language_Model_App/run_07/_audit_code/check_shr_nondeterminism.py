"""Checks that the SHAP-RE (SHR) similarity metric is nondeterministic because
its SIDL dictionary learning + sparse coding are randomly initialized
(np.random.* in shapelet_based_measures.py / utils_shapelet.py) and
sources/run_TSG_evaluation.py never seeds the RNG before calling it.
Supports finding: shr-unseeded-nondeterministic. Runs the *repo's own*
calculate_shapelet_recons_err three times on identical inputs."""
import numpy as np
import sys, os

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "code",
                                    "SDForger__neurips_supplemental"))
sys.path.insert(0, REPO)
from utils.evaluation.shapelet_based_measures import calculate_shapelet_recons_err

np.random.seed(123)  # establish global state once, mirroring a single process run
orig = np.random.standard_normal((30, 60, 1)).astype(np.float64)
gen = np.random.standard_normal((30, 60, 1)).astype(np.float64)

vals = [float(calculate_shapelet_recons_err(orig.copy(), gen.copy())) for _ in range(3)]
all_equal = len({round(v, 4) for v in vals}) == 1
print("SHR on identical inputs, 3 calls:", [round(v, 4) for v in vals])
print("deterministic:", all_equal)

out = os.path.join(os.path.dirname(__file__), "out", "shr_nondeterminism.csv")
os.makedirs(os.path.dirname(out), exist_ok=True)
with open(out, "w") as f:
    f.write("call1,call2,call3,deterministic\n")
    f.write(f"{vals[0]:.4f},{vals[1]:.4f},{vals[2]:.4f},{all_equal}\n")
print("wrote", out)
