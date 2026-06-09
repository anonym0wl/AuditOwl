"""Static checks (no repo execution): missing basicsr.test module import,
unregistered 'RAVAE' arch required by stage-2 config/RAVAEHFLora, and
presence of reproducibility artefacts. Supports findings:
import-missing-test-module, stage2-ravae-arch-unregistered, repro-artefacts-missing."""
import ast
import os
import re
import csv

REPO = os.path.join(os.path.dirname(__file__), "..", "code", "lyd-2022__Latent-Harmony")
REPO = os.path.abspath(REPO)
OUT = os.path.join(os.path.dirname(__file__), "out")
os.makedirs(OUT, exist_ok=True)

rows = []

# --- (1) basicsr/__init__.py imports .test but basicsr/test.py is absent ---
init_path = os.path.join(REPO, "basicsr", "__init__.py")
with open(init_path) as f:
    init_src = f.read()
imports_test = bool(re.search(r"^\s*from\s+\.test\s+import", init_src, re.M))
test_py_exists = os.path.isfile(os.path.join(REPO, "basicsr", "test.py"))
rows.append({
    "check": "init_imports_dot_test",
    "result": str(imports_test),
    "verdict": "from .test import * present in basicsr/__init__.py" if imports_test else "absent",
})
rows.append({
    "check": "basicsr_test_py_exists",
    "result": str(test_py_exists),
    "verdict": "basicsr/test.py missing -> import basicsr raises ModuleNotFoundError" if (imports_test and not test_py_exists) else "ok",
})

# --- (2) RAVAE arch registration vs requirement ---
# Collect all @ARCH_REGISTRY.register() class names across basicsr/archs/*.py
registered = set()
archs_dir = os.path.join(REPO, "basicsr", "archs")
for root, _, files in os.walk(archs_dir):
    for fn in files:
        if not fn.endswith(".py"):
            continue
        with open(os.path.join(root, fn)) as f:
            src = f.read()
        try:
            tree = ast.parse(src)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for dec in node.decorator_list:
                    # match ARCH_REGISTRY.register() call decorator
                    target = dec.func if isinstance(dec, ast.Call) else dec
                    name = ""
                    if isinstance(target, ast.Attribute):
                        name = target.attr
                    if name == "register":
                        registered.add(node.name)

ravae_registered = "RAVAE" in registered
# stage2 config requires vae_config.type: RAVAE
cfg2 = os.path.join(REPO, "configs", "stage2_hflora.yml")
with open(cfg2) as f:
    cfg2_src = f.read()
cfg_requires_ravae = bool(re.search(r"type:\s*RAVAE\b", cfg2_src))
rows.append({
    "check": "arch_registered_names",
    "result": ",".join(sorted(registered)),
    "verdict": "RAVAE_EQ registered but RAVAE NOT registered" if (not ravae_registered and "RAVAE_EQ" in registered) else "see result",
})
rows.append({
    "check": "stage2_config_requires_RAVAE_type",
    "result": str(cfg_requires_ravae),
    "verdict": "stage2_hflora.yml sets vae_config.type: RAVAE" if cfg_requires_ravae else "no",
})
rows.append({
    "check": "RAVAE_resolvable",
    "result": str(ravae_registered),
    "verdict": "ARCH_REGISTRY.get('RAVAE') raises KeyError (RAVAE never defined)" if not ravae_registered else "ok",
})

# --- (3) reproducibility artefacts presence ---
def any_match(patterns):
    for root, _, files in os.walk(REPO):
        if "__pycache__" in root:
            continue
        for fn in files:
            for p in patterns:
                if re.search(p, fn, re.I):
                    return os.path.relpath(os.path.join(root, fn), REPO)
    return ""

artefacts = {
    "requirements_or_env": [r"^requirements.*\.txt$", r"^environment.*\.ya?ml$", r"^pyproject", r"^setup\.py$"],
    "test_or_inference_script": [r"test", r"infer", r"eval", r"demo"],
    "pretrained_weights": [r"\.pth$", r"\.ckpt$", r"\.pt$", r"\.safetensors$"],
    "readme_with_instructions": [r"^readme"],
}
for label, pats in artefacts.items():
    hit = any_match(pats)
    rows.append({
        "check": f"artefact::{label}",
        "result": hit if hit else "NONE",
        "verdict": "present" if hit else "ABSENT",
    })

# README content length (only "# Latent-Harmony")
readme = os.path.join(REPO, "README.md")
readme_txt = open(readme).read().strip() if os.path.isfile(readme) else ""
rows.append({
    "check": "readme_content",
    "result": repr(readme_txt),
    "verdict": "README is a one-line title only; no install/data/run instructions, no results table" if len(readme_txt) < 60 else "see result",
})

# datasets present?
ds_dir = os.path.join(REPO, "datasets")
rows.append({
    "check": "datasets_dir_present",
    "result": str(os.path.isdir(ds_dir)),
    "verdict": "no datasets/ dir; configs point to ./datasets/{train,val} which do not exist" if not os.path.isdir(ds_dir) else "present",
})

out_csv = os.path.join(OUT, "import_and_registry.csv")
with open(out_csv, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["check", "result", "verdict"])
    w.writeheader()
    for r in rows:
        w.writerow(r)

for r in rows:
    print(f"{r['check']:38s} | {r['result'][:60]:60s} | {r['verdict']}")
print(f"\nWrote {out_csv}")
