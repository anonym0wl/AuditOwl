#!/usr/bin/env python3
"""Parses inference.sh and reports, per dataset, which --pred and --gt it pairs.

Supports finding: eval-gt-path-hardcoded-udm10. Shows every eval_metrics.py call
uses --gt datasets/test/UDM10/GT regardless of the prediction dataset, which (given
eval_metrics.py's filename-matching skip) yields 0 evaluated samples for non-UDM10 sets.
"""
import os, re, json

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "code", "zhengchen1999__DOVE"))
sh = open(os.path.join(REPO, "inference.sh"), "r").read()

# Split into command blocks by 'python ' invocations is messy; instead regex each eval block.
eval_calls = []
for m in re.finditer(r"python eval_metrics\.py(.*?)(?=\n#|\npython |\Z)", sh, re.DOTALL):
    block = m.group(1)
    gt = re.search(r"--gt\s+(\S+)", block)
    pred = re.search(r"--pred\s+(\S+)", block)
    eval_calls.append({"gt": gt.group(1) if gt else None,
                       "pred": pred.group(1) if pred else None})

all_gt_udm10 = all(c["gt"] == "datasets/test/UDM10/GT" for c in eval_calls)
non_udm10_pred_with_udm10_gt = [
    c for c in eval_calls
    if c["gt"] == "datasets/test/UDM10/GT" and c["pred"] and "UDM10" not in c["pred"]
]

result = {
    "n_eval_calls": len(eval_calls),
    "eval_calls": eval_calls,
    "all_gt_point_to_UDM10": all_gt_udm10,
    "n_mismatched_pred_vs_gt": len(non_udm10_pred_with_udm10_gt),
    "mismatched_examples": non_udm10_pred_with_udm10_gt,
}
outp = os.path.join(os.path.dirname(__file__), "out", "inference_sh_gt.json")
with open(outp, "w") as fh:
    json.dump(result, fh, indent=2)
print(json.dumps(result, indent=2))
