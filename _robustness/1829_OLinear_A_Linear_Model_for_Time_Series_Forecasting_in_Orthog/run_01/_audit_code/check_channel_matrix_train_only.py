"""Check whether committed weather channel-correlation matrix (weather_COV_channel_ratio0.70.npy)
is computed from TRAIN portion only (first 70%), replicating Generate_corrmat.ipynb Cell 1.
Supports finding: orthotrans-train-only. Read-only.
"""
import os
import numpy as np
import pandas as pd

REPO = os.path.join(os.path.dirname(__file__), "..", "code", "jackyue1994__OLinear")
CSV = os.path.join(REPO, "dataset", "weather", "weather.csv")
NPY = os.path.join(REPO, "dataset", "weather", "weather_COV_channel_ratio0.70.npy")

data = pd.read_csv(CSV, header=0).values
A_ori = data[0:, 1:].astype(np.float32)
len_a = A_ori.shape[0]
train_ratio = 0.7

committed = np.load(NPY)

A_train = A_ori[0:int(len_a * train_ratio)]
Q_train = np.corrcoef(A_train.T)

A_full = A_ori[0:len_a]
Q_full = np.corrcoef(A_full.T)

raw_tr = np.nanmax(np.abs(committed - Q_train))
raw_fu = np.nanmax(np.abs(committed - Q_full))

rows = [
    ("committed_shape", str(committed.shape)),
    ("max_abs_diff_vs_train", f"{raw_tr:.6f}"),
    ("max_abs_diff_vs_full", f"{raw_fu:.6f}"),
    ("matches_train_only", str(raw_tr < 1e-4)),
    ("matches_full_series", str(raw_fu < 1e-4)),
]
out = os.path.join(os.path.dirname(__file__), "out", "channel_matrix_train_check.csv")
with open(out, "w") as f:
    for k, v in rows:
        f.write(f"{k},{v}\n")
        print(f"{k}: {v}")
print(f"\nSaved -> {out}")
