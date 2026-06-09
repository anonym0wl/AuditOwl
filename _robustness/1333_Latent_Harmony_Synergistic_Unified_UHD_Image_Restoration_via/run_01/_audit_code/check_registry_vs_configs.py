"""Statically check that every arch/model `type` referenced in configs is registered
in the code. Supports finding 'stage2-ravae-type-unregistered'. Read-only; no torch import."""
import os, re, glob, json

REPO = os.path.join(os.path.dirname(__file__), "..", "code", "lyd-2022__Latent-Harmony")
REPO = os.path.abspath(REPO)

# 1) collect registered arch class names (decorator @ARCH_REGISTRY.register() then `class X`)
def collect_registered(folder, registry):
    names = set()
    for path in glob.glob(os.path.join(REPO, folder, "*.py")):
        with open(path) as f:
            lines = f.readlines()
        for i, ln in enumerate(lines):
            if registry in ln and ".register()" in ln:
                # next non-empty line should be a class def
                for j in range(i+1, min(i+4, len(lines))):
                    m = re.match(r"\s*class\s+([A-Za-z_]\w*)", lines[j])
                    if m:
                        names.add(m.group(1))
                        break
    return names

arch_names = collect_registered("basicsr/archs", "ARCH_REGISTRY")
model_names = collect_registered("basicsr/models", "MODEL_REGISTRY")

# 2) collect type: references from config ymls
type_refs = []  # (file, lineno, kind_guess, value)
for path in glob.glob(os.path.join(REPO, "configs", "*.yml")):
    with open(path) as f:
        for n, ln in enumerate(f, 1):
            m = re.match(r"\s*(model_)?type:\s*([A-Za-z_]\w*)\s*$", ln)
            if m:
                type_refs.append((os.path.basename(path), n, ln.strip()))

# 3) cross-check arch-looking types (those that are not loss/dataset/optimizer/io types)
known_non_arch = {"PairedImageDataset", "disk", "L1Loss", "KlLoss", "GANLoss",
                  "Adam", "CosineAnnealingRestartLR"}
results = []
for fname, lineno, raw in type_refs:
    val = raw.split(":", 1)[1].strip()
    is_model = raw.startswith("model_type")
    if val in known_non_arch:
        verdict = "non-arch (skipped)"
    elif is_model:
        verdict = "REGISTERED" if val in model_names else "UNREGISTERED-MODEL"
    elif val in arch_names:
        verdict = "REGISTERED-ARCH"
    elif val in {"UNetDiscriminatorSN"}:  # discriminator arch
        verdict = "REGISTERED-ARCH" if val in arch_names else "UNREGISTERED-ARCH"
    else:
        verdict = "UNREGISTERED-ARCH"
    results.append({"file": fname, "line": lineno, "ref": raw, "value": val, "verdict": verdict})

out = {
    "registered_archs": sorted(arch_names),
    "registered_models": sorted(model_names),
    "config_type_refs": results,
    "unregistered": [r for r in results if "UNREGISTERED" in r["verdict"]],
}
outpath = os.path.join(os.path.dirname(__file__), "out", "registry_vs_configs.json")
with open(outpath, "w") as f:
    json.dump(out, f, indent=2)
print(json.dumps(out, indent=2))
