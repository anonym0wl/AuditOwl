"""Check which Table-2 metrics have a runnable computation script in the repo (supports findings: fastervqa-no-script, ewarp-broken-import, dover-external-dep)."""
import os, json, re

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "code", "zhengchen1999__DOVE"))
OUT = os.path.join(os.path.dirname(__file__), "out")
os.makedirs(OUT, exist_ok=True)

# Metrics reported in Table 2 of the paper.
table2_metrics = ["psnr", "ssim", "lpips", "dists", "clipiqa", "fastervqa", "dover", "ewarp"]

# pyiqa-computable metrics, per eval_metrics.py (fr_metrics + clipiqa via pyiqa.create_metric)
pyiqa_metrics_in_eval = ["psnr", "ssim", "lpips", "dists", "clipiqa"]

def grep_repo(pattern):
    hits = []
    rx = re.compile(pattern, re.IGNORECASE)
    for root, _, files in os.walk(REPO):
        for f in files:
            if f.endswith(".py") or f.endswith(".md") or f.endswith(".sh"):
                p = os.path.join(root, f)
                try:
                    with open(p, "r", errors="ignore") as fh:
                        for i, line in enumerate(fh, 1):
                            if rx.search(line):
                                hits.append((os.path.relpath(p, REPO), i, line.rstrip()))
                except Exception:
                    pass
    return hits

report = {}
for m in table2_metrics:
    report[m] = {
        "pyiqa_in_eval_metrics": m in pyiqa_metrics_in_eval,
    }

# E*_warp: eval_ewarp.py imports `from ewarp import Ewarp`; check the module exists.
ewarp_module = None
raft_dir_under_scripts = os.path.join(REPO, "finetune", "scripts", "RAFT")
ewarp_py_anywhere = []
for root, _, files in os.walk(REPO):
    for f in files:
        if f.lower() == "ewarp.py":
            ewarp_py_anywhere.append(os.path.relpath(os.path.join(root, f), REPO))
report["ewarp"]["import_line"] = "finetune/scripts/eval_ewarp.py:149 -> from ewarp import Ewarp"
report["ewarp"]["ewarp_module_files_in_repo"] = ewarp_py_anywhere
report["ewarp"]["RAFT_dir_under_scripts_exists"] = os.path.isdir(raft_dir_under_scripts)
report["ewarp"]["RAFT_dir_actual_location"] = os.path.relpath(
    os.path.join(REPO, "finetune", "utils", "RAFT"), REPO
) if os.path.isdir(os.path.join(REPO, "finetune", "utils", "RAFT")) else None

# DOVER: eval_dover.py imports external package DOVER
dover_pkg_in_repo = os.path.isdir(os.path.join(REPO, "finetune", "scripts", "DOVER")) or \
                    os.path.isdir(os.path.join(REPO, "DOVER"))
report["dover"]["import_line"] = "finetune/scripts/eval_dover.py:150 -> from DOVER.evaluate_a_set_of_videos import evaluate_set"
report["dover"]["DOVER_pkg_in_repo"] = dover_pkg_in_repo
# requirements.txt content
req = os.path.join(REPO, "requirements.txt")
with open(req) as fh:
    req_lines = [l.strip().lower() for l in fh if l.strip()]
report["dover"]["dover_in_requirements"] = any("dover" in l for l in req_lines)

# FasterVQA: any script?
fastervqa_hits = grep_repo(r"fastervqa")
report["fastervqa"]["repo_mentions"] = fastervqa_hits
report["fastervqa"]["has_compute_script"] = any(
    h[0].endswith(".py") for h in fastervqa_hits
)

with open(os.path.join(OUT, "metric_scripts.json"), "w") as fh:
    json.dump(report, fh, indent=2)

print(json.dumps(report, indent=2))
