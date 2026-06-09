"""Sanity-check acf_torch in feature_based_measures.py (lines 98-109).
Line 103: y = x[:, i:] * x[:, :-i] if i > 0 else torch.pow(x, 2)
For i>0, x[:, i:] has T-i steps and x[:, :-i] has T-i steps -> shapes match,
so this is NOT a broadcasting bug. We confirm shapes line up and ACD runs."""
import torch, csv, os

def acf_torch(x, max_lag, dim=(0, 1)):
    acf_list = []
    x = x - x.mean((0, 1))
    std = torch.var(x, unbiased=False, dim=(0, 1))
    for i in range(max_lag):
        y = x[:, i:] * x[:, :-i] if i > 0 else torch.pow(x, 2)
        acf_i = torch.mean(y, dim) / std
        acf_list.append(acf_i)
    return torch.stack(acf_list)

x = torch.randn(30, 250, 1)
res = acf_torch(x, max_lag=64)
os.makedirs("out", exist_ok=True)
with open("out/acf_torch.csv","w",newline="") as f:
    w=csv.writer(f); w.writerow(["fact","value"])
    rows=[("acf_runs_without_error", True), ("output_shape", str(tuple(res.shape)))]
    for r in rows: w.writerow(r); print(r)
