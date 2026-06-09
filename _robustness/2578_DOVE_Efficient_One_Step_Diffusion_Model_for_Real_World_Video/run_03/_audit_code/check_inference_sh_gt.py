"""Check that inference.sh passes the wrong --gt (always UDM10/GT) for non-UDM10 eval blocks (supports finding: eval-gt-path-mismatch)."""
import os, re, json

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "code", "zhengchen1999__DOVE"))
OUT = os.path.join(os.path.dirname(__file__), "out")
os.makedirs(OUT, exist_ok=True)

sh = os.path.join(REPO, "inference.sh")
with open(sh) as fh:
    lines = fh.readlines()

# Pair each --pred results/DOVE/<DATASET> with the nearest preceding --gt line.
results = []
last_gt = None
for i, line in enumerate(lines, 1):
    m_gt = re.search(r"--gt\s+(\S+)", line)
    if m_gt:
        last_gt = (i, m_gt.group(1))
    m_pred = re.search(r"--pred\s+results/DOVE/(\S+)", line)
    if m_pred and last_gt is not None:
        pred_ds = m_pred.group(1)
        gt_line, gt_path = last_gt
        gt_ds = gt_path.split("/")[2] if gt_path.startswith("datasets/test/") else gt_path
        results.append({
            "eval_pred_dataset": pred_ds,
            "eval_pred_line": i,
            "gt_path": gt_path,
            "gt_line": gt_line,
            "gt_dataset": gt_ds,
            "mismatch": (gt_ds != pred_ds),
        })
        last_gt = None  # consume

report = {"pairs": results,
          "num_mismatches": sum(1 for r in results if r["mismatch"]),
          "num_pairs": len(results)}
with open(os.path.join(OUT, "inference_sh_gt.json"), "w") as fh:
    json.dump(report, fh, indent=2)
print(json.dumps(report, indent=2))
