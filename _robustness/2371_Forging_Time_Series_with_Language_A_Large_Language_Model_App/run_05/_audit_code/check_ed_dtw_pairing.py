"""Demonstrates that calculate_ed / calculate_dtw in
utils/evaluation/distance_based_measures.py pair the i-th ORIGINAL window with
the i-th GENERATED sample by array index, and that the number of compared pairs
equals ori_data.shape[0] (so when generated > original, extra generated samples
are silently ignored; and the pairing has no semantic correspondence because
generated samples are produced independently of any specific real window).

Re-implements ONLY calculate_ed's loop structure (lines 13-26)."""
import numpy as np, csv, os

def calculate_ed(ori_data, gen_data):
    n_samples = ori_data.shape[0]
    n_series = ori_data.shape[2]
    distance_eu = []
    for i in range(n_samples):
        total = 0
        for j in range(n_series):
            total += np.linalg.norm(ori_data[i, :, j] - gen_data[i, :, j])
        distance_eu.append(total / n_series)
    return np.array(distance_eu).mean(), n_samples

rng = np.random.default_rng(0)
# multisample/univariate eval shapes after .transpose(1,2,0): (n_samples, T, C)
ori = rng.standard_normal((30, 250, 1))   # 30 real windows
gen = rng.standard_normal((100, 250, 1))  # 100 generated samples (paper: 100)

ed, n_pairs = calculate_ed(ori, gen)
# Show that permuting the generated rows changes ED -> pairing is order-dependent
perm = rng.permutation(gen.shape[0])
ed_perm, _ = calculate_ed(ori, gen[perm])

os.makedirs("out", exist_ok=True)
with open("out/ed_dtw_pairing.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["fact", "value"])
    rows = [
        ("n_original_windows", ori.shape[0]),
        ("n_generated_samples", gen.shape[0]),
        ("n_pairs_actually_compared (==ori.shape[0])", n_pairs),
        ("generated_samples_ignored (n_gen - n_pairs)", gen.shape[0]-n_pairs),
        ("ED_with_natural_order", round(float(ed), 6)),
        ("ED_with_permuted_generated_rows", round(float(ed_perm), 6)),
        ("ED_changes_under_permutation", bool(abs(ed-ed_perm) > 1e-9)),
    ]
    for r in rows:
        w.writerow(r); print(r)
