"""Check: does any *_arch.py register an arch named 'RAVAE' (referenced by stage2_hflora.yml)?

Supports finding `stage2-ravae-type-not-registered`. Static (regex) scan only; read-only.
The Registry.get() in basicsr/utils/registry.py raises KeyError on a missing name,
so an unregistered 'RAVAE' would crash Stage-2 instantiation.
"""
import os
import re
import csv

CODE = os.path.join(os.path.dirname(__file__), '..', 'code', 'lyd-2022__Latent-Harmony')
ARCH_DIR = os.path.join(CODE, 'basicsr', 'archs')

# Registry only scans files ending with '_arch.py' (see basicsr/archs/__init__.py).
arch_files = [f for f in os.listdir(ARCH_DIR) if f.endswith('_arch.py')]

registered = set()
# A class is registered iff decorated with @ARCH_REGISTRY.register(); name = class name.
for f in arch_files:
    with open(os.path.join(ARCH_DIR, f)) as fh:
        src = fh.read()
    # find "@ARCH_REGISTRY.register()\n...class X("
    for m in re.finditer(r'@ARCH_REGISTRY\.register\(\)\s*\nclass\s+(\w+)', src):
        registered.add(m.group(1))

# types requested by the configs
requested = {}
cfg_dir = os.path.join(CODE, 'configs')
for cf in os.listdir(cfg_dir):
    with open(os.path.join(cfg_dir, cf)) as fh:
        for line in fh:
            m = re.search(r'\btype:\s*([A-Za-z_]\w+)', line)
            if m:
                requested.setdefault(m.group(1), []).append(cf)

rows = []
for t, cfs in sorted(requested.items()):
    # only care about network_g arch types we expect in ARCH_REGISTRY
    rows.append((t, ';'.join(sorted(set(cfs))), t in registered))

out = os.path.join(os.path.dirname(__file__), 'out', 'arch_registry.csv')
with open(out, 'w', newline='') as fh:
    w = csv.writer(fh)
    w.writerow(['requested_type', 'in_configs', 'is_registered_arch'])
    for r in rows:
        w.writerow(r)

print('Registered arch classes (from *_arch.py):', sorted(registered))
print()
print('RAVAE registered? ', 'RAVAE' in registered)
print('RAVAE_EQ registered?', 'RAVAE_EQ' in registered)
print('RAVAEHFLora registered?', 'RAVAEHFLora' in registered)
print()
print('stage2_hflora.yml requests vae_config.type == RAVAE; Registry.get("RAVAE") -> KeyError')
print('Wrote', out)
