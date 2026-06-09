"""Checks (read-only): (1) which arch/model types are registered vs referenced
in the configs; (2) existence of promised artefacts (weights, datasets, deps).
Supports findings: stage2-ravae-type-unregistered, missing-restoration-network,
missing-weights-data, missing-deps-readme.
Pure static parsing -- does NOT import torch or run the repo."""
import os
import re
import json

REPO = os.path.join(os.path.dirname(__file__), '..', 'code', 'lyd-2022__Latent-Harmony')
REPO = os.path.abspath(REPO)
OUT = os.path.join(os.path.dirname(__file__), 'out')
os.makedirs(OUT, exist_ok=True)

# 1) registered arch class names (decorator @ARCH_REGISTRY.register() on next class line)
registered_archs = []
for root, _, files in os.walk(os.path.join(REPO, 'basicsr', 'archs')):
    if '__pycache__' in root:
        continue
    for f in files:
        if not f.endswith('_arch.py'):  # only *_arch.py are auto-imported
            continue
        path = os.path.join(root, f)
        with open(path) as fh:
            lines = fh.readlines()
        for i, ln in enumerate(lines):
            if 'ARCH_REGISTRY.register()' in ln:
                # find next "class X" line
                for j in range(i + 1, min(i + 4, len(lines))):
                    m = re.match(r'\s*class\s+(\w+)', lines[j])
                    if m:
                        registered_archs.append((m.group(1), os.path.relpath(path, REPO)))
                        break

# 2) types referenced in configs
cfg_types = {}
for cfg in ['stage1_eqvae.yml', 'stage2_hflora.yml']:
    p = os.path.join(REPO, 'configs', cfg)
    with open(p) as fh:
        txt = fh.read()
    cfg_types[cfg] = re.findall(r'^\s*type:\s*([A-Za-z_]\w+)', txt, flags=re.M)

reg_names = set(n for n, _ in registered_archs)
# RAVAE referenced by stage2 vae_config
ravae_referenced = 'RAVAE' in cfg_types['stage2_hflora.yml']
ravae_registered = 'RAVAE' in reg_names

# restoration network presence (SFHformer/Restormer/NAFNet AS a registered top-level net_g)
restoration_net_registered = any(
    n in reg_names for n in ['SFHformer', 'Restormer', 'NAFNet', 'RestorationNet']
)

# 3) promised artefacts
artefacts = {
    './weights/stage1_eqvae.pth': os.path.join(REPO, 'weights', 'stage1_eqvae.pth'),
    './weights/dinov2_vits14.pth': os.path.join(REPO, 'weights', 'dinov2_vits14.pth'),
    './datasets/train/gt': os.path.join(REPO, 'datasets', 'train', 'gt'),
    './datasets/train/lq': os.path.join(REPO, 'datasets', 'train', 'lq'),
    'requirements.txt': os.path.join(REPO, 'requirements.txt'),
    'setup.py': os.path.join(REPO, 'setup.py'),
    'environment.yml': os.path.join(REPO, 'environment.yml'),
}
artefact_exists = {k: os.path.exists(v) for k, v in artefacts.items()}

result = {
    'registered_archs': registered_archs,
    'config_types': cfg_types,
    'RAVAE_referenced_in_stage2_config': ravae_referenced,
    'RAVAE_registered': ravae_registered,
    'restoration_net_registered': restoration_net_registered,
    'artefact_exists': artefact_exists,
}
with open(os.path.join(OUT, 'registry_and_artifacts.json'), 'w') as fh:
    json.dump(result, fh, indent=2)
print(json.dumps(result, indent=2))
