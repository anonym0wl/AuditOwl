"""Checks every ADBench dataset name maps to a defined epoch in determine_FMAD_hyperparameters; supports tccm-undefined-epoch-crash finding. Read-only."""
import os, sys, re

REPO = os.path.join(os.path.dirname(__file__), "..", "code", "ZhongLIFR__TCCM-NIPS")
REPO = os.path.abspath(REPO)

# Reimplement determine_FMAD_hyperparameters logic by importing it, but without torch deps:
# parse the source's elif branch substrings instead, to avoid importing torch.
src_path = os.path.join(REPO, "FMAD", "functions.py")
with open(src_path) as f:
    src = f.read()

# Extract the substrings tested in `if "X" in dataset_name` branches
keys = re.findall(r'"([^"]+)" in dataset_name', src)

# Gather dataset basenames
ds = []
for sub in ["small", "medium", "high_dim", "large"]:
    d = os.path.join(REPO, "datasets", sub)
    if os.path.isdir(d):
        for fn in os.listdir(d):
            if fn.endswith(".npz"):
                ds.append(os.path.splitext(fn)[0])

unmatched = []
for name in sorted(ds):
    lower = name.lower()
    if not any(k in lower for k in keys):
        unmatched.append(name)

out = os.path.join(os.path.dirname(__file__), "out", "hyperparam_coverage.txt")
with open(out, "w") as f:
    f.write(f"n_datasets={len(ds)}\n")
    f.write(f"n_branch_keys={len(keys)}\n")
    f.write(f"unmatched_datasets={unmatched}\n")
    # Note: when unmatched, epoch_size is never assigned -> UnboundLocalError at return.
print(f"n_datasets={len(ds)}")
print(f"n_branch_keys={len(keys)}")
print(f"unmatched_datasets={unmatched}")
print(f"branch_keys={sorted(keys)}")
