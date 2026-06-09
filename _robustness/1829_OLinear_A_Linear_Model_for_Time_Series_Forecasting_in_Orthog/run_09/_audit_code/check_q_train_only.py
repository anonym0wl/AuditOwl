"""Checks whether the shipped temporal Q-matrix npy (OrthoTrans basis) was
computed from the TRAIN portion only (no test/full-data leakage). Reproduces
the Generate_corrmat.ipynb (cell 0) algorithm on (a) train-only and (b)
full-data, then compares each against the shipped npy. Supports finding
'orthotrans-q-train-only' (sanity / no-leakage confirmation)."""
import os
import numpy as np
import pandas as pd
from numpy.linalg import eigh

REPO = os.path.join(os.path.dirname(__file__), "..", "code", "jackyue1994__OLinear")


def build_q(A, time_lag):
    # exact replica of Generate_corrmat.ipynb cell 0
    Sigma_list = []
    for feature_idx in range(int(A.shape[1] / 1)):
        lagged_matrix = np.array([
            A[i:A.shape[0] - time_lag + i + 1, feature_idx]
            for i in range(time_lag)
        ])
        if np.isnan(lagged_matrix).any():
            lagged_matrix = np.nan_to_num(lagged_matrix)
        cov_matrix = np.cov(lagged_matrix)
        diag_vec = np.diag(cov_matrix)
        if (diag_vec < 1e-4).any():
            continue
        cov_matrix = cov_matrix / diag_vec
        Sigma_list.append(np.array(cov_matrix, dtype=np.float32))
    Sigma = np.mean(Sigma_list, axis=0)
    eigenvalues, eigenvectors = eigh(Sigma)
    q_mat = np.flip(eigenvectors.T, axis=0)
    return np.ascontiguousarray(q_mat)


def best_match(shipped, cand):
    # eigenvectors are sign-ambiguous; compare row-magnitudes via |q q^T| alignment
    # use mean abs diff after sign-aligning each row
    s = shipped.copy()
    c = cand.copy()
    # align signs row by row to maximize agreement
    for r in range(s.shape[0]):
        if np.dot(s[r], c[r]) < 0:
            c[r] = -c[r]
    return float(np.mean(np.abs(s - c)))


def main():
    cases = [
        # (csv, train_ratio, time_lag, shipped_npy, csv_col_start)
        ("dataset/weather/weather.csv", 0.7, 96, "dataset/weather/weather_96_ratio0.7.npy", 1),
        ("dataset/power/power.csv", 0.7, 12, "dataset/power/power_12_ratio0.7.npy", 1),
    ]
    rows = []
    for csv, tr, lag, npy, c0 in cases:
        csv_p = os.path.join(REPO, csv)
        npy_p = os.path.join(REPO, npy)
        if not (os.path.isfile(csv_p) and os.path.isfile(npy_p)):
            rows.append(f"{csv}: MISSING csv or npy, skipped")
            continue
        data = pd.read_csv(csv_p, header=0)
        data = data.dropna(axis=1, how="all").values
        N = data.shape[0]
        train_length = int(N * tr)
        A_train = data[0:train_length, c0:].astype(np.float32)
        A_full = data[:, c0:].astype(np.float32)
        shipped = np.load(npy_p)
        q_train = build_q(A_train, lag)
        q_full = build_q(A_full, lag)
        d_train = best_match(shipped, q_train)
        d_full = best_match(shipped, q_full)
        rows.append(
            f"{os.path.basename(csv)} lag={lag} ratio={tr}: "
            f"meanabsdiff(shipped,train_only)={d_train:.4e}  "
            f"meanabsdiff(shipped,full_data)={d_full:.4e}  "
            f"-> {'TRAIN-ONLY (match train)' if d_train < d_full else 'FULL-DATA?'}"
        )
    out = os.path.join(os.path.dirname(__file__), "out", "q_train_only.txt")
    with open(out, "w") as f:
        f.write("\n".join(rows) + "\n")
    print("\n".join(rows))


if __name__ == "__main__":
    main()
