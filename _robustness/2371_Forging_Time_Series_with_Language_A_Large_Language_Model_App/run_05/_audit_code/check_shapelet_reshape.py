"""Checks that calculate_shapelet_recons_err's reshape collapses channels and
breaks for multivariate (C>1) data. Supports finding shapelet-reshape-univariate-only.

It re-implements ONLY the reshape lines from
utils/evaluation/shapelet_based_measures.py (lines 20-21) on synthetic arrays
shaped like the TSG eval inputs (n_samples, time, channels)."""
import numpy as np

def reshape_like_code(orig_data):
    # verbatim logic from shapelet_based_measures.py lines 20-21
    return orig_data.reshape(orig_data.shape[0], orig_data.shape[1])

rows = []
# univariate: (n, T, 1) -> reshape to (n, T) is a no-op collapse, OK
uni = np.arange(5*250*1).reshape(5, 250, 1).astype(float)
try:
    r = reshape_like_code(uni)
    rows.append(("univariate(n=5,T=250,C=1)", str(uni.shape), str(r.shape), "OK_collapses_to_2D"))
except Exception as e:
    rows.append(("univariate(n=5,T=250,C=1)", str(uni.shape), "ERROR", repr(e)))

# multivariate: (n, T, 3) -> reshape(n, T) requires n*T elements but array has n*T*3
mv = np.arange(5*250*3).reshape(5, 250, 3).astype(float)
try:
    r = reshape_like_code(mv)
    rows.append(("multivariate(n=5,T=250,C=3)", str(mv.shape), str(r.shape), "NO_ERROR_but_lossy?"))
except Exception as e:
    rows.append(("multivariate(n=5,T=250,C=3)", str(mv.shape), "ERROR", type(e).__name__+": "+str(e)))

import csv, os
os.makedirs("out", exist_ok=True)
with open("out/shapelet_reshape.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["case", "input_shape", "output_shape", "verdict"])
    for row in rows:
        w.writerow(row)
        print(row)
