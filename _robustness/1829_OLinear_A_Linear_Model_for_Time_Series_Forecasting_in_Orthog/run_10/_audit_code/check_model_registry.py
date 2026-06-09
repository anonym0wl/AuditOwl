"""Checks which --model names requested by scripts are NOT registered in
experiments/exp_basic.py model_dict (would raise KeyError at run.py). Supports
finding 'basis-script-unregistered-model'. Read-only."""
import os, re, glob

REPO = os.path.join(os.path.dirname(__file__), '..', 'code', 'jackyue1994__OLinear')
REPO = os.path.abspath(REPO)
OUT = os.path.join(os.path.dirname(__file__), 'out')
os.makedirs(OUT, exist_ok=True)

# 1) registered model keys
exp_basic = open(os.path.join(REPO, 'experiments', 'exp_basic.py')).read()
registry = set(re.findall(r"'(OLinear[A-Za-z0-9_]*)'\s*:", exp_basic))

# 2) all model names referenced in shell scripts (model_names arrays + model_name=OLinear...)
referenced = {}
for sh in glob.glob(os.path.join(REPO, 'scripts', '**', '*.sh'), recursive=True):
    txt = open(sh).read()
    names = set()
    for m in re.findall(r'model_names=\(([^)]*)\)', txt):
        # skip commented lines is hard here; we only parse uncommented assignment lines
        pass
    # parse line-by-line, ignore comment lines
    for line in txt.splitlines():
        s = line.strip()
        if s.startswith('#'):
            continue
        m = re.search(r'model_names=\(([^)]*)\)', s)
        if m:
            for tok in m.group(1).split():
                names.add(tok)
        m2 = re.match(r'model_name=([A-Za-z0-9_]+)\s*$', s)
        if m2:
            names.add(m2.group(1))
    for n in names:
        if n.startswith('OLinear'):
            referenced.setdefault(n, []).append(os.path.relpath(sh, REPO))

unregistered = {n: fs for n, fs in referenced.items() if n not in registry}

lines = []
lines.append('registered_model_keys=' + ','.join(sorted(registry)))
lines.append('referenced_OLinear_models=' + ','.join(sorted(referenced)))
lines.append('UNREGISTERED (referenced by uncommented script lines but not in model_dict -> KeyError):')
for n in sorted(unregistered):
    lines.append(f'  {n}  in  {sorted(unregistered[n])}')
report = '\n'.join(lines)
print(report)
with open(os.path.join(OUT, 'model_registry_check.txt'), 'w') as f:
    f.write(report + '\n')
