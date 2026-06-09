"""Maps paper artefacts to repo computing code (supports baseline-code-missing and section6-classifier-missing).
Read-only: greps the supplemental package for (a) the 7 similarity metrics, (b) the 3 utility metrics,
(c) any baseline generator (TimeVAE/TimeVQVAE/RTSGAN/SDEGAN/LS4), (d) the Section-6 kNN classifier.
"""
import os, re, json, glob

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CODE = os.path.join(ROOT, "code", "SDForger__neurips_supplemental")

py_files = glob.glob(os.path.join(CODE, "**", "*.py"), recursive=True)
blob = ""
for f in py_files:
    blob += "\n" + open(f, errors="ignore").read()

def present(patterns):
    return any(re.search(p, blob, re.I) for p in patterns)

checks = {
    # Table 1 similarity metrics (SDForger own values)
    "MDD (calculate_mdd)": present([r"def calculate_mdd"]),
    "ACD (calculate_acd)": present([r"def calculate_acd"]),
    "SD (calculate_sd)": present([r"def calculate_sd"]),
    "KD (calculate_kd)": present([r"def calculate_kd"]),
    "ED (calculate_ed)": present([r"def calculate_ed"]),
    "DTW (calculate_dtw)": present([r"def calculate_dtw"]),
    "SHR (calculate_shapelet_recons_err)": present([r"def calculate_shapelet_recons_err"]),
    # Table 2 utility metrics
    "RMSE (compute_rmse)": present([r"def compute_rmse"]),
    "MASE (compute_mase)": present([r"def compute_mase"]),
    "WQL (compute_wql)": present([r"def compute_wql"]),
    # Baseline GENERATORS needed for Table 1 & Table 2 baseline rows
    "Baseline generator TimeVAE": present([r"timevae", r"time_vae"]),
    "Baseline generator TimeVQVAE": present([r"timevqvae", r"time_vqvae", r"vqvae"]),
    "Baseline generator RTSGAN": present([r"rtsgan", r"rts_gan"]),
    "Baseline generator SDEGAN": present([r"sdegan", r"sde_gan"]),
    "Baseline generator LS4": present([r"\bls4\b"]),
    # Section 6 classifier for the 0.81 accuracy headline
    "Section-6 kNN classifier / accuracy": present([r"neighbor", r"\bknn\b", r"accuracy_score",
                                                     r"skfda", r"KNeighbors"]),
}

out = {k: ("PRESENT" if v else "MISSING") for k, v in checks.items()}
outdir = os.path.join(os.path.dirname(__file__), "out")
os.makedirs(outdir, exist_ok=True)
with open(os.path.join(outdir, "traceability.json"), "w") as f:
    json.dump(out, f, indent=2)
# Also emit a CSV (one artefact per row) so findings can cite out/check_*.csv + csv_row.
with open(os.path.join(outdir, "traceability.csv"), "w") as f:
    f.write("row,artefact,status\n")
    for i, (k, v) in enumerate(out.items()):
        f.write(f"{i},{k},{v}\n")
print(json.dumps(out, indent=2))
print("\nPython files scanned:", len(py_files))
