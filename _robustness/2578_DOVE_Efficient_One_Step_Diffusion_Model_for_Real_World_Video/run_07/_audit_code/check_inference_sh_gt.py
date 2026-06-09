"""Check: inference.sh passes --gt datasets/test/UDM10/GT to eval_metrics.py for EVERY
dataset (SPMCS, YouHQ40, RealVSR, MVSR4x, VideoLQ), not each dataset's own GT.
Supports finding inference-sh-wrong-gt. Read-only parse of inference.sh."""
import os, re

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "code", "zhengchen1999__DOVE"))
sh = open(os.path.join(REPO, "inference.sh"), encoding="utf-8").read()

# Find eval_metrics blocks: capture the --pred and the --gt
blocks = re.split(r"python eval_metrics.py", sh)[1:]
rows = []
for b in blocks:
    gt = re.search(r"--gt\s+(\S+)", b)
    pred = re.search(r"--pred\s+(\S+)", b)
    rows.append((pred.group(1) if pred else None, gt.group(1) if gt else None))

print("pred_dir, gt_dir per eval_metrics.py call in inference.sh:")
bad = 0
for pred, gt in rows:
    pred_ds = pred.split("/")[-1] if pred else "?"
    gt_ds = gt.split("/")[-2] if gt and "/" in gt else "?"
    flag = "" if pred_ds == gt_ds else "  <-- GT dataset != pred dataset"
    if flag:
        bad += 1
    print(f"  pred={pred}  gt={gt}{flag}")
print(f"\nMismatched GT calls: {bad} of {len(rows)}")
