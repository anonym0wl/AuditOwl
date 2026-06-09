"""Reproduces eval_dover.py's `results[name] = dover_results[i-1]` mapping to show the
per-sample score is shifted by one (name[0] gets the LAST video's score), while the
mean is unchanged. Supports finding `dover-per-sample-offbyone`. Read-only / self-contained."""
import json, os
import numpy as np

# Simulate dover() returning per-video scores in pred_names order
pred_names = ["001", "002", "003", "004", "005"]
dover_results = [10.0, 20.0, 30.0, 40.0, 50.0]  # aligned to pred_names index i

# Buggy mapping from eval_dover.py lines 158-159
results = {}
for i, name in enumerate(pred_names):
    results[name] = dover_results[i - 1]

correct = {name: dover_results[i] for i, name in enumerate(pred_names)}

out = {
    "buggy_per_sample": results,
    "correct_per_sample": correct,
    "per_sample_matches_correct": bool(results == correct),
    "buggy_mean": float(np.mean(list(results.values()))),
    "correct_mean": float(np.mean(list(correct.values()))),
    "mean_unchanged": bool(abs(np.mean(list(results.values())) - np.mean(list(correct.values()))) < 1e-9),
}
outpath = os.path.join(os.path.dirname(__file__), "out", "dover_offbyone.json")
json.dump(out, open(outpath, "w"), indent=2)
print(json.dumps(out, indent=2))
