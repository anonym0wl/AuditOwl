"""Static check: is arch type 'RAVAE' (used by configs/stage2_hflora.yml:42) actually
registered/importable? Supports finding `stage2-ravae-arch-missing`.

The arch registry is populated only by modules ending in '_arch.py' (see
basicsr/archs/__init__.py auto-scan). We parse those files with `ast` and collect the
names of classes decorated with @ARCH_REGISTRY.register(). No torch import needed.
"""
import ast
import os

REPO = os.path.join(os.path.dirname(__file__), '..', 'code', 'lyd-2022__Latent-Harmony')
ARCH_DIR = os.path.join(REPO, 'basicsr', 'archs')

registered = []
for fn in sorted(os.listdir(ARCH_DIR)):
    if not fn.endswith('_arch.py'):
        continue
    path = os.path.join(ARCH_DIR, fn)
    tree = ast.parse(open(path).read(), filename=fn)
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for dec in node.decorator_list:
                # match @ARCH_REGISTRY.register()  (a Call whose func is an Attribute .register)
                func = dec.func if isinstance(dec, ast.Call) else dec
                if isinstance(func, ast.Attribute) and func.attr == 'register':
                    registered.append((fn, node.name))

reg_names = sorted({n for _, n in registered})
print('Auto-imported *_arch.py files contribute these registered arch names:')
for fn, name in registered:
    print(f'  {name:20s}  ({fn})')
print()
print('config stage2_hflora.yml requests vae_config.type = "RAVAE"')
print('Is "RAVAE" registered?  ->', 'RAVAE' in reg_names)
print('Is "RAVAE_EQ" registered? ->', 'RAVAE_EQ' in reg_names)
print()
print('VERDICT:', 'BUG (RAVAE not registered -> ARCH_REGISTRY.get("RAVAE") raises KeyError)'
      if 'RAVAE' not in reg_names else 'RAVAE present')
