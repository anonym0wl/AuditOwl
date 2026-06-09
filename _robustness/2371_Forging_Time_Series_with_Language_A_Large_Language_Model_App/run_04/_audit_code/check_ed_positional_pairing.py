"""Check (supports ed-dtw-positional-pairing): the repo's calculate_ed pairs
original[i] with generated[i] by ARRAY INDEX, ignores extra generated samples,
and is sensitive to the ordering of generated rows -- i.e. it does not compute a
distribution-level distance between two unordered sets of curves. We reproduce
the exact loop from utils/evaluation/distance_based_measures.py:calculate_ed.
Read-only; writes a summary CSV under out/."""
import numpy as np
import os

OUT = os.path.join(os.path.dirname(__file__), "out")
os.makedirs(OUT, exist_ok=True)


def calculate_ed(ori_data, gen_data):
    # verbatim re-implementation of repo calculate_ed
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
    return distance_eu.mean(), len(distance_eu)


rng = np.random.RandomState(0)
# univariate config shapes after transpose: ori (30,250,1), gen (100,250,1)
n_ori, length, n_ch = 30, 250, 1
n_gen = 100
ori = rng.rand(n_ori, length, n_ch)
gen = rng.rand(n_gen, length, n_ch)

ed_orig, n_used = calculate_ed(ori, gen)

# Permute the generated rows: a *set-level* distance must be invariant to this.
perm = rng.permutation(n_gen)
gen_perm = gen[perm]
ed_perm, _ = calculate_ed(ori, gen_perm)

# How many generated samples are actually consumed?
gen_used = n_used  # = n_ori
gen_ignored = n_gen - gen_used

rows = [
    ("n_original_samples", n_ori),
    ("n_generated_samples", n_gen),
    ("generated_samples_used_by_ED", gen_used),
    ("generated_samples_ignored", gen_ignored),
    ("ED_default_order", round(float(ed_orig), 6)),
    ("ED_after_permuting_generated_rows", round(float(ed_perm), 6)),
    ("ED_changes_with_generated_order", ed_orig != ed_perm),
]
import csv
with open(os.path.join(OUT, "ed_positional_pairing.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["key", "value"])
    for k, v in rows:
        w.writerow([k, v])
for k, v in rows:
    print(f"{k},{v}")
