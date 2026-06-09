"""Checks which Table-2 metrics have a working compute path in the repo.
Supports findings: ewarp-module-missing, dover-package-missing, fastervqa-no-script,
inference-sh-wrong-gt. Read-only; writes a CSV to out/.
"""
import os, re, csv, ast

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "code", "zhengchen1999__DOVE"))
OUT = os.path.join(os.path.dirname(__file__), "out")
os.makedirs(OUT, exist_ok=True)

def exists(rel):
    return os.path.exists(os.path.join(REPO, rel))

rows = []

# 1. E*warp: eval_ewarp.py imports 'from ewarp import Ewarp' after chdir to RAFT subdir of finetune/scripts
ewarp_anywhere = []
for dirpath, _, files in os.walk(REPO):
    for f in files:
        if f == "ewarp.py" or f.lower().startswith("ewarp"):
            ewarp_anywhere.append(os.path.relpath(os.path.join(dirpath, f), REPO))
rows.append(["E*warp (Table 2)", "finetune/scripts/eval_ewarp.py",
             "imports 'from ewarp import Ewarp'; module files found: %s" % (ewarp_anywhere or "NONE"),
             "MISSING_MODULE" if not ewarp_anywhere else "present"])

# RAFT subdir expected by eval_ewarp.py (it chdir's to finetune/scripts then to ./RAFT)
rows.append(["E*warp RAFT dir", "finetune/scripts/RAFT",
             "eval_ewarp.py does os.chdir(os.path.join(original_dir,'RAFT')) from finetune/scripts",
             "MISSING_DIR" if not exists("finetune/scripts/RAFT") else "present"])

# default raft model path used by eval_ewarp.py
rows.append(["E*warp RAFT ckpt default", "finetune/scripts/models/raft-things.pth",
             "default --model in eval_ewarp.py; actual checkpoint lives at finetune/utils/RAFT/raft-things.pth=%s" % exists("finetune/utils/RAFT/raft-things.pth"),
             "MISSING_PATH" if not exists("finetune/scripts/models/raft-things.pth") else "present"])

# 2. DOVER: eval_dover.py imports DOVER.evaluate_a_set_of_videos
dover_pkg = []
for dirpath, dirs, files in os.walk(REPO):
    for d in dirs:
        if d == "DOVER":
            dover_pkg.append(os.path.relpath(os.path.join(dirpath, d), REPO))
rows.append(["DOVER (Table 2)", "finetune/scripts/eval_dover.py",
             "imports 'from DOVER.evaluate_a_set_of_videos import evaluate_set'; DOVER pkg dirs: %s; in requirements.txt: %s" % (
                 dover_pkg or "NONE",
                 "DOVER" in open(os.path.join(REPO,"requirements.txt")).read()),
             "MISSING_PACKAGE" if not dover_pkg else "present"])

# 3. VBench eval (auxiliary, not in main table)
vbench_pkg = [os.path.relpath(os.path.join(dp,d),REPO) for dp,ds,_ in os.walk(REPO) for d in ds if d=="VBench"]
rows.append(["VBench (aux)", "finetune/scripts/eval_vbench.py",
             "imports 'from evaluate import calculate_final' under ./VBench; VBench dirs: %s" % (vbench_pkg or "NONE"),
             "MISSING_PACKAGE" if not vbench_pkg else "present"])

# 4. FasterVQA: is there ANY script computing it?
faster_hits = []
for dirpath, _, files in os.walk(REPO):
    for f in files:
        if f.endswith((".py",)):
            p = os.path.join(dirpath, f)
            try:
                txt = open(p, encoding="utf-8", errors="ignore").read()
            except Exception:
                continue
            if re.search(r"faster", txt, re.I):
                faster_hits.append((os.path.relpath(p, REPO),
                                    [ln for ln in txt.splitlines() if re.search("faster", ln, re.I)][:2]))
rows.append(["FasterVQA (Table 2 + Fig 1)", "(none)",
             "python files referencing 'faster': %s" % (faster_hits or "NONE"),
             "NO_SCRIPT" if not faster_hits else "present"])

# 5. inference.sh: which --gt is used per eval block
sh = open(os.path.join(REPO, "inference.sh")).read()
gt_lines = re.findall(r"--gt\s+(\S+)", sh)
pred_lines = re.findall(r"--pred\s+(\S+)", sh)
mismatch = []
for gt, pred in zip(gt_lines, pred_lines):
    ds_pred = pred.split("/")[-1]
    ds_gt = gt.split("/")[-2] if "/" in gt else gt
    ok = (ds_gt == ds_pred)
    mismatch.append("pred=%s gt_dataset=%s match=%s" % (ds_pred, ds_gt, ok))
rows.append(["inference.sh eval --gt", "inference.sh",
             " | ".join(mismatch),
             "GT_MISMATCH" if any("match=False" in m for m in mismatch) else "ok"])

with open(os.path.join(OUT, "eval_scripts_check.csv"), "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["paper_artefact", "repo_location", "detail", "status"])
    w.writerows(rows)

for r in rows:
    print(r[3].ljust(16), "|", r[0], "->", r[1])
print("\nWrote", os.path.join(OUT, "eval_scripts_check.csv"))
