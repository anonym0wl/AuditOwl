"""Checks: eval_dover.py assigns dover_results[i-1] to pred_names[i], so the
per-video score is shifted by one (name i gets the i-1 score; name 0 gets the
LAST score). Demonstrates the misassignment and that the mean is unaffected.
Supports finding dover-per-video-off-by-one. Pure logic reproduction; read-only.
Output: out/dover_offbyone.txt
"""
import os
out_dir = os.path.join(os.path.dirname(__file__), "out"); os.makedirs(out_dir, exist_ok=True)

# Simulate the exact loop from eval_dover.py lines 156-164.
pred_names = [f"vid{j:02d}" for j in range(5)]
dover_results = [10, 20, 30, 40, 50]  # hypothetical per-video scores in pred order

results = {}
for i, name in enumerate(pred_names):
    results[name] = dover_results[i - 1]   # the buggy line

import statistics
correct = {name: dover_results[i] for i, name in enumerate(pred_names)}

lines = []
lines.append("pred_names order : " + str(pred_names))
lines.append("dover_results    : " + str(dover_results))
lines.append("buggy assignment : " + str(results))
lines.append("correct assignment: " + str(correct))
lines.append(f"vid00 assigned    : {results['vid00']} (should be {correct['vid00']}; got last element)")
lines.append(f"mean(buggy)={statistics.mean(results.values())}  mean(correct)={statistics.mean(correct.values())}")
lines.append("=> per-video scores are MISASSIGNED (shifted by one); the AVERAGE is unaffected (same multiset).")
result = "\n".join(lines)
print(result)
with open(os.path.join(out_dir, "dover_offbyone.txt"), "w") as f:
    f.write(result + "\n")
