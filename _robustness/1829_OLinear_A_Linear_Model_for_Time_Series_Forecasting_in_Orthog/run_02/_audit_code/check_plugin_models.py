"""Checks that (a) the model registry contains only OLinear variants (no
iTransformer/PatchTST/RLinear/DLinear/Leddam baselines) and (b) the CLI plugin
flags for applying OrthoTrans/NormLin to baselines are never consumed by any
model. Supports `missing-plugin-and-baseline-code`."""
import os, re, glob

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'code', 'jackyue1994__OLinear'))

# (a) model registry
basic = open(os.path.join(REPO, 'experiments', 'exp_basic.py')).read()
reg = re.findall(r"'([^']+)':\s*\w+", basic)
print('Models registered in exp_basic.model_dict:')
for m in reg:
    print('   ', m)
baselines = ['iTransformer', 'PatchTST', 'RLinear', 'DLinear', 'Leddam',
             'TimeMixer', 'TimesNet', 'CARD', 'Fredformer', 'FilterNet']
present_baselines = [b for b in baselines if any(b.lower() in r.lower() for r in reg)]
print('\nPaper baselines present in registry:', present_baselines or 'NONE')

# (b) plugin flags consumed?
flags = ['iTrans_ortho_trans', 'PatchTST_ortho_trans', 'DLinear_ortho_trans',
         'iTrans_linear', 'PatchTST_linear', 'Leddam_attnLinear']
pyfiles = [p for p in glob.glob(os.path.join(REPO, '**', '*.py'), recursive=True)
           if '__pycache__' not in p]
print('\nPlugin-flag consumption (files using each flag, excluding run.py arg defs):')
for fl in flags:
    users = []
    for p in pyfiles:
        if os.path.basename(p) == 'run.py':
            continue
        txt = open(p).read()
        # count real uses (attribute access args.<flag>), not just substring in comments
        if re.search(r'\b%s\b' % re.escape(fl), txt):
            users.append(os.path.relpath(p, REPO))
    print('   %-22s -> %s' % (fl, users or 'NEVER CONSUMED'))
