"""Checks which Table-2 metrics have computation code in the repo and whether
the eval scripts' imports/paths resolve. Supports findings:
ewarp-module-missing, fastervqa-no-code, dover-external-and-offbyone.
Read-only; writes a CSV under out/."""
import os, csv, re

REPO = os.path.join(os.path.dirname(__file__), "..", "code", "zhengchen1999__DOVE")
REPO = os.path.abspath(REPO)

rows = []

def exists(rel):
    return os.path.exists(os.path.join(REPO, rel))

# 1. ewarp module that eval_ewarp.py imports ("from ewarp import Ewarp")
ewarp_module_found = []
for dp, _, fns in os.walk(REPO):
    for fn in fns:
        if fn == "ewarp.py":
            ewarp_module_found.append(os.path.relpath(os.path.join(dp, fn), REPO))
# any "def Ewarp" definition anywhere
ewarp_def = []
for dp, _, fns in os.walk(REPO):
    for fn in fns:
        if fn.endswith(".py"):
            p = os.path.join(dp, fn)
            try:
                t = open(p, encoding="utf-8", errors="ignore").read()
            except Exception:
                continue
            if re.search(r"def\s+Ewarp\b", t):
                ewarp_def.append(os.path.relpath(p, REPO))
rows.append(["ewarp.py module file present", str(bool(ewarp_module_found)), ";".join(ewarp_module_found) or "NONE"])
rows.append(["'def Ewarp' defined anywhere", str(bool(ewarp_def)), ";".join(ewarp_def) or "NONE"])

# 2. RAFT dir that eval_ewarp.py chdir's into: finetune/scripts/RAFT
rows.append(["finetune/scripts/RAFT exists (eval_ewarp chdir target)", str(exists("finetune/scripts/RAFT")), "expected by eval_ewarp.py line 147-148"])
rows.append(["finetune/scripts/models/raft-things.pth exists (eval_ewarp default --model)", str(exists("finetune/scripts/models/raft-things.pth")), "actual is finetune/utils/RAFT/raft-things.pth"])
rows.append(["finetune/utils/RAFT/raft-things.pth exists", str(exists("finetune/utils/RAFT/raft-things.pth")), ""])

# 3. VBench dir that eval_vbench.py chdir's into: finetune/scripts/VBench
rows.append(["finetune/scripts/VBench exists (eval_vbench chdir target)", str(exists("finetune/scripts/VBench")), "expected by eval_vbench.py line 146-147"])

# 4. DOVER package import in eval_dover.py
dover_pkg = exists("finetune/scripts/DOVER") or exists("DOVER")
rows.append(["DOVER package vendored in repo", str(dover_pkg), "eval_dover.py imports DOVER.evaluate_a_set_of_videos"])

# 5. FasterVQA computation code
fastervqa_code = []
for dp, _, fns in os.walk(REPO):
    for fn in fns:
        if fn.endswith(".py"):
            t = open(os.path.join(dp, fn), encoding="utf-8", errors="ignore").read()
            if re.search(r"faster.?vqa", t, re.I):
                fastervqa_code.append(os.path.relpath(os.path.join(dp, fn), REPO))
rows.append(["FasterVQA computation code present (.py)", str(bool(fastervqa_code)), ";".join(fastervqa_code) or "NONE"])

# 6. DOVER per-sample off-by-one: simulate results[name]=dover_results[i-1]
dover_results = ["score_for_vid0", "score_for_vid1", "score_for_vid2"]
pred_names = ["vid0", "vid1", "vid2"]
mapping = {}
for i, name in enumerate(pred_names):
    mapping[name] = dover_results[i-1]
correct = all(mapping[n] == dover_results[j] for j, n in enumerate(pred_names))
rows.append(["DOVER per-sample mapping correct (results[name]=dover_results[i-1])", str(correct), str(mapping)])
# average is order-independent
import statistics
vals = [0.7, 0.8, 0.9]
mean_offset = statistics.mean([vals[i-1] for i in range(len(vals))])
mean_direct = statistics.mean(vals)
rows.append(["DOVER average unaffected by i-1 offset", str(mean_offset == mean_direct), f"{mean_offset} vs {mean_direct}"])

# 7. requirements.txt content checks
req = open(os.path.join(REPO, "requirements.txt"), encoding="utf-8").read().lower()
rows.append(["'diffusers' pinned in requirements.txt", str("diffusers" in req), "needed for CogVideoX pipeline/scheduler"])
rows.append(["'pyiqa' in requirements.txt", str("pyiqa" in req), "needed for all reported IQA metrics"])

# 8. video processing pipeline (Sec 3.3) code: scene detect / motion-area crop / quality filter
pipeline_hits = []
for dp, _, fns in os.walk(REPO):
    for fn in fns:
        if fn.endswith(".py"):
            t = open(os.path.join(dp, fn), encoding="utf-8", errors="ignore").read()
            if re.search(r"scenedetect|scene_detect|motion_mask|motion_area|bounding_box|aesthetic", t, re.I):
                pipeline_hits.append(os.path.relpath(os.path.join(dp, fn), REPO))
rows.append(["Sec 3.3 video-processing-pipeline code present", str(bool(pipeline_hits)), ";".join(pipeline_hits) or "NONE"])

os.makedirs(os.path.join(os.path.dirname(__file__), "out"), exist_ok=True)
out = os.path.join(os.path.dirname(__file__), "out", "missing_metric_code.csv")
with open(out, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["check", "value", "detail"])
    w.writerows(rows)

for r in rows:
    print(r)
print("\nWrote", out)
