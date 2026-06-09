"""Checks the per-sample index mapping in eval_dover.py (supports finding dover-per-sample-offbyone).
Reproduces the loop `for i, name in enumerate(pred_names): results[name] = dover_results[i-1]`
and shows that the first sorted clip receives the LAST DOVER score.
"""
import json, os

# Simulate 5 sorted clip names and 5 DOVER scores in pred order
pred_names = ["001", "002", "003", "004", "005"]
dover_results = [0.10, 0.20, 0.30, 0.40, 0.50]  # score_for_001 ... score_for_005

# The repo's mapping (eval_dover.py lines 158-159)
results = {}
for i, name in enumerate(pred_names):
    results[name] = dover_results[i - 1]

# Correct mapping would be dover_results[i]
correct = {name: dover_results[i] for i, name in enumerate(pred_names)}

mismatches = {n: (results[n], correct[n]) for n in pred_names if results[n] != correct[n]}

avg_repo = sum(results.values()) / len(results)
avg_correct = sum(correct.values()) / len(correct)

out = {
    "repo_mapping (name -> assigned score)": results,
    "correct_mapping (name -> true score)": correct,
    "n_misaligned_samples": len(mismatches),
    "misaligned": mismatches,
    "avg_repo": round(avg_repo, 6),
    "avg_correct": round(avg_correct, 6),
    "averages_equal": abs(avg_repo - avg_correct) < 1e-12,
    "note": "First clip (001) gets the LAST clip's score; all per-sample scores are shifted by one. Average is unchanged (same multiset).",
}
os.makedirs(os.path.join(os.path.dirname(__file__), "out"), exist_ok=True)
with open(os.path.join(os.path.dirname(__file__), "out", "dover_offbyone.json"), "w") as f:
    json.dump(out, f, indent=2)
print(json.dumps(out, indent=2))
