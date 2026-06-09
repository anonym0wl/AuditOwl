"""Checks that the per-dataset epoch values hardcoded in FMAD/functions.py:determine_FMAD_hyperparameters
match Table 5 of the paper, and that NO label-free / CSM epoch-selection logic exists in the repo.
Supports findings: epoch-selection-protocol-missing, hardcoded-per-dataset-epochs (difference/methodology).
Read-only; outputs to out/."""
import os, re, csv

REPO = os.path.join(os.path.dirname(__file__), "..", "code", "ZhongLIFR__TCCM-NIPS")
FUNCS = os.path.join(REPO, "FMAD", "functions.py")

# Epoch values transcribed from paper Table 5 (key: lowercased dataset token used in code branch)
TABLE5 = {
    "census": 5, "backdoor": 200, "campaign": 50, "mnist": 500, "speech": 500,
    "optdigits": 2000, "spambase": 5000, "musk": 5, "internetads": 50,
    "donors": 30, "http": 100, "cover": 10, "fraud": 75, "skin": 110, "celeba": 2,
    "smtp": 2, "aloi": 100, "shuttle": 200, "magic.gamma": 10, "mammography": 20,
    "annthyroid": 2000, "pendigits": 1000, "satellite": 10, "landsat": 6,
    "satimage-2": 5, "pageblocks": 1800, "wilt": 20, "thyroid": 10, "waveform": 580,
    "cardiotocography": 1, "fault": 5000, "cardio": 2000, "letter": 50, "yeast": 130,
    "vowels": 20, "pima": 5, "breastw": 1, "wdbc": 2, "ionosphere": 10, "stamps": 200,
    "vertebral": 25, "wbc": 1, "glass": 200, "wpbc": 6, "lymphography": 3, "wine": 20,
    "hepatitis": 1,
}

src = open(FUNCS).read()
# Parse the elif chain: capture token and epoch_size
code_epochs = {}
pat = re.compile(r'(?:if|elif)\s+"([^"]+)"\s+in\s+dataset_name:\s*\n\s*epoch_size\s*=\s*(\d+)')
for m in pat.finditer(src):
    code_epochs[m.group(1)] = int(m.group(2))

rows = []
mismatch = 0
missing_in_code = 0
for k, paper_v in TABLE5.items():
    code_v = code_epochs.get(k, None)
    status = "MATCH" if code_v == paper_v else ("MISSING_IN_CODE" if code_v is None else "MISMATCH")
    if status == "MISMATCH":
        mismatch += 1
    if status == "MISSING_IN_CODE":
        missing_in_code += 1
    rows.append((k, paper_v, code_v, status))

# Check for any CSM / contrast-score / epoch-selection logic anywhere in the repo
csm_hits = []
for root, _, files in os.walk(REPO):
    if "datasets" in root or ".git" in root:
        continue
    for fn in files:
        if fn.endswith(".py"):
            p = os.path.join(root, fn)
            txt = open(p, errors="ignore").read().lower()
            for kw in ["csm", "contrast score", "contrast_score", "epoch_select",
                       "select_epoch", "candidate epoch", "candidate_epoch"]:
                if kw in txt:
                    csm_hits.append((os.path.relpath(p, REPO), kw))

out = os.path.join(os.path.dirname(__file__), "out", "table5_epochs.csv")
with open(out, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["dataset_token", "paper_table5_epochs", "code_epochs", "status"])
    for r in rows:
        w.writerow(r)

print(f"Table5 entries checked: {len(TABLE5)}")
print(f"  MATCH: {sum(1 for r in rows if r[3]=='MATCH')}")
print(f"  MISMATCH: {mismatch}")
print(f"  MISSING_IN_CODE: {missing_in_code}")
print(f"CSM / epoch-selection logic hits in repo .py files: {len(csm_hits)} -> {csm_hits}")
print(f"Wrote {out}")
