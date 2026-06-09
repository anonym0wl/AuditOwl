"""Checks that the external modules imported by the VQA/Ewarp eval scripts exist in the repo
(supports findings ewarp-module-missing, dover-vbench-external-deps).
Read-only filesystem existence checks.
"""
import json, os

REPO = os.path.join(os.path.dirname(__file__), "..", "code", "zhengchen1999__DOVE")

def exists(rel):
    return os.path.exists(os.path.join(REPO, rel))

checks = {
    # eval_ewarp.py: chdir to original_dir/RAFT then `from ewarp import Ewarp`
    "finetune/scripts/RAFT/ (chdir target)": exists("finetune/scripts/RAFT"),
    "any ewarp.py in repo": any(
        f == "ewarp.py" for _, _, fs in os.walk(REPO) for f in fs
    ),
    "raft-things.pth at default --model path (finetune/scripts/models/raft-things.pth)":
        exists("finetune/scripts/models/raft-things.pth"),
    "raft-things.pth actual location (finetune/utils/RAFT/raft-things.pth)":
        exists("finetune/utils/RAFT/raft-things.pth"),
    # eval_vbench.py: chdir to original_dir/VBench then `from evaluate import calculate_final`
    "finetune/scripts/VBench/ (chdir target)": exists("finetune/scripts/VBench"),
    "any VBench dir in repo": any(
        d == "VBench" for _, ds, _ in os.walk(REPO) for d in ds
    ),
    # eval_dover.py: `from DOVER.evaluate_a_set_of_videos import evaluate_set`
    "any DOVER package dir in repo": any(
        d == "DOVER" for _, ds, _ in os.walk(REPO) for d in ds
    ),
    # requirements coverage
    "pyiqa in requirements.txt": "pyiqa" in open(os.path.join(REPO, "requirements.txt")).read().lower(),
    "diffusers in requirements.txt": "diffusers" in open(os.path.join(REPO, "requirements.txt")).read().lower(),
}
os.makedirs(os.path.join(os.path.dirname(__file__), "out"), exist_ok=True)
with open(os.path.join(os.path.dirname(__file__), "out", "eval_imports.json"), "w") as f:
    json.dump(checks, f, indent=2)
print(json.dumps(checks, indent=2))
