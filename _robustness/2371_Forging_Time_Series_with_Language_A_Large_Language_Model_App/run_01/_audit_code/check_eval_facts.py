"""Deterministic checks for TSG similarity-metric evaluation facts.
Supports findings: ed-dtw-index-pairing, ed-scaling-paper-mismatch, shapre-reshape-multichannel.
Read-only: imports nothing from the repo, just reproduces the array logic.
"""
import numpy as np

out = []

# --- Fact 1: ED/DTW pair sample i of original with sample i of generated, ---
# --- and the loop range is ori_data.shape[0] (ED) / ori_data.shape[0] (DTW). ---
# Reproduce calculate_ed control flow with mismatched counts (30 real windows, 100 gen).
n_real, n_gen, L, C = 30, 100, 250, 1
rng = np.random.default_rng(0)
ori = rng.normal(size=(n_real, L, C))
gen = rng.normal(size=(n_gen, L, C))
# calculate_ed: for i in range(ori_data.shape[0]) -> pairs ori[i] with gen[i]
n_iter_ed = ori.shape[0]
out.append(f"ED loop iterates over ori_data.shape[0] = {n_iter_ed} (real windows); "
           f"generated has {n_gen} samples -> {n_gen - n_iter_ed} generated samples are never compared, "
           f"and real window i is paired with generated sample i by raw index.")
# Confirm gen[i] for i in range(n_real) is well-defined (no error) and arbitrary
paired_ok = all(gen[i].shape == ori[i].shape for i in range(n_iter_ed))
out.append(f"Index-pairing ori[i] vs gen[i] runs without error for i<{n_iter_ed}: {paired_ok}")

# --- Fact 2: paper says ED preprocessing fits to [0,1]; code uses StandardScaler ---
# StandardScaler on a (n_windows, window_length) array standardizes each COLUMN
# (each timestamp position across windows) to zero-mean unit-variance, range != [0,1].
from sklearn.preprocessing import StandardScaler
arr = rng.normal(loc=5.0, scale=3.0, size=(n_real, L))
scaled = StandardScaler().fit_transform(arr)
out.append(f"StandardScaler output range = [{scaled.min():.3f}, {scaled.max():.3f}] "
           f"(NOT within [0,1] as the paper's ED definition states).")
out.append(f"StandardScaler column means ~0: max|mean|={np.abs(scaled.mean(0)).max():.2e}; "
           f"this scales per-timestamp across windows, not per-series to [0,1].")

# --- Fact 3: shapelet RE reshape(shape[0], shape[1]) requires shape[2]==1 ---
# calculate_shapelet_recons_err does orig_data.reshape(orig_data.shape[0], orig_data.shape[1])
multi = rng.normal(size=(n_real, L, 3))  # 3 channels
try:
    multi.reshape(multi.shape[0], multi.shape[1])
    res = "reshape SUCCEEDED unexpectedly"
except ValueError as e:
    res = f"reshape RAISED ValueError -> SHAP-RE only handles single-channel (C=1) input. ({e})"
out.append(res)
single = rng.normal(size=(n_real, L, 1))
single.reshape(single.shape[0], single.shape[1])
out.append("SHAP-RE reshape works only when n_channels==1 (drops the channel axis).")

with open("out/eval_facts.txt", "w") as f:
    f.write("\n".join(out) + "\n")
print("\n".join(out))
