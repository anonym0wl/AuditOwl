"""Checks whether model implementations for the OrthoTrans/NormLin plug-in
experiments (paper Table 5 & generality figs: iTransformer, PatchTST, RLinear,
DLinear) exist in model/ and are registered. Supports finding
'plugin-generality-models-missing'. Read-only."""
import os, re, glob

REPO = os.path.join(os.path.dirname(__file__), '..', 'code', 'jackyue1994__OLinear')
REPO = os.path.abspath(REPO)
OUT = os.path.join(os.path.dirname(__file__), 'out')
os.makedirs(OUT, exist_ok=True)

baselines = ['iTransformer', 'PatchTST', 'RLinear', 'DLinear']
model_files = [os.path.relpath(p, REPO) for p in glob.glob(os.path.join(REPO, 'model', '**', '*.py'), recursive=True)]
exp_basic = open(os.path.join(REPO, 'experiments', 'exp_basic.py')).read()
registry = set(re.findall(r"'([A-Za-z0-9_]+)'\s*:", exp_basic))

lines = []
lines.append('model/ python files:')
for mf in sorted(model_files):
    lines.append('  ' + mf)
lines.append('')
lines.append('registered model_dict keys: ' + ','.join(sorted(registry)))
lines.append('')
for b in baselines:
    file_hit = [mf for mf in model_files if b.lower() in os.path.basename(mf).lower()]
    reg_hit = [k for k in registry if b.lower() in k.lower()]
    lines.append(f'{b}: model_file={file_hit or "NONE"} ; registry_key={reg_hit or "NONE"}')

# scripts that try to run plugin experiments
plugin_scripts = []
for sh in glob.glob(os.path.join(REPO, 'scripts', '**', '*.sh'), recursive=True):
    txt = open(sh).read()
    for b in baselines:
        if re.search(rf'--model\s+{b}\b', txt):
            plugin_scripts.append((os.path.relpath(sh, REPO), b))
lines.append('')
lines.append('scripts invoking a baseline directly as --model: ' + (str(plugin_scripts) if plugin_scripts else 'NONE'))

report = '\n'.join(lines)
print(report)
with open(os.path.join(OUT, 'plugin_baselines_check.txt'), 'w') as f:
    f.write(report + '\n')
