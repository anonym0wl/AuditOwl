"""Checks which headline long-term datasets and their precomputed Q-matrix .npy
files (referenced by scripts/OLinear/*.sh) are actually present in the repo,
supporting finding missing-headline-data-and-qmats. Read-only over code/."""
import os, re, json, glob

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "code", "jackyue1994__OLinear"))

# Parse each OLinear script for root_path, data_path, q_mat_file, q_out_mat_file, q_channel_file
scripts = sorted(glob.glob(os.path.join(REPO, "scripts", "OLinear", "*.sh")))
rows = []
for sc in scripts:
    txt = open(sc, encoding="utf-8").read()
    rp = re.search(r"--root_path\s+(\S+)", txt)
    dp = re.search(r"--data_path\s+(\S+)", txt)
    # q files may contain ${var} -> just check the directory presence of the data csv
    root = rp.group(1) if rp else None
    data = dp.group(1) if dp else None
    data_exists = None
    if root and data:
        # root like ./dataset/electricity/  -> repo-relative
        full = os.path.join(REPO, root.lstrip("./"), data)
        data_exists = os.path.isfile(full)
    rows.append({
        "script": os.path.basename(sc),
        "root_path": root,
        "data_path": data,
        "data_file_present": data_exists,
    })

# Explicitly probe a few concrete headline Q-mat filenames the ECL/ETT scripts load
probe = [
    "dataset/electricity/electricity_96_ratio0.7.npy",
    "dataset/electricity/electricity.csv",
    "dataset/traffic/traffic.csv",
    "dataset/ETT-small/ETTh1.csv",
    "dataset/Solar/solar_AL.txt",
    "dataset/PEMS/PEMS03.npz",
    "dataset/exchange_rate/exchange_rate.csv",
    "dataset/METR_LA/METR_LA.csv",
]
probe_res = {p: os.path.isfile(os.path.join(REPO, p)) for p in probe}

out = {"scripts": rows, "probe_files_present": probe_res}
with open(os.path.join(os.path.dirname(__file__), "out", "missing_data_qmat.json"), "w") as fh:
    json.dump(out, fh, indent=2)
print(json.dumps(out, indent=2))
