"""Shows that utils_ttm.compute_wql, fed a single point forecast for all three
quantiles (as TTM produces), reduces exactly to 0.5 * MAE rather than a true
Weighted Quantile Loss. Supports finding wql-is-scaled-mae.
"""
import numpy as np
import os

os.makedirs(os.path.join(os.path.dirname(__file__), "out"), exist_ok=True)


def compute_wql(true, pred, quantiles=[0.1, 0.5, 0.9]):
    # verbatim from utils/evaluation/utils_ttm.py::compute_wql
    total_loss = 0
    for q in quantiles:
        errors = true - pred
        total_loss += np.mean(np.maximum(q * errors, (q - 1) * errors))
    return total_loss / len(quantiles)


rng = np.random.default_rng(0)
true = rng.standard_normal(5000)
pred = rng.standard_normal(5000)  # SAME single point forecast used for every quantile
mae = np.mean(np.abs(true - pred))
wql = compute_wql(true, pred)

out = (
    f"WQL (3 quantiles, identical point prediction) = {wql:.6f}\n"
    f"0.5 * MAE                                     = {0.5*mae:.6f}\n"
    f"ratio WQL / MAE                               = {wql/mae:.6f}\n\n"
    "TTM emits a single point forecast, and compute_wql passes that same point\n"
    "prediction for q=0.1, 0.5, 0.9. The pinball loss with one prediction is\n"
    "0.5*|e| averaged over the symmetric quantile set, so the Table-2 'WQL'\n"
    "column is exactly 0.5*MAE, not a Weighted Quantile Loss (which requires\n"
    "distinct quantile/probabilistic forecasts)."
)
print(out)
with open(os.path.join(os.path.dirname(__file__), "out", "wql_is_half_mae.txt"), "w") as f:
    f.write(out + "\n")
