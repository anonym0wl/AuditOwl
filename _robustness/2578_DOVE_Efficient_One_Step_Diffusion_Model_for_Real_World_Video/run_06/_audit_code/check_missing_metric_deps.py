"""Checks presence of metric-computation code/deps: FasterVQA script, DOVER package,
ewarp module, VBench module, RAFT dir/ckpt for eval_ewarp, and pyiqa in requirements.
Supports findings on missing VQA/temporal metric code. Read-only."""
import os, json

REPO = os.path.join(os.path.dirname(__file__), "..", "code", "zhengchen1999__DOVE")

def exists(p):
    return os.path.exists(os.path.join(REPO, p))

# search whole tree for substrings
def grep_tree(needles):
    hits = {n: [] for n in needles}
    for root, dirs, files in os.walk(REPO):
        if ".git" in root:
            continue
        for f in files:
            if not (f.endswith(".py") or f.endswith(".sh") or f.endswith(".md") or f.endswith(".txt")):
                continue
            fp = os.path.join(root, f)
            try:
                t = open(fp, errors="ignore").read()
            except Exception:
                continue
            for n in needles:
                if n.lower() in t.lower():
                    hits[n].append(os.path.relpath(fp, REPO))
    return hits

checks = {}
# FasterVQA: is there any code computing it?
checks["fastervqa_create_metric"] = grep_tree(["fastervqa", "fast_vqa", "FAST-VQA"])
# DOVER package present?
checks["DOVER_package_dir"] = exists("finetune/scripts/DOVER") or exists("DOVER")
# ewarp module that defines Ewarp (imported by eval_ewarp.py)
checks["ewarp_module_files"] = grep_tree(["def Ewarp"])
# VBench evaluate.calculate_final
checks["vbench_dir"] = exists("finetune/scripts/VBench") or exists("VBench")
# RAFT dir where eval_ewarp.py chdir's into (finetune/scripts/RAFT) + its default model path
checks["scripts_RAFT_dir"] = exists("finetune/scripts/RAFT")
checks["scripts_models_raft_pth"] = exists("finetune/scripts/models/raft-things.pth")
checks["utils_RAFT_raft_pth"] = exists("finetune/utils/RAFT/raft-things.pth")
# pyiqa in requirements?
req = open(os.path.join(REPO, "requirements.txt")).read().lower()
checks["pyiqa_in_requirements"] = ("pyiqa" in req)
# musiq/maniqa metrics referenced but used in Table 2? (paper Table 2 uses fastervqa/dover/ewarp)

outpath = os.path.join(os.path.dirname(__file__), "out", "missing_metric_deps.json")
json.dump(checks, open(outpath, "w"), indent=2)
print(json.dumps(checks, indent=2))
