#!/usr/bin/env python3
"""Checks whether the VQA / E*_warp eval scripts' imported modules exist in the repo.

Supports findings: missing-dover-package, missing-ewarp-module, ewarp-wrong-raft-path,
missing-fastervqa-script. Repo is read-only; this only inspects the filesystem.
"""
import os, json

REPO = os.path.join(os.path.dirname(__file__), "..", "code", "zhengchen1999__DOVE")
REPO = os.path.abspath(REPO)
scripts = os.path.join(REPO, "finetune", "scripts")

checks = {}

# eval_dover.py imports: from DOVER.evaluate_a_set_of_videos import evaluate_set
# It chdir's into scripts/ first, so DOVER must be importable from scripts/ (cwd) or sys.path.
checks["DOVER_pkg_under_scripts"] = os.path.exists(os.path.join(scripts, "DOVER"))
checks["DOVER_pkg_anywhere"] = any(
    "DOVER" == d for _, dirs, _ in os.walk(REPO) for d in dirs
)

# eval_ewarp.py: raft_dir = os.path.join(original_dir(=scripts), "RAFT"); os.chdir(raft_dir)
checks["RAFT_under_scripts"] = os.path.isdir(os.path.join(scripts, "RAFT"))
# RAFT actually lives under finetune/utils/RAFT
checks["RAFT_under_utils"] = os.path.isdir(os.path.join(REPO, "finetune", "utils", "RAFT"))
# from ewarp import Ewarp  -> ewarp.py must exist in scripts/RAFT (the chdir target)
checks["ewarp_module_in_scripts_RAFT"] = os.path.exists(os.path.join(scripts, "RAFT", "ewarp.py"))
checks["ewarp_module_anywhere"] = any(
    f == "ewarp.py" for _, _, files in os.walk(REPO) for f in files
)

# FasterVQA computation script (README TODO says not added)
fastervqa_hits = []
for root, _, files in os.walk(REPO):
    if ".git" in root:
        continue
    for f in files:
        if f.endswith(".py"):
            try:
                txt = open(os.path.join(root, f), "r", encoding="utf-8", errors="ignore").read()
            except Exception:
                continue
            if "fastervqa" in txt.lower() or "faster_vqa" in txt.lower():
                fastervqa_hits.append(os.path.relpath(os.path.join(root, f), REPO))
checks["fastervqa_script_present"] = len(fastervqa_hits) > 0
checks["fastervqa_hits"] = fastervqa_hits

outp = os.path.join(os.path.dirname(__file__), "out", "missing_eval_deps.json")
with open(outp, "w") as fh:
    json.dump(checks, fh, indent=2)
print(json.dumps(checks, indent=2))
