"""Extracts every `--gt` and `--pred` pair from inference.sh (supports finding eval-wrong-gt-dataset).
Flags eval_metrics.py calls whose --gt dataset does not match the --pred dataset.
Read-only: parses the shell script text.
"""
import json, os, re

REPO = os.path.join(os.path.dirname(__file__), "..", "code", "zhengchen1999__DOVE")
sh = os.path.join(REPO, "inference.sh")
text = open(sh).read()

# Split into eval_metrics.py invocations
blocks = re.split(r"python eval_metrics\.py", text)[1:]
rows = []
for b in blocks:
    gt = re.search(r"--gt\s+(\S+)", b)
    pred = re.search(r"--pred\s+(\S+)", b)
    if not (gt and pred):
        continue
    gt_p, pred_p = gt.group(1), pred.group(1)
    # dataset name = component after datasets/test/ for gt, after results/DOVE/ for pred
    gt_ds = re.search(r"datasets/test/([^/]+)/", gt_p)
    pred_ds = re.search(r"results/DOVE/([^/]+)", pred_p)
    gt_ds = gt_ds.group(1) if gt_ds else gt_p
    pred_ds = pred_ds.group(1) if pred_ds else pred_p
    rows.append({
        "gt": gt_p, "pred": pred_p,
        "gt_dataset": gt_ds, "pred_dataset": pred_ds,
        "mismatch": gt_ds != pred_ds,
    })

mismatches = [r for r in rows if r["mismatch"]]
out = {
    "total_eval_calls_with_gt": len(rows),
    "mismatched_calls": len(mismatches),
    "rows": rows,
    "note": "Every eval_metrics.py call hardcodes --gt datasets/test/UDM10/GT; only the UDM10 call is self-consistent. The other 4 full-reference datasets (SPMCS, YouHQ40, RealVSR, MVSR4x) are scored against UDM10 GT.",
}
os.makedirs(os.path.join(os.path.dirname(__file__), "out"), exist_ok=True)
with open(os.path.join(os.path.dirname(__file__), "out", "inference_gt_paths.json"), "w") as f:
    json.dump(out, f, indent=2)
print(json.dumps(out, indent=2))
