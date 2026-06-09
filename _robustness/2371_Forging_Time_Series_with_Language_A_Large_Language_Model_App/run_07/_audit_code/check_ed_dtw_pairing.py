"""Checks how calculate_ed / calculate_dtw pair original vs generated samples
(supports finding: ed-dtw-index-pairing). It re-implements the exact loop logic
of utils/evaluation/distance_based_measures.py and shows that (a) only
min(n_orig) samples are used, ignoring the rest of the 100 generated, and
(b) the pairing is index-based, so a random permutation of the generated
samples changes the ED/DTW value substantially -- i.e. the metric depends on
the arbitrary order of the generated set, which has no correspondence to the
originals."""
import numpy as np
import os

rng = np.random.default_rng(0)

# Paper protocol (Appendix C.2): I=30 training instances, generate 100 synthetic.
N_ORIG = 30          # original/train windows
N_GEN = 100          # generated samples (min=max=100 in config.yaml)
L = 250              # window length
C = 1                # channels (univariate)

# Build independent original and generated sets (no per-sample correspondence).
orig = rng.standard_normal((N_ORIG, L, C))
gen = rng.standard_normal((N_GEN, L, C))


def calculate_ed(ori_data, gen_data):
    # verbatim logic from distance_based_measures.py:13-26
    n_samples = ori_data.shape[0]
    n_series = ori_data.shape[2]
    distance_eu = []
    for i in range(n_samples):
        total = 0
        for j in range(n_series):
            total += np.linalg.norm(ori_data[i, :, j] - gen_data[i, :, j])
        distance_eu.append(total / n_series)
    return np.array(distance_eu).mean()


# 1) How many generated samples are actually consumed?
n_used = orig.shape[0]
print(f"generated samples available : {gen.shape[0]}")
print(f"generated samples used by ED: {n_used}  (loop runs over ori_data.shape[0])")
print(f"generated samples ignored   : {gen.shape[0]-n_used}")

# 2) Does the metric depend on the (arbitrary) ordering of the generated set?
base = calculate_ed(orig, gen)
perm_vals = []
for s in range(20):
    p = np.random.default_rng(s).permutation(N_GEN)
    perm_vals.append(calculate_ed(orig, gen[p]))
perm_vals = np.array(perm_vals)
print(f"\nED with default order      : {base:.4f}")
print(f"ED over 20 random gen-orders: mean={perm_vals.mean():.4f} "
      f"min={perm_vals.min():.4f} max={perm_vals.max():.4f} std={perm_vals.std():.4f}")
print("If ED were order-invariant (true distribution distance) the std would be ~0.")

os.makedirs(os.path.join(os.path.dirname(__file__), "out"), exist_ok=True)
out = os.path.join(os.path.dirname(__file__), "out", "ed_dtw_pairing.csv")
with open(out, "w") as f:
    f.write("metric,gen_available,gen_used,gen_ignored,ed_default,ed_perm_mean,ed_perm_min,ed_perm_max,ed_perm_std\n")
    f.write(f"ED,{N_GEN},{n_used},{N_GEN-n_used},{base:.4f},{perm_vals.mean():.4f},"
            f"{perm_vals.min():.4f},{perm_vals.max():.4f},{perm_vals.std():.4f}\n")
print(f"\nwrote {out}")
