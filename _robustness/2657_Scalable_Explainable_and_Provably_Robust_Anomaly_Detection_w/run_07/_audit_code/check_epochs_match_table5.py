"""Confirms the hardcoded per-dataset epochs in FMAD/functions.determine_FMAD_hyperparameters
equal the #Epochs reported in paper Table 5. Supports finding: missing-csm-epoch-selection
(the *values* match the paper, so what is absent is the unsupervised CSM *selection procedure*,
not the numbers). Read-only. Output -> out/epochs_match_table5.csv
"""
import os, sys, csv

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "code", "ZhongLIFR__TCCM-NIPS"))
sys.path.insert(0, REPO)
# import the function directly (no torch needed)
import importlib.util
spec = importlib.util.spec_from_file_location("fmad_functions", os.path.join(REPO, "FMAD", "functions.py"))
# functions.py imports torch; guard by importing torch-free copy via exec of just the function is complex.
# Simpler: parse the function's elif ladder is overkill; we re-implement by reading literals from source.

import re
src = open(os.path.join(REPO, "FMAD", "functions.py")).read()
# capture blocks:  "<name>" in dataset_name: ... epoch_size = N
code_epochs = {}
pat = re.compile(r'"([^"]+)"\s+in\s+dataset_name:\s*\n\s*epoch_size\s*=\s*(\d+)')
for name, ep in pat.findall(src):
    code_epochs[name.lower()] = int(ep)

# Paper Table 5 epochs (transcribed from paper_text.txt lines ~5281-5460; high_dim+large subset that is unambiguous)
table5 = {
    "census": 5, "backdoor": 200, "campaign": 50, "mnist": 500, "speech": 500,
    "optdigits": 2000, "spambase": 5000, "musk": 5, "internetads": 50,
    "donors": 30, "http": 100, "cover": 10,
}

rows = []
for ds, paper_ep in table5.items():
    code_ep = code_epochs.get(ds, None)
    rows.append({"dataset": ds, "paper_table5_epochs": paper_ep,
                 "code_hardcoded_epochs": code_ep,
                 "match": "YES" if code_ep == paper_ep else "NO"})

out = os.path.join(os.path.dirname(__file__), "out", "epochs_match_table5.csv")
with open(out, "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
    w.writeheader(); w.writerows(rows)
for r in rows:
    print(r)
print("All match:", all(r["match"] == "YES" for r in rows))
print("Wrote", out)
