"""Verifies the train/test split in utils.load_adbench_npz on one small dataset.

Supports the methodology review of data splitting: confirms (a) training uses
ONLY normal samples, (b) train/test normal rows are disjoint, (c) the
StandardScaler is fit on X_train only (no test statistics leak). Read-only;
loads a frozen dataset file directly. Output: out/split_and_scaler.txt
"""
import os
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

DS = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                  "..", "code", "ZhongLIFR__TCCM-NIPS", "datasets", "small", "42_WBC.npz")

data = np.load(DS, allow_pickle=True)
X, y = data["X"], data["y"].astype(int)

X_normal, X_anom = X[y == 0], X[y == 1]
y_normal = y[y == 0]

X_train, X_test_normal, y_train, _ = train_test_split(
    X_normal, y_normal, test_size=0.5, random_state=0, stratify=y_normal
)
X_test = np.vstack((X_test_normal, X_anom))

# Disjointness of normal rows between train and test
train_rows = set(map(lambda r: r.tobytes(), X_train))
test_normal_rows = set(map(lambda r: r.tobytes(), X_test_normal))
overlap = train_rows & test_normal_rows

# Scaler fit on train only -> train mean ~0, train std ~1; test mean != 0 generally
scaler = StandardScaler().fit(X_train)
Xtr = scaler.transform(X_train)
Xte = scaler.transform(X_test)

out = []
out.append(f"dataset = 42_WBC; X={X.shape}, normals={len(X_normal)}, anomalies={len(X_anom)}")
out.append(f"train labels unique = {np.unique(y_train)} (should be [0] = normal-only)")
out.append(f"X_train rows = {len(X_train)}, X_test_normal rows = {len(X_test_normal)}")
out.append(f"train/test-normal row overlap = {len(overlap)} (should be 0)")
out.append(f"scaled-train mean abs = {abs(Xtr.mean()):.4f} (≈0), std = {Xtr.std():.4f} (≈1)")
out.append(f"scaled-test  mean abs = {abs(Xte.mean()):.4f} (≠0 expected: scaler fit on train only)")
text = "\n".join(out)
print(text)
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "split_and_scaler.txt"), "w") as f:
    f.write(text + "\n")
