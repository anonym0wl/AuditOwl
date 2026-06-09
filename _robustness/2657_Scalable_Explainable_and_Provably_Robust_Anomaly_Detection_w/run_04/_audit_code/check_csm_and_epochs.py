"""Checks: (1) no CSM/Improved-Contrast-Score-Margin epoch-selection code exists in repo;
(2) summarises the per-dataset hardcoded epoch values in determine_FMAD_hyperparameters.
Supports findings: csm-epoch-selection-code-missing."""
import os, re, ast, json

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "code", "ZhongLIFR__TCCM-NIPS"))
OUT = os.path.join(os.path.dirname(__file__), "out")
os.makedirs(OUT, exist_ok=True)

# (1) grep for CSM / contrast score margin tokens across all .py files
tokens = ["csm", "contrast score", "contrast_score", "score margin", "score_margin",
          "mu_O", "presumed inlier", "candidate epoch", "epoch select", "select_epoch"]
# NOTE: "T(f)" deliberately excluded: it false-matches redirect_stdout(f) idiom.
hits = {}
for root, _, files in os.walk(REPO):
    if os.sep + ".git" in root:
        continue
    for fn in files:
        if not fn.endswith(".py"):
            continue
        p = os.path.join(root, fn)
        try:
            txt = open(p, encoding="utf-8", errors="ignore").read().lower()
        except Exception:
            continue
        for tok in tokens:
            if tok.lower() in txt:
                hits.setdefault(tok, []).append(os.path.relpath(p, REPO))

# (2) parse the hardcoded epoch dict from FMAD/functions.py
fpath = os.path.join(REPO, "FMAD", "functions.py")
src = open(fpath).read()
epochs = re.findall(r'epoch_size\s*=\s*(\d+)', src)
epochs = [int(e) for e in epochs]

result = {
    "csm_token_hits": hits,
    "csm_code_found": bool(hits),
    "num_hardcoded_epoch_branches": len(epochs),
    "epoch_values_min": min(epochs) if epochs else None,
    "epoch_values_max": max(epochs) if epochs else None,
    "distinct_epoch_values": sorted(set(epochs)),
}
with open(os.path.join(OUT, "csm_and_epochs.json"), "w") as f:
    json.dump(result, f, indent=2)
print(json.dumps(result, indent=2))
