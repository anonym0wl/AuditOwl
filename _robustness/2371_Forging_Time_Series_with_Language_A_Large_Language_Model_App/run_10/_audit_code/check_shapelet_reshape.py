"""Checks whether calculate_shapelet_recons_err's reshape works for C>1 channels.
Supports finding: shapelet-reshape-multivariate-crash."""
import numpy as np

# Mimic shapelet_based_measures.calculate_shapelet_recons_err reshape:
#   train_data = orig_data.reshape(orig_data.shape[0], orig_data.shape[1])
# orig_data has shape (n_samples, length, n_channels) after transpose(1,2,0) in TSG_evaluation.

def try_reshape(n, L, C):
    arr = np.zeros((n, L, C))
    try:
        out = arr.reshape(arr.shape[0], arr.shape[1])
        return f"OK -> shape {out.shape}"
    except Exception as e:
        return f"CRASH: {type(e).__name__}: {e}"

print("C=1 (univariate/multisample, length 250):", try_reshape(30, 250, 1))
print("C=2 (multivariate, 2 channels):", try_reshape(30, 250, 2))
print("C=3 (multivariate bikesharing, 3 channels):", try_reshape(30, 250, 3))
