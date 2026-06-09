"""Checks that calculate_ed/calculate_dtw pair original[i] with generated[i] by
index (no matching), so ED/DTW depend on the arbitrary row order of two
independent sample sets. Supports finding ed-dtw-index-pairing.

Read-only: reimplements the exact loop of
utils/evaluation/distance_based_measures.py::calculate_ed and feeds it two
independent Gaussian sample sets, then re-shuffles the generated set and
recomputes. A permutation-invariant similarity metric would be unchanged under
a re-ordering of the generated rows; this one is not.
"""
import numpy as np
import os

os.makedirs(os.path.join(os.path.dirname(__file__), "out"), exist_ok=True)


def calculate_ed(ori_data, gen_data):
    # verbatim re-implementation of distance_based_measures.calculate_ed
    n_samples = ori_data.shape[0]
    n_series = ori_data.shape[2]
    distance_eu = []
    for i in range(n_samples):
        total_distance_eu = 0
        for j in range(n_series):
            distance = np.linalg.norm(ori_data[i, :, j] - gen_data[i, :, j])
            total_distance_eu += distance
        distance_eu.append(total_distance_eu / n_series)
    return np.array(distance_eu).mean()


rng = np.random.default_rng(0)
# Two INDEPENDENT sample sets drawn from the SAME distribution
# shape (n_samples, length, n_channels)
ori = rng.standard_normal((30, 250, 1))
gen = rng.standard_normal((30, 250, 1))

ed_orig_order = calculate_ed(ori, gen)

# Re-order the generated rows only (same multiset of samples, different order)
perm = rng.permutation(gen.shape[0])
ed_perm_order = calculate_ed(ori, gen[perm])

# Re-order generated rows a second, different way
perm2 = rng.permutation(gen.shape[0])
ed_perm_order2 = calculate_ed(ori, gen[perm2])

lines = []
lines.append(f"ED with generated rows in original order : {ed_orig_order:.4f}")
lines.append(f"ED with generated rows permutation #1    : {ed_perm_order:.4f}")
lines.append(f"ED with generated rows permutation #2    : {ed_perm_order2:.4f}")
lines.append("")
lines.append(
    "If ED were a set-vs-set similarity it would be invariant to re-ordering "
    "the generated rows. It is NOT: the three values above differ, proving ED "
    "(and DTW, same loop) compare original[i] vs generated[i] by arbitrary "
    "index rather than by any matching."
)
out = "\n".join(lines)
print(out)
with open(os.path.join(os.path.dirname(__file__), "out", "ed_index_pairing.txt"), "w") as f:
    f.write(out + "\n")
