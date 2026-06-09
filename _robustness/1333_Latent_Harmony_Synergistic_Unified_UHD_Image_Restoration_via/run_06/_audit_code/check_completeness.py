"""Static completeness check: which reproduction artefacts exist?

Supports findings `no-eval-entrypoint`, `no-requirements`, `no-data`, `readme-empty`.
Looks for: an eval/inference/metric-computing entrypoint; a dependency spec; a non-trivial
README; pretrained weights; dataset files.
"""
import os, re

REPO = os.path.join(os.path.dirname(__file__), '..', 'code', 'lyd-2022__Latent-Harmony')

# 1) entrypoints: files with `if __name__ == '__main__'`
mains = []
for root, _, files in os.walk(REPO):
    if '__pycache__' in root:
        continue
    for f in files:
        if f.endswith('.py'):
            p = os.path.join(root, f)
            t = open(p, errors='ignore').read()
            if re.search(r"__name__\s*==\s*['\"]__main__['\"]", t):
                rel = os.path.relpath(p, REPO)
                # classify
                kind = 'train' if 'train_pipeline' in t or rel.endswith('train.py') else \
                       'eval/test' if re.search(r'test_pipeline|def main\b.*test|inference', t) else 'debug/util'
                mains.append((rel, kind))
print('Runnable entrypoints (__main__):')
for rel, kind in sorted(mains):
    print(f'  {rel:40s} -> {kind}')
print()

# 2) is there ANY explicit test/eval pipeline like BasicSR test.py?
has_test_py = os.path.exists(os.path.join(REPO, 'basicsr', 'test.py'))
print('basicsr/test.py exists? ->', has_test_py)
print()

# 3) dependency spec
dep_files = []
for name in ['requirements.txt', 'setup.py', 'setup.cfg', 'pyproject.toml',
             'environment.yml', 'environment.yaml', 'conda.yaml', 'Pipfile']:
    if os.path.exists(os.path.join(REPO, name)):
        dep_files.append(name)
print('Dependency spec files present:', dep_files if dep_files else 'NONE')
print()

# 4) README content
readme = os.path.join(REPO, 'README.md')
content = open(readme).read() if os.path.exists(readme) else ''
print(f'README.md byte length: {len(content)}  content={content!r}')
print()

# 5) weights / checkpoints / datasets
weight_like = []
data_like = []
for root, _, files in os.walk(REPO):
    if '__pycache__' in root:
        continue
    for f in files:
        if f.endswith(('.pth', '.ckpt', '.pt', '.safetensors')):
            weight_like.append(os.path.relpath(os.path.join(root, f), REPO))
        if f.endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tif')):
            data_like.append(os.path.relpath(os.path.join(root, f), REPO))
print('Checkpoint/weight files present:', weight_like if weight_like else 'NONE')
print('Image/data files present:', data_like if data_like else 'NONE')
print()
print('Configs reference these external artefacts (must be supplied by user):')
for cfgname in ['stage1_eqvae.yml', 'stage2_hflora.yml']:
    cfg = open(os.path.join(REPO, 'configs', cfgname)).read()
    for ln in cfg.splitlines():
        if re.search(r'(weight|pretrain|dataroot).*:', ln) and ('./' in ln or 'weights' in ln):
            print(f'  [{cfgname}] {ln.strip()}')
