"""Checks how calculate_ed / calculate_dtw pair real vs synthetic samples.
Supports finding: ed-dtw-index-pairing.
Read-only: imports the repo's own distance functions and probes their behaviour
with controlled inputs (no repo files modified)."""
import os, sys
import numpy as np

# dtaidistance (needed by the repo module's DTW import) is not installed in this
# sandbox, so we cannot import distance_based_measures directly. We instead copy
# calculate_ed VERBATIM from
#   code/SDForger__neurips_supplemental/utils/evaluation/distance_based_measures.py:13-26
# (only the ED function is needed; DTW shares the identical index-pairing loop).
def calculate_ed(ori_data, gen_data):
    n_samples = ori_data.shape[0]
    n_series = ori_data.shape[2]
    distance_eu = []
    for i in range(n_samples):
        total_distance_eu = 0
        for j in range(n_series):
            distance = np.linalg.norm(ori_data[i, :, j] - gen_data[i, :, j])
            total_distance_eu += distance
        distance_eu.append(total_distance_eu / n_series)
    distance_eu = np.array(distance_eu)
    average_distance_eu = distance_eu.mean()
    return average_distance_eu

os.makedirs(os.path.join(os.path.dirname(__file__), 'out'), exist_ok=True)
out = open(os.path.join(os.path.dirname(__file__), 'out', 'ed_dtw_pairing.txt'), 'w')

rng = np.random.default_rng(0)

# Shape convention in TSG_evaluation: (n_samples, length, n_channels)
# Case A: identical real & synthetic samples but in a DIFFERENT random order.
# If ED were a *set/distribution* comparison, reordering the synthetic block
# would not change the score. If it is an INDEX-WISE pairing, it changes.
real = rng.standard_normal((30, 20, 1))
gen_same_order = real.copy()
perm = rng.permutation(30)
gen_shuffled = real[perm].copy()

ed_same = calculate_ed(real, gen_same_order)
ed_shuf = calculate_ed(real, gen_shuffled)

out.write("Case A: synthetic set == real set, only the row order differs.\n")
out.write(f"  ED(real, real in same order)    = {ed_same:.6f}\n")
out.write(f"  ED(real, real in shuffled order)= {ed_shuf:.6f}\n")
out.write("  -> If these differ, calculate_ed pairs sample i of real with sample i\n")
out.write("     of synthetic by array index (not a distributional comparison).\n\n")

# Case B: unequal counts. Paper generates 100 synthetic vs 30 real (multisample/uv).
# calculate_ed loops over range(ori_data.shape[0]); show it silently uses only the
# first n_real synthetic rows and ignores the rest.
real2 = rng.standard_normal((30, 20, 1))
gen100 = rng.standard_normal((100, 20, 1))
ed_full = calculate_ed(real2, gen100)
ed_first30 = calculate_ed(real2, gen100[:30])
out.write("Case B: 30 real vs 100 synthetic (paper's multisample/univariate counts).\n")
out.write(f"  ED(real[30], gen[100])      = {ed_full:.6f}\n")
out.write(f"  ED(real[30], gen[:30])      = {ed_first30:.6f}\n")
out.write("  -> Identical => synthetic rows 30..99 are never used; ED uses only the\n")
out.write("     first 30 synthetic rows, paired by index to the 30 real rows.\n")

out.close()
print(open(os.path.join(os.path.dirname(__file__), 'out', 'ed_dtw_pairing.txt')).read())
