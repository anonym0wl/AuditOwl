"""Checks that inference.sh passes UDM10 GT to eval_metrics for non-UDM10 datasets.
Supports finding `inference-sh-gt-mismatch`. Read-only: parses the shipped inference.sh."""
import os, re, json

REPO = os.path.join(os.path.dirname(__file__), "..", "code", "zhengchen1999__DOVE")
sh = os.path.join(REPO, "inference.sh")
text = open(sh).read()

# Find each eval_metrics.py invocation block: --pred results/DOVE/<NAME> and the --gt path
# Split on 'python eval_metrics.py'
blocks = text.split("python eval_metrics.py")
rows = []
for b in blocks[1:]:
    gt = re.search(r"--gt\s+(\S+)", b)
    pred = re.search(r"--pred\s+(\S+)", b)
    if gt and pred:
        rows.append((pred.group(1), gt.group(1)))

mismatches = []
for pred, gt in rows:
    # dataset name in pred path: results/DOVE/<NAME>
    m = re.search(r"results/DOVE/([^/\s]+)", pred)
    pred_ds = m.group(1) if m else pred
    gt_ds = None
    mgt = re.search(r"datasets/test/([^/\s]+)/", gt)
    gt_ds = mgt.group(1) if mgt else gt
    flag = (pred_ds != gt_ds) and (gt_ds is not None)
    if flag:
        mismatches.append({"pred_dataset": pred_ds, "gt_path": gt, "gt_dataset": gt_ds})

out = {"eval_blocks": rows, "mismatches": mismatches, "n_mismatch": len(mismatches)}
outpath = os.path.join(os.path.dirname(__file__), "out", "inference_sh_gt.json")
json.dump(out, open(outpath, "w"), indent=2)
print(json.dumps(out, indent=2))
