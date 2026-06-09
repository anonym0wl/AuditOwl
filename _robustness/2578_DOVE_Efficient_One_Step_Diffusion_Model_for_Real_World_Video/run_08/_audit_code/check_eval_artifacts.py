#!/usr/bin/env python3
"""Deterministic checks for DOVE audit: missing eval modules, eval_dover off-by-one,
and the inference.sh hardcoded-UDM10 --gt bug. Read-only; writes CSV to out/."""
import csv
import os
import re

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "code", "zhengchen1999__DOVE"))
OUT = os.path.join(os.path.dirname(__file__), "out")
os.makedirs(OUT, exist_ok=True)

rows = []

# 1. Missing external eval packages referenced by eval scripts.
ewarp_module = []
for dp, _, fns in os.walk(REPO):
    for fn in fns:
        if fn == "ewarp.py":
            ewarp_module.append(os.path.join(dp, fn))
dover_pkg = os.path.isdir(os.path.join(REPO, "finetune", "scripts", "DOVER")) or \
            any(os.path.isdir(os.path.join(dp, "DOVER")) for dp, _, _ in os.walk(REPO))
vbench_pkg = any(os.path.basename(dp) == "VBench" for dp, _, _ in os.walk(REPO))
rows.append(["ewarp_module_present", bool(ewarp_module), str(ewarp_module)])
rows.append(["DOVER_package_present", dover_pkg, "imported at eval_dover.py:150 'from DOVER...'"])
rows.append(["VBench_package_present", vbench_pkg, "sys.path.append at eval_vbench.py:19-20"])

# 2. eval_ewarp chdir target vs actual RAFT location, and default model path.
raft_at_cwd = os.path.isdir(os.path.join(REPO, "RAFT"))
raft_actual = os.path.isdir(os.path.join(REPO, "finetune", "utils", "RAFT"))
default_model = os.path.exists(os.path.join(REPO, "finetune", "scripts", "models", "raft-things.pth"))
rows.append(["eval_ewarp_chdir_RAFT_at_repo_root_exists", raft_at_cwd, "eval_ewarp.py:147 joins original_dir+'RAFT'"])
rows.append(["RAFT_actual_at_finetune_utils", raft_actual, "actual location finetune/utils/RAFT"])
rows.append(["eval_ewarp_default_raft_weights_exist", default_model, "default --model finetune/scripts/models/raft-things.pth"])

# 3. eval_dover off-by-one mapping (i-1 inside enumerate from 0).
dover_src = open(os.path.join(REPO, "finetune", "scripts", "eval_dover.py")).read()
m = re.search(r"for i, name in enumerate\(pred_names\):\s*\n\s*results\[name\] = dover_results\[i-1\]", dover_src)
rows.append(["eval_dover_uses_i_minus_1_index", bool(m), "results[name]=dover_results[i-1] under enumerate from 0"])

# 4. inference.sh: every eval block uses --gt datasets/test/UDM10/GT regardless of dataset.
inf = open(os.path.join(REPO, "inference.sh")).read().splitlines()
gt_lines = [(i + 1, ln.strip()) for i, ln in enumerate(inf) if "--gt" in ln]
pred_lines = [(i + 1, ln.strip()) for i, ln in enumerate(inf) if "--pred" in ln]
n_gt = len(gt_lines)
n_udm10_gt = sum(1 for _, ln in gt_lines if "datasets/test/UDM10/GT" in ln)
# pred datasets other than UDM10 that still point gt to UDM10
mismatched = []
for (gl, gtxt), (pl, ptxt) in zip(gt_lines, pred_lines):
    pred_ds = ptxt.split("results/DOVE/")[-1]
    if "UDM10/GT" in gtxt and not pred_ds.startswith("UDM10"):
        mismatched.append(pred_ds)
rows.append(["inference_sh_num_gt_lines", n_gt, str(gt_lines)])
rows.append(["inference_sh_gt_all_UDM10", n_udm10_gt == n_gt and n_gt > 0,
             f"{n_udm10_gt}/{n_gt} --gt lines point to UDM10/GT"])
rows.append(["inference_sh_pred_datasets_with_wrong_gt", len(mismatched), ",".join(mismatched)])

# 5. Video processing pipeline (Sec 3.3 / Eq.8) code presence.
src_all = ""
for dp, _, fns in os.walk(REPO):
    if ".git" in dp:
        continue
    for fn in fns:
        if fn.endswith((".py", ".yaml", ".sh")):
            try:
                src_all += open(os.path.join(dp, fn), errors="ignore").read().lower()
            except Exception:
                pass
pipeline_terms = {t: (t in src_all) for t in
                  ["aesthetic", "scenedetect", "scene detect", "motion mask", "bounding box", "motion area"]}
rows.append(["pipeline_any_term_present", any(pipeline_terms.values()), str(pipeline_terms)])

with open(os.path.join(OUT, "eval_artifacts.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["check", "value", "detail"])
    w.writerows(rows)

for r in rows:
    print(r)
