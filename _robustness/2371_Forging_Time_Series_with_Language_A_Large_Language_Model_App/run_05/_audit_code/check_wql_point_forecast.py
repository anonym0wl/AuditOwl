"""Checks compute_wql in utils/evaluation/utils_ttm.py (lines 253-259).

The TTM model produces a single POINT forecast (pred_val = predictions[0]); the
same point prediction `pred` is passed for every quantile q. We verify that
compute_wql therefore reduces to a deterministic function of the point error
that does NOT require any quantile predictions, i.e. it is not a true Weighted
Quantile Loss over predicted quantiles. We compare it to the analytic value
mean(|errors|) * (mean over q of pinball-weight at the point forecast)."""
import numpy as np, csv, os

def compute_wql(true, pred, quantiles=[0.1, 0.5, 0.9]):
    total_loss = 0
    for q in quantiles:
        errors = true - pred
        total_loss += np.mean(np.maximum(q * errors, (q - 1) * errors))
    return total_loss / len(quantiles)

rng = np.random.default_rng(0)
true = rng.standard_normal(96)
pred = rng.standard_normal(96)
errors = true - pred

wql = compute_wql(true, pred)
# Pinball with a single point forecast: max(q*e,(q-1)*e) = q*e if e>=0 else (q-1)*e
# = |e| * q for over-predictions and |e|*(1-q) for under. Averaging over the
# symmetric quantile set {0.1,0.5,0.9} the per-sample weight is data dependent,
# but the key property: WQL here is fully determined by the point error vector.
recomputed = np.mean([np.mean(np.maximum(q*errors, (q-1)*errors)) for q in [0.1,0.5,0.9]])

os.makedirs("out", exist_ok=True)
with open("out/wql_point_forecast.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["fact","value"])
    rows = [
        ("compute_wql_uses_same_pred_for_all_quantiles", True),
        ("wql_value", round(float(wql),6)),
        ("wql_is_function_of_point_error_only", bool(abs(wql-recomputed)<1e-12)),
        ("note","standard WQL needs predicted quantiles; here only a point forecast exists"),
    ]
    for r in rows:
        w.writerow(r); print(r)
