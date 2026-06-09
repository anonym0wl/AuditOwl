"""Check whether the committed weather Q_i matrix (weather_96_ratio0.7.npy) is computed
from the TRAIN portion only (first 70%) as the paper claims (X_train), vs the full series.
Supports finding: orthotrans-train-only (verifies no leakage in the precomputed transform).
Read-only: reads dataset CSV + committed npy; writes a summary CSV to out/.
"""
import os
import numpy as np
import pandas as pd
from numpy.linalg import eigh

REPO = os.path.join(os.path.dirname(__file__), "..", "code", "jackyue1994__OLinear")
CSV = os.path.join(REPO, "dataset", "weather", "weather.csv")
QNPY = os.path.join(REPO, "dataset", "weather", "weather_96_ratio0.7.npy")

time_lag = 96
train_ratio = 0.7  # custom dataset uses 0.7 train

data = pd.read_csv(CSV, header=0)
data = data.dropna(axis=1, how="all").values
n = data.shape[0]
train_length = int(n * train_ratio)


def compute_q(A):
    """Replicate Generate_corrmat.ipynb Cell 0 logic."""
    Sigma_list = []
    for f in range(A.shape[1]):
        lagged = np.array([A[i:A.shape[0] - time_lag + i + 1, f] for i in range(time_lag)])
        if np.isnan(lagged).any():
            lagged = np.nan_to_num(lagged)
        cov = np.cov(lagged)
        diag = np.diag(cov)
        if (diag < 1e-4).any():
            continue
        cov = cov / diag
        Sigma_list.append(np.array(cov, dtype=np.float32))
    Sigma = np.mean(Sigma_list, axis=0)
    eigvals, eigvecs = eigh(Sigma)
    return np.flip(eigvecs.T, axis=0).astype(np.float32)


# committed matrix
Q_committed = np.load(QNPY)

# train-only (first 70%), columns 1: (skip date col)
A_train = data[0:train_length, 1:].astype(np.float32)
Q_train = compute_q(A_train)

# full series
A_full = data[0:n, 1:].astype(np.float32)
Q_full = compute_q(A_full)


def diff(a, b):
    # eigenvectors can flip sign; compare abs to be sign-robust, plus raw
    m = min(a.shape[0], b.shape[0])
    raw = np.max(np.abs(a[:m] - b[:m]))
    sign_robust = np.max(np.abs(np.abs(a[:m]) - np.abs(b[:m])))
    return raw, sign_robust


raw_tr, sr_tr = diff(Q_committed, Q_train)
raw_fu, sr_fu = diff(Q_committed, Q_full)

rows = [
    ("committed_shape", str(Q_committed.shape)),
    ("train_recompute_shape", str(Q_train.shape)),
    ("full_recompute_shape", str(Q_full.shape)),
    ("n_total_rows", str(n)),
    ("train_length", str(train_length)),
    ("max_abs_diff_vs_train", f"{raw_tr:.6f}"),
    ("max_abs_diff_signrobust_vs_train", f"{sr_tr:.6f}"),
    ("max_abs_diff_vs_full", f"{raw_fu:.6f}"),
    ("max_abs_diff_signrobust_vs_full", f"{sr_fu:.6f}"),
    ("matches_train_only", str(sr_tr < 1e-3)),
    ("matches_full_series", str(sr_fu < 1e-3)),
]
out = os.path.join(os.path.dirname(__file__), "out", "q_matrix_train_check.csv")
with open(out, "w") as f:
    for k, v in rows:
        f.write(f"{k},{v}\n")
        print(f"{k}: {v}")
print(f"\nSaved -> {out}")
