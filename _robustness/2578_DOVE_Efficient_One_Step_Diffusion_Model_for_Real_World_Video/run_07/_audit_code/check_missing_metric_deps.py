"""Checks: (1) no FasterVQA computation in repo; (2) eval_dover/eval_ewarp/eval_vbench
import external packages/files not present in the repo; (3) eval_ewarp default RAFT model
path does not exist. Supports findings: fastervqa-no-code, dover-ewarp-vbench-missing-deps,
ewarp-broken-paths. Read-only."""
import os, re, subprocess, json

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "code", "zhengchen1999__DOVE"))
out = {}

# (1) Search for any FasterVQA computation across .py (case-insensitive)
py_hits = []
for root, _, files in os.walk(REPO):
    if ".git" in root:
        continue
    for f in files:
        if f.endswith(".py"):
            p = os.path.join(root, f)
            try:
                txt = open(p, encoding="utf-8", errors="ignore").read()
            except Exception:
                continue
            for m in re.finditer(r"faster[_ ]?vqa|fast[_ ]?vqa", txt, re.I):
                line_no = txt[:m.start()].count("\n") + 1
                py_hits.append((os.path.relpath(p, REPO), line_no, m.group(0)))
out["fastervqa_python_hits"] = py_hits

# (2) external import targets and whether the module file exists where the script would look
checks = []
# eval_dover.py: cwd is finetune/scripts ; imports DOVER.evaluate_a_set_of_videos
dover_pkg = os.path.join(REPO, "finetune", "scripts", "DOVER")
checks.append(("eval_dover.py -> finetune/scripts/DOVER/", os.path.isdir(dover_pkg)))
# eval_ewarp.py: cwd is finetune/scripts ; sys.path RAFT under cwd ; from ewarp import Ewarp (in finetune/scripts/RAFT)
ewarp_raft_dir = os.path.join(REPO, "finetune", "scripts", "RAFT")
ewarp_mod = os.path.join(ewarp_raft_dir, "ewarp.py")
checks.append(("eval_ewarp.py -> finetune/scripts/RAFT/ (chdir target)", os.path.isdir(ewarp_raft_dir)))
checks.append(("eval_ewarp.py -> finetune/scripts/RAFT/ewarp.py", os.path.isfile(ewarp_mod)))
# any ewarp.py anywhere
any_ewarp = []
for root, _, files in os.walk(REPO):
    for f in files:
        if f.lower() == "ewarp.py":
            any_ewarp.append(os.path.relpath(os.path.join(root, f), REPO))
checks.append(("any ewarp.py in repo", any_ewarp if any_ewarp else False))
# eval_vbench.py: from evaluate import calculate_final (in finetune/scripts/VBench)
vbench_dir = os.path.join(REPO, "finetune", "scripts", "VBench")
checks.append(("eval_vbench.py -> finetune/scripts/VBench/", os.path.isdir(vbench_dir)))
# (3) eval_ewarp default model path: finetune/scripts/models/raft-things.pth (relative to cwd=finetune/scripts)
ewarp_default_model = os.path.join(REPO, "finetune", "scripts", "models", "raft-things.pth")
checks.append(("eval_ewarp default --model finetune/scripts/models/raft-things.pth", os.path.isfile(ewarp_default_model)))
# where raft-things.pth actually is
raft_actual = []
for root, _, files in os.walk(REPO):
    for f in files:
        if f == "raft-things.pth":
            raft_actual.append(os.path.relpath(os.path.join(root, f), REPO))
checks.append(("actual raft-things.pth location(s)", raft_actual))
out["import_path_checks"] = checks

print(json.dumps(out, indent=2))
with open(os.path.join(os.path.dirname(__file__), "out", "missing_metric_deps.json"), "w") as f:
    json.dump(out, f, indent=2)
