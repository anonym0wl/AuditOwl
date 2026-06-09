"""Inventory of repo completeness vs paper claims (read-only static scan).

Supports findings: missing-eval-inference-code, missing-rtheta-restoration-net,
missing-dependency-spec. Saves out/completeness.csv.
"""
import os, glob, re, csv

ROOT = os.path.join(os.path.dirname(__file__), "..", "code", "lyd-2022__Latent-Harmony")
ROOT = os.path.abspath(ROOT)

py = [p for p in glob.glob(os.path.join(ROOT, "**", "*.py"), recursive=True)
      if "__pycache__" not in p]

# dependency spec files
dep_files = []
for pat in ["requirements*.txt", "setup.py", "setup.cfg", "pyproject.toml",
            "environment*.yml", "environment*.yaml", "Pipfile", "conda*.yml"]:
    dep_files += glob.glob(os.path.join(ROOT, pat))

# eval/test/inference entrypoints
eval_files = [p for p in py if re.search(r"(test|infer|eval|metric_main|calc_)",
                                         os.path.basename(p), re.I)
              and "metrics/" not in p.replace("\\", "/")]

# restoration network Rtheta references (class definitions or net_r usage)
rtheta_hits = []
for p in py:
    with open(p) as f:
        src = f.read()
    if re.search(r"net_r\b|self\.net_g_r\b|restoration_net|RestorationNet|class\s+R_?theta", src):
        rtheta_hits.append(os.path.relpath(p, ROOT))

# main entrypoints
main_files = []
for p in py:
    with open(p) as f:
        if "__main__" in f.read():
            main_files.append(os.path.relpath(p, ROOT))

out_dir = os.path.join(os.path.dirname(__file__), "out")
os.makedirs(out_dir, exist_ok=True)
rows = [
    ["n_python_files_no_pycache", str(len(py))],
    ["dependency_spec_files", ";".join(os.path.basename(x) for x in dep_files) or "NONE"],
    ["eval_test_infer_scripts", ";".join(os.path.relpath(x, ROOT) for x in eval_files) or "NONE"],
    ["rtheta_restoration_net_refs", ";".join(rtheta_hits) or "NONE"],
    ["main_entrypoints", ";".join(main_files)],
]
with open(os.path.join(out_dir, "completeness.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["key", "value"])
    w.writerows(rows)
for r in rows:
    print(r[0], "=>", r[1])
