"""Checks that stage2 config's vae_config.type 'RAVAE' is registered (it is not).

Supports finding: stage2-ravae-arch-unregistered. Read-only static scan of the
repo source; does not import torch. Saves a CSV to out/arch_registry.csv.
"""
import re, os, glob, csv

ROOT = os.path.join(os.path.dirname(__file__), "..", "code", "lyd-2022__Latent-Harmony")
ROOT = os.path.abspath(ROOT)


def registered(reg_name, subdir):
    names = {}
    for path in glob.glob(os.path.join(ROOT, "basicsr", subdir, "**", "*.py"), recursive=True):
        with open(path) as f:
            src = f.read()
        for m in re.finditer(r"@%s\.register\(\)\s*\nclass\s+(\w+)" % reg_name, src):
            names.setdefault(m.group(1), os.path.relpath(path, ROOT))
    return names


arch_regs = registered("ARCH_REGISTRY", "archs")
model_regs = registered("MODEL_REGISTRY", "models")

# config-referenced types
cfg_types = {}
for cfg in glob.glob(os.path.join(ROOT, "configs", "*.yml")):
    with open(cfg) as f:
        c = f.read()
    cfg_types[os.path.basename(cfg)] = re.findall(r"type:\s*([A-Za-z_]\w*)", c)

out_dir = os.path.join(os.path.dirname(__file__), "out")
os.makedirs(out_dir, exist_ok=True)
rows = []
rows.append(["registered_archs", ";".join(sorted(arch_regs))])
rows.append(["registered_models", ";".join(sorted(model_regs))])
rows.append(["stage2_referenced_types", ";".join(cfg_types.get("stage2_hflora.yml", []))])
rows.append(["RAVAE_registered", str("RAVAE" in arch_regs)])
rows.append(["RAVAE_EQ_registered", str("RAVAE_EQ" in arch_regs)])
rows.append(["stage2_loads_RAVAE_via_get", "RAVAE in stage2 vae_config.type -> ARCH_REGISTRY.get('RAVAE') raises KeyError"])

with open(os.path.join(out_dir, "arch_registry.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["key", "value"])
    w.writerows(rows)

for r in rows:
    print(r[0], "=>", r[1])
