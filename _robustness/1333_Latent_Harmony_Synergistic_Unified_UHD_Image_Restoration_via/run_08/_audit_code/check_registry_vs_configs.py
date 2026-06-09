"""Statically check that every `type:` name in the two example configs resolves
to an ARCH/MODEL/LOSS/DATASET class registered in basicsr. Supports finding
`stage2-vae-type-unregistered` (config asks for `RAVAE`, repo only has `RAVAE_EQ`).
Read-only: parses source with AST + yaml, imports nothing from the repo.
"""
import ast
import os
import sys
import yaml

REPO = os.path.join(os.path.dirname(__file__), '..', 'code', 'lyd-2022__Latent-Harmony')
REPO = os.path.abspath(REPO)
OUT = os.path.join(os.path.dirname(__file__), 'out')
os.makedirs(OUT, exist_ok=True)


def registered_class_names(subdir, suffix):
    """Return set of class names decorated with *_REGISTRY.register() under subdir."""
    names = set()
    folder = os.path.join(REPO, 'basicsr', subdir)
    for fn in os.listdir(folder):
        if not fn.endswith('.py'):
            continue
        path = os.path.join(folder, fn)
        with open(path) as f:
            tree = ast.parse(f.read(), filename=path)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for dec in node.decorator_list:
                    # match X_REGISTRY.register(...)
                    if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute):
                        if dec.func.attr == 'register':
                            names.add(node.name)
    return names


def collect_types(d, acc):
    if isinstance(d, dict):
        for k, v in d.items():
            if k == 'type' and isinstance(v, str):
                acc.append(v)
            collect_types(v, acc)
    elif isinstance(d, list):
        for v in d:
            collect_types(v, acc)


arch_names = registered_class_names('archs', '_arch.py')
model_names = registered_class_names('models', '_model.py')
loss_names = registered_class_names('losses', None)
data_names = registered_class_names('data', None)
all_registered = arch_names | model_names | loss_names | data_names

print('Registered ARCH classes :', sorted(arch_names))
print('Registered MODEL classes:', sorted(model_names))
print('Registered LOSS classes :', sorted(loss_names))
print('Registered DATA classes :', sorted(data_names))
print()

lines = []
for cfg in ['stage1_eqvae.yml', 'stage2_hflora.yml']:
    path = os.path.join(REPO, 'configs', cfg)
    with open(path) as f:
        opt = yaml.safe_load(f)
    types = []
    collect_types(opt, types)
    model_type = opt.get('model_type')
    if model_type:
        types.append(model_type)
    for t in sorted(set(types)):
        status = 'OK' if t in all_registered else 'UNREGISTERED'
        line = f'{cfg},{t},{status}'
        lines.append(line)
        print(line)

with open(os.path.join(OUT, 'registry_vs_configs.csv'), 'w') as f:
    f.write('config,type_name,status\n')
    f.write('\n'.join(lines) + '\n')

print()
print('Wrote', os.path.join(OUT, 'registry_vs_configs.csv'))
