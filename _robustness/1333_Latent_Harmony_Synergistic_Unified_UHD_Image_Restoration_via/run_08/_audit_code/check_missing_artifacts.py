"""File-existence checks for artefacts the paper's results depend on.
Supports findings: missing-dependency-spec, missing-data-and-weights,
missing-eval-script, missing-restoration-network-Rtheta.
Read-only; only stats the filesystem and greps source statically.
"""
import os
import re

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'code', 'lyd-2022__Latent-Harmony'))
OUT = os.path.join(os.path.dirname(__file__), 'out')
os.makedirs(OUT, exist_ok=True)

rows = []

# 1) dependency specification
dep_files = ['requirements.txt', 'setup.py', 'setup.cfg', 'pyproject.toml', 'environment.yml', 'environment.yaml', 'Pipfile']
present_dep = [f for f in dep_files if os.path.exists(os.path.join(REPO, f))]
rows.append(('dependency_spec', 'present' if present_dep else 'MISSING', ','.join(present_dep) or 'none of ' + '/'.join(dep_files)))

# 2) data dirs referenced by configs
for p in ['datasets', 'datasets/train/gt', 'datasets/train/lq', 'datasets/val/gt', 'datasets/val/lq']:
    rows.append(('data_dir:' + p, 'present' if os.path.exists(os.path.join(REPO, p)) else 'MISSING', ''))

# 3) weights referenced by configs
for p in ['weights', 'weights/stage1_eqvae.pth', 'weights/dinov2_vits14.pth']:
    rows.append(('weight:' + p, 'present' if os.path.exists(os.path.join(REPO, p)) else 'MISSING', ''))

# 4) download/prepare scripts
sh = []
for root, _, files in os.walk(REPO):
    if '__pycache__' in root:
        continue
    for fn in files:
        if fn.endswith('.sh') or 'download' in fn.lower() or 'prepare' in fn.lower():
            sh.append(os.path.relpath(os.path.join(root, fn), REPO))
rows.append(('download_or_prepare_scripts', 'present' if sh else 'MISSING', ','.join(sh) or 'none'))

# 5) test / inference / eval entrypoint
entry = []
for root, _, files in os.walk(REPO):
    if '__pycache__' in root:
        continue
    for fn in files:
        if re.search(r'(test|infer|demo|eval)\.py$', fn, re.I):
            entry.append(os.path.relpath(os.path.join(root, fn), REPO))
rows.append(('test_or_eval_entrypoint', 'present' if entry else 'MISSING', ','.join(entry) or 'only train.py exists'))

# 6) README with reproduction commands
readme = os.path.join(REPO, 'README.md')
readme_len = os.path.getsize(readme) if os.path.exists(readme) else -1
rows.append(('readme_bytes', str(readme_len), 'README.md size in bytes (16 = just "# Latent-Harmony")'))

# 7) restoration network R_theta as separate trainable module in stage-2 model
vaeadapter = os.path.join(REPO, 'basicsr', 'models', 'VAEadapter_model.py')
src = open(vaeadapter).read()
# look for an LRes / restoration-net training: a second network besides net_g (VAE) and net_d_hf (disc)
has_res_net = bool(re.search(r'net_r\b|restoration.?net|R_theta|self\.net_res|LRes|l_res\b', src))
rows.append(('stage2_restoration_network_Rtheta', 'present' if has_res_net else 'MISSING',
             'VAEadapter trains only LoRA via HF loss; no Rtheta / LRes (paper Eq.7)'))

print(f'{"check":42s} {"status":10s} detail')
print('-' * 90)
for name, status, detail in rows:
    print(f'{name:42s} {status:10s} {detail}')

with open(os.path.join(OUT, 'missing_artifacts.csv'), 'w') as f:
    f.write('check,status,detail\n')
    for name, status, detail in rows:
        f.write(f'{name},{status},"{detail}"\n')
print('\nWrote', os.path.join(OUT, 'missing_artifacts.csv'))
