#!/usr/bin/env python3
"""Demonstrates the off-by-one per-sample mapping in eval_dover.py line ~158-159.

Supports finding: dover-per-sample-offbyone. Reproduces the assignment logic
`results[name] = dover_results[i-1]` over a sorted name list to show the first
name receives the LAST score (i=0 -> index -1).
"""
import json, os

# Simulate: pred_names sorted, dover_results aligned to sorted order (the normal expectation).
pred_names = ["001", "002", "003", "004"]
dover_results = [0.10, 0.20, 0.30, 0.40]  # imagine these are in sorted-name order

# Code under audit:
#   for i, name in enumerate(pred_names):
#       results[name] = dover_results[i-1]
buggy = {}
for i, name in enumerate(pred_names):
    buggy[name] = dover_results[i - 1]

correct = {name: dover_results[i] for i, name in enumerate(pred_names)}

mismatch = {n: (buggy[n], correct[n]) for n in pred_names if buggy[n] != correct[n]}

result = {
    "buggy_mapping": buggy,
    "correct_mapping": correct,
    "per_sample_mismatches": mismatch,
    "first_name_gets_last_score": buggy[pred_names[0]] == dover_results[-1],
    "n_mismatched_of_n": f"{len(mismatch)}/{len(pred_names)}",
    "note": "Average over results.values() is unaffected (same multiset); per-sample names are shifted by one.",
}
outp = os.path.join(os.path.dirname(__file__), "out", "dover_offbyone.json")
with open(outp, "w") as fh:
    json.dump(result, fh, indent=2)
print(json.dumps(result, indent=2))
