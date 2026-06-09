"""Deterministic checks of evaluation-metric implementation facts (read-only).

Confirms code-level facts behind several findings without running the heavy
generation pipeline:
  - ED/DTW pair real[i] with generated[i] by array index (no matching/sort).
  - Preprocessing uses StandardScaler (z-score), NOT [0,1] min-max as Appendix B.2 states.
  - SHAP-RE collapses the channel axis via reshape(shape[0], shape[1]).
  - MASE denominator uses the forecast horizon's own first differences.
  - WQL uses one point prediction for all quantiles and divides by n_quantiles.
Outputs to _audit_code/out/metric_facts.txt
"""
import ast, os, re

BASE = os.path.join(os.path.dirname(__file__), "..", "code",
                    "SDForger__neurips_supplemental")
OUT = os.path.join(os.path.dirname(__file__), "out")
os.makedirs(OUT, exist_ok=True)
lines = []

def src(rel):
    with open(os.path.join(BASE, rel)) as f:
        return f.read()

# 1) ED / DTW index pairing
dbm = src("utils/evaluation/distance_based_measures.py")
ed_idx = "ori_data[i, :, j] - gen_data[i, :, j]" in dbm
dtw_idx = "multi_dtw_distance(ori_data[i]" in dbm and "comp_data[i]" in dbm
has_match = bool(re.search(r"linear_sum_assignment|argmin|nearest|match|sort", dbm))
lines.append(f"[ED] pairs ori_data[i] with gen_data[i] by index: {ed_idx}")
lines.append(f"[DTW] pairs ori_data[i] with comp_data[i] by index: {dtw_idx}")
lines.append(f"[ED/DTW] any matching/sorting before pairing: {has_match}")

# 2) StandardScaler vs [0,1] scaling in preprocessing
pp = src("utils/augmentation/utils_preprocess_data.py")
uses_standardscaler = "StandardScaler()" in pp and "scaler.fit_transform" in pp
uses_minmax = "MinMaxScaler" in pp or "feature_range=(0" in pp
lines.append(f"[preprocess] uses StandardScaler (z-score): {uses_standardscaler}")
lines.append(f"[preprocess] uses MinMax/[0,1] scaling: {uses_minmax}")

# 3) SHAP-RE channel collapse
sh = src("utils/evaluation/shapelet_based_measures.py")
reshape_2d = "reshape(orig_data.shape[0], orig_data.shape[1])" in sh
seeded = bool(re.search(r"np\.random\.seed|random_state", sh))
rand_init = "np.random.randn(n_test, K)" in sh and "np.random.rand(orig_data.shape[0])" in sh
lines.append(f"[SHAP-RE] reshape to (n,length) collapsing channel axis: {reshape_2d}")
lines.append(f"[SHAP-RE] sets a local seed inside calculate_shapelet_recons_err: {seeded}")
lines.append(f"[SHAP-RE] random dictionary/label init each call: {rand_init}")

# 4) MASE / WQL formulas
tt = src("utils/evaluation/utils_ttm.py")
mase_horizon_naive = "np.mean(np.abs(true[1:] - true[:-1]))" in tt
wql_one_pred = "errors = true - pred" in tt and "total_loss / len(quantiles)" in tt
wql_normalized = "np.sum(np.abs(true" in tt  # standard WQL normalises by sum|true|
lines.append(f"[MASE] denominator = mean|true[1:]-true[:-1]| over forecast horizon: {mase_horizon_naive}")
lines.append(f"[WQL] same point 'pred' reused for all quantiles; divided by n_quantiles: {wql_one_pred}")
lines.append(f"[WQL] normalised by sum|true| (standard WQL): {wql_normalized}")

# 5) baselines present?
import glob
all_py = glob.glob(os.path.join(BASE, "**", "*.py"), recursive=True)
bl = re.compile(r"timevae|timevqvae|rtsgan|sdegan|\bls4\b|cosci", re.I)
hits = [p for p in all_py if bl.search(open(p).read())]
lines.append(f"[baselines] py files referencing TimeVAE/TimeVQVAE/RTSGAN/SDEGAN/LS4: {len(hits)}")

txt = "\n".join(lines) + "\n"
with open(os.path.join(OUT, "metric_facts.txt"), "w") as f:
    f.write(txt)
print(txt)
