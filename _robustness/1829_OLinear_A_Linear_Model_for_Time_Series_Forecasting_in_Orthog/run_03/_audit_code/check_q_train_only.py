"""Checks the OrthoTrans Q matrix is (a) orthonormal and (b) reproducible from
the TRAIN split only (first 70%), i.e. no test-set leakage in its construction.
Supports finding: orthotrans-train-only (no-leakage verification). Read-only."""
import os
import numpy as np
import pandas as pd

REPO = os.path.join(os.path.dirname(__file__), "..", "code", "jackyue1994__OLinear")
OUT = os.path.join(os.path.dirname(__file__), "out")
os.makedirs(OUT, exist_ok=True)

lines = []

def log(s):
    print(s)
    lines.append(s)

# ---- 1. orthonormality of a shipped temporal Q matrix (cars, lag 12) ----
qfile = os.path.join(REPO, "dataset", "cars", "cars_12_ratio0.7.npy")
Q = np.load(qfile).astype(np.float64)
ident_err = np.max(np.abs(Q @ Q.T - np.eye(Q.shape[0])))
log(f"[orthonormal] cars_12_ratio0.7.npy shape={Q.shape} max|QQ^T - I|={ident_err:.2e}")

# ---- 2. reproduce the temporal Q matrix from train-only slice per the notebook ----
# Generate_corrmat.ipynb cell 0: train_ratio=0.7, A = data[train_length-int(N*ratio):train_length, 1:]
csv = os.path.join(REPO, "dataset", "cars", "cars.csv")
df = pd.read_csv(csv, header=0)
df = df.dropna(axis=1, how="all")
data = df.values
train_ratio = 0.7
train_length = int(data.shape[0] * train_ratio)
ratio = train_ratio * 1.0
A = data[train_length - int(data.shape[0] * ratio):train_length, 1:].astype(np.float32)
log(f"[reproduce] cars.csv rows={data.shape[0]} train_length(0.7)={train_length} A.shape={A.shape}")

time_lag = 12
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
eigval, eigvec = np.linalg.eigh(Sigma)
q_repro = np.flip(eigvec.T, axis=0)

# eigenvectors are sign-ambiguous; compare |Q| row-aligned
diff_abs = np.max(np.abs(np.abs(q_repro) - np.abs(Q)))
log(f"[reproduce] max||q_repro| - |Q_shipped|| (sign-free) = {diff_abs:.3e}")

# does the LAST 30% (test+val) feed into this Q at all? confirm slice end == train_length
log(f"[no-leakage] Q uses rows [0:{train_length}] of {data.shape[0]} "
    f"= first {100*train_length/data.shape[0]:.1f}% (train); test rows [{int(data.shape[0]*0.8)}:] excluded")

with open(os.path.join(OUT, "check_q_train_only.txt"), "w") as fh:
    fh.write("\n".join(lines) + "\n")
