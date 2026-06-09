"""Checks that every dataset .npz file name resolves to a branch in
determine_FMAD_hyperparameters (else epoch_size is undefined -> UnboundLocalError /
returns garbage). Supports finding: epoch-hparam-no-default-branch."""
import os, sys, json

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "code", "ZhongLIFR__TCCM-NIPS"))
OUT = os.path.join(os.path.dirname(__file__), "out")
os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, REPO)

from FMAD.functions import determine_FMAD_hyperparameters

names = []
for root, _, files in os.walk(os.path.join(REPO, "datasets")):
    if "contamination" in root:
        continue
    for fn in files:
        if fn.endswith(".npz"):
            names.append(fn[:-4])
names = sorted(set(names))

resolved, unresolved = {}, []
for n in names:
    try:
        hp = determine_FMAD_hyperparameters(n)
        # the function builds a dict referencing epoch_size etc.; if no branch
        # matched, those locals are undefined -> NameError/UnboundLocalError.
        resolved[n] = hp
    except Exception as e:
        unresolved.append({"dataset": n, "error": f"{type(e).__name__}: {e}"})

result = {
    "n_datasets": len(names),
    "n_resolved": len(resolved),
    "n_unresolved": len(unresolved),
    "unresolved": unresolved,
}
with open(os.path.join(OUT, "epoch_coverage.json"), "w") as f:
    json.dump(result, f, indent=2)
print(json.dumps(result, indent=2))
