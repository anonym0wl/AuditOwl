"""Runs determine_FMAD_hyperparameters() on all 47 actual dataset filenames to confirm
every dataset resolves to a defined epoch value (no UnboundLocalError from substring
collisions or unmatched names). Supports a no-finding 'looks fine' note. Read-only."""
import os, sys, csv

REPO = os.path.join(os.path.dirname(__file__), "..", "code", "ZhongLIFR__TCCM-NIPS")
sys.path.insert(0, REPO)
from FMAD.functions import determine_FMAD_hyperparameters  # noqa

names = []
for grp in ["small", "medium", "high_dim", "large"]:
    d = os.path.join(REPO, "datasets", grp)
    for fn in os.listdir(d):
        if fn.endswith(".npz"):
            names.append(fn[:-4])
names = sorted(set(names))

rows, errors = [], 0
for n in names:
    try:
        hp = determine_FMAD_hyperparameters(n)
        # Defined only if 'epochs' key resolved to an int (function would raise/return junk otherwise)
        ok = isinstance(hp.get("epochs"), int)
        rows.append((n, hp.get("epochs"), hp.get("batch_size"), "OK" if ok else "UNDEFINED"))
        if not ok:
            errors += 1
    except Exception as e:
        rows.append((n, None, None, f"ERROR: {type(e).__name__}: {e}"))
        errors += 1

out = os.path.join(os.path.dirname(__file__), "out", "hyperparam_dispatch.csv")
with open(out, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["dataset", "epochs", "batch_size", "status"])
    w.writerows(rows)

print(f"Datasets tested: {len(names)}; errors/undefined: {errors}")
for r in rows:
    if not str(r[3]).startswith("OK"):
        print("  PROBLEM:", r)
print(f"Wrote {out}")
