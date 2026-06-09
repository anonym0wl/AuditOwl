"""Checks that run_semisupervise.sh runs all 7 force_inductive models (indices 45-51).
The loop `for j in {45..50}` runs only 6 indices, dropping index 51 (KNN_semisup),
contradicting the inline comment '# 7 models'. Supports finding: semisup-knn-not-run (bug).
Read-only; outputs to out/."""
import os, re, csv

REPO = os.path.join(os.path.dirname(__file__), "..", "code", "ZhongLIFR__TCCM-NIPS")

# Reconstruct MODEL_NAMES ordering exactly as FullExperiments.py builds it
src = open(os.path.join(REPO, "FullExperiments.py")).read()
def keys(name):
    blk = re.findall(name + r' = \{(.*?)\n\}', src, re.S)[0]
    return re.findall(r'"([^"]+)"\s*:', blk)
deep = keys("deep_models"); trans = keys("transductive_models")
forced = keys("force_inductive_models"); induc = keys(r"\ninductive_models")
addl = keys("additional_models")
MODEL_NAMES = deep + trans + induc + addl + forced

# Parse the j-loop ranges from run_semisupervise.sh
sh = open(os.path.join(REPO, "bash_files", "run_semisupervise.sh")).read()
ranges = re.findall(r"for j in \{(\d+)\.\.(\d+)\}", sh)
comments = re.findall(r"for j in \{\d+\.\.\d+\}; do\s*#\s*(.*)", sh)

forced_start = len(deep) + len(trans) + len(induc) + len(addl)  # index of first force_inductive
forced_indices = list(range(forced_start, forced_start + len(forced)))

rows = []
for (a, b), cmt in zip(ranges, comments):
    a, b = int(a), int(b)
    run = list(range(a, b + 1))
    run_models = [MODEL_NAMES[i] for i in run if i < len(MODEL_NAMES)]
    dropped = [MODEL_NAMES[i] for i in forced_indices if i not in run]
    rows.append((f"{a}..{b}", cmt.strip(), len(run), len(forced), run_models, dropped))

out = os.path.join(os.path.dirname(__file__), "out", "semisup_model_count.csv")
with open(out, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["j_range", "inline_comment", "n_run", "n_force_inductive_total", "run_models", "dropped_models"])
    for r in rows:
        w.writerow([r[0], r[1], r[2], r[3], ";".join(r[4]), ";".join(r[5])])

print(f"force_inductive indices in MODEL_NAMES: {forced_indices} -> {[MODEL_NAMES[i] for i in forced_indices]}")
for r in rows:
    print(f"  j {r[0]} (comment '{r[1]}'): runs {r[2]} of {r[3]} force_inductive models; DROPPED: {r[5]}")
print(f"Wrote {out}")
