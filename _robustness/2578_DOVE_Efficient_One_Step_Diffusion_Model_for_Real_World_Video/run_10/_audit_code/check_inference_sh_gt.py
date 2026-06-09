"""Checks: inference.sh passes --gt datasets/test/UDM10/GT for every dataset eval.
Supports finding eval-gt-hardcoded-udm10. Read-only; parses the shell script.
Output: out/inference_sh_gt.txt
"""
import os, re

REPO = os.path.join(os.path.dirname(__file__), "..", "code", "zhengchen1999__DOVE")
sh = os.path.join(REPO, "inference.sh")
out_dir = os.path.join(os.path.dirname(__file__), "out")
os.makedirs(out_dir, exist_ok=True)

with open(sh) as f:
    text = f.read()

# Find each eval_metrics.py invocation block: capture the --pred and --gt args.
# The script uses backslash line continuations. Normalize.
norm = text.replace("\\\n", " ")
blocks = re.findall(r"python eval_metrics\.py.*?(?=python |\Z)", norm, flags=re.S)

lines = []
for b in blocks:
    gt = re.search(r"--gt\s+(\S+)", b)
    pred = re.search(r"--pred\s+(\S+)", b)
    gt = gt.group(1) if gt else "(none)"
    pred = pred.group(1) if pred else "(none)"
    mismatch = "MISMATCH" if ("UDM10" in gt and "UDM10" not in pred) else "ok"
    lines.append(f"pred={pred:35s} gt={gt:30s} {mismatch}")

result = "\n".join(lines)
print(result)
n_mismatch = sum(1 for l in lines if l.endswith("MISMATCH"))
print(f"\nTotal eval_metrics.py calls: {len(blocks)}; GT-pred dataset mismatches: {n_mismatch}")

with open(os.path.join(out_dir, "inference_sh_gt.txt"), "w") as f:
    f.write(result + f"\n\nTotal calls: {len(blocks)}; mismatches: {n_mismatch}\n")
