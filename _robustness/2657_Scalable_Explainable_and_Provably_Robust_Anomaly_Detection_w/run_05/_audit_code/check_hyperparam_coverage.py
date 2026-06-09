"""Check determine_FMAD_hyperparameters covers all 47 datasets (else UnboundLocalError)."""
import os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__),"..","code","ZhongLIFR__TCCM-NIPS"))
sys.path.insert(0, ROOT)
os.chdir(ROOT)
from FMAD.functions import determine_FMAD_hyperparameters

datasets = []
for split in ["small","medium","high_dim","large"]:
    d = os.path.join(ROOT,"datasets",split)
    for f in os.listdir(d):
        if f.endswith(".npz"): datasets.append(f[:-4])

bad = []
ok = 0
for dn in sorted(datasets):
    try:
        h = determine_FMAD_hyperparameters(dn)
        if h.get("epochs") is None: bad.append((dn,"epochs=None"))
        else: ok+=1
    except Exception as e:
        bad.append((dn, repr(e)))

print(f"datasets covered OK: {ok}/{len(datasets)}")
print("PROBLEMS:", bad if bad else "NONE")
# also check the contamination datasets (run via determine too)
contam = [f[:-4] for f in os.listdir(os.path.join(ROOT,"datasets","contamination")) if f.endswith(".npz")]
print("contamination datasets:", contam)
for dn in contam:
    try:
        determine_FMAD_hyperparameters(dn)
    except Exception as e:
        print("  CONTAM PROBLEM", dn, repr(e))
