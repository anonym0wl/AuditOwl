"""Check: eval_dover.py maps DOVER scores to video names with an off-by-one shift
(results[name] = dover_results[i-1]). Demonstrates that per-sample assignment is a
cyclic shift (first name gets last score). Supports finding dover-score-name-misalign.
Read-only: reproduces the assignment logic only, no repo files modified."""
pred_names = ["001", "002", "003", "004"]          # sorted names
dover_results = [0.10, 0.20, 0.30, 0.40]            # scores in dover() order (== sorted pred order)

# Exact logic from eval_dover.py lines 158-159
results = {}
for i, name in enumerate(pred_names):
    results[name] = dover_results[i - 1]

print("pred_names      :", pred_names)
print("dover_results   :", dover_results)
print("assigned mapping:", results)
print()
correct = {n: dover_results[i] for i, n in enumerate(pred_names)}
print("correct mapping :", correct)
print()
mismatched = [n for n in pred_names if results[n] != correct[n]]
print("names with WRONG score:", mismatched)
print("mean(assigned) == mean(correct):",
      round(sum(results.values()) / len(results), 6) == round(sum(correct.values()) / len(correct), 6))
