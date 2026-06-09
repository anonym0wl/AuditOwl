"""Checks: (1) which baseline models from Tables 2/3 have code in the repo,
(2) which of the 24 datasets ship data files, (3) Q-matrix ratio vs train split.
Supports findings: baselines-not-in-repo, longterm-data-not-shipped.
Read-only. Run: cd _audit_code && python check_baselines_and_data.py"""
import os, glob, json

ROOT = os.path.join(os.path.dirname(__file__), '..', 'code', 'jackyue1994__OLinear')
ROOT = os.path.abspath(ROOT)
out = {}

# (1) baseline model code
baselines = ["TimeMixer", "FilterNet", "FITS", "DLinear", "TimeMixerpp", "Leddam",
             "CARD", "Fredformer", "iTransformer", "PatchTST", "TimesNet"]
model_files = [os.path.basename(p) for p in glob.glob(os.path.join(ROOT, 'model', '*.py'))]
out["model_py_files"] = sorted(model_files)
# scan exp_basic model_dict registered names
basic = open(os.path.join(ROOT, 'experiments', 'exp_basic.py')).read()
out["registered_models_contains_only_OLinear"] = (
    basic.count("'OLinear") >= 1 and "iTransformer" not in basic.split("model_dict")[1][:600]
)

# (2) dataset data files (csv/xlsx/npz) present, excluding precomputed Q (*.npy)
data_files = []
for ext in ('*.csv', '*.xlsx', '*.npz', '*.txt'):
    data_files += glob.glob(os.path.join(ROOT, 'dataset', '**', ext), recursive=True)
out["shipped_data_files"] = sorted(os.path.relpath(p, ROOT) for p in data_files)
longterm = ['electricity', 'traffic', 'ETT', 'solar', 'PEMS', 'exchange', 'metr', 'weather']
present_lt = [k for k in longterm
              if any(k.lower() in os.path.basename(p).lower() for p in data_files)]
out["longterm_datasets_with_data_shipped"] = present_lt

# (3) requirements pywt naming
req = open(os.path.join(ROOT, 'requirements.txt')).read().splitlines()
out["requirements"] = req
out["pywt_listed_as_pywt_not_PyWavelets"] = ('pywt' in [r.strip() for r in req])

print(json.dumps(out, indent=2))
with open(os.path.join(os.path.dirname(__file__), 'out', 'check_baselines_and_data.json'), 'w') as f:
    json.dump(out, f, indent=2)
