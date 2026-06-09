#!/usr/bin/env python3
"""Checks which evaluation metrics in Table 2 have computation code in the repo.

Supports findings: ewarp-module-missing, dover-vbench-external-deps,
pyiqa-not-in-requirements. Read-only; writes a CSV to out/.
"""
import os
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent / "code" / "zhengchen1999__DOVE"
OUT = Path(__file__).resolve().parent / "out"
OUT.mkdir(parents=True, exist_ok=True)


def file_exists(*names):
    hits = []
    for root, _, files in os.walk(REPO):
        for f in files:
            if f in names:
                hits.append(os.path.relpath(os.path.join(root, f), REPO))
    return hits


rows = []

# ewarp module (imported by finetune/scripts/eval_ewarp.py:149 `from ewarp import Ewarp`)
ewarp = file_exists("ewarp.py")
rows.append(("ewarp.py module (E*warp metric, Table 2)", ewarp or "ABSENT"))

# DOVER package (imported by eval_dover.py:150)
dover_dir = [os.path.relpath(os.path.join(r), REPO)
             for r, d, _ in os.walk(REPO) for x in d if x == "DOVER"]
rows.append(("DOVER/ package (DOVER metric, Table 2)", dover_dir or "ABSENT (external dep)"))

# VBench package (imported by eval_vbench.py:149)
vbench_dir = [os.path.relpath(os.path.join(r), REPO)
              for r, d, _ in os.walk(REPO) for x in d if x == "VBench"]
rows.append(("VBench/ package (not a Table-2 metric)", vbench_dir or "ABSENT (external dep)"))

# pyiqa in requirements?
req = (REPO / "requirements.txt").read_text()
rows.append(("pyiqa listed in requirements.txt",
             "YES" if "pyiqa" in req.lower() else "NO (needed by eval_metrics.py)"))

# video processing pipeline (HQ-VSR construction, Sec 3.3) -- search for curation steps
patterns = ["scenedetect", "scene_detect", "aesthetic", "motion_mask",
            "motion_area", "bounding_box"]
found_pipeline = subprocess.run(
    ["grep", "-rniIl", "|".join(patterns), "-E",
     str(REPO / "finetune" / "datasets"),
     str(REPO / "finetune" / "scripts")],
    capture_output=True, text=True)
rows.append(("HQ-VSR curation pipeline code (Sec 3.3/Fig 3)",
             found_pipeline.stdout.strip() or "ABSENT"))

csv = OUT / "missing_eval_modules.csv"
with open(csv, "w") as f:
    f.write("artefact,status\n")
    for a, s in rows:
        f.write(f"\"{a}\",\"{s}\"\n")

for a, s in rows:
    print(f"{a}: {s}")
print(f"\nWrote {csv}")
