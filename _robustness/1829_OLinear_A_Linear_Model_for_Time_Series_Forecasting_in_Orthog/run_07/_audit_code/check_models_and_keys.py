"""Checks (a) which model keys the scripts request vs what model_dict provides, and
(b) whether any baseline / plug-in model (iTransformer/PatchTST/DLinear/...) exists in model/.
Supports 'missing' (no baseline/plug-in code) and 'bug' (undefined wavelet_concat key) findings.
Read-only. Output: out/model_keys.csv
"""
import os, re, glob, csv

REPO = os.path.join(os.path.dirname(__file__), '..', 'code', 'jackyue1994__OLinear')
EXP = os.path.join(REPO, 'experiments', 'exp_basic.py')
OUT = os.path.join(os.path.dirname(__file__), 'out', 'model_keys.csv')

# model_dict keys (parse the dict literal)
exp_txt = open(EXP).read()
keys = set(re.findall(r"'([A-Za-z0-9_]+)':\s*[A-Za-z0-9_]+,", exp_txt))

# model names requested in scripts (active, non-commented lines)
requested = set()
for sh in glob.glob(os.path.join(REPO, 'scripts', '**', '*.sh'), recursive=True):
    for line in open(sh, errors='ignore'):
        s = line.strip()
        if s.startswith('#'):
            continue
        m = re.match(r'model_name=([A-Za-z0-9_]+)\b', s)
        if m and m.group(1):
            requested.add(m.group(1))
        for arr in re.findall(r'model_names=\(([^)]*)\)', s):
            for tok in arr.split():
                if re.match(r'^[A-Za-z0-9_]+$', tok):
                    requested.add(tok)

undefined = sorted(r for r in requested if r and r not in keys)

# baseline / plug-in model files in model/
baseline_names = ['iTransformer', 'PatchTST', 'DLinear', 'TimeMixer', 'Leddam',
                  'CARD', 'Fredformer', 'FITS', 'FilterNet', 'TimesNet']
model_files = os.listdir(os.path.join(REPO, 'model'))
baseline_present = {b: any(b.lower() in f.lower() for f in model_files) for b in baseline_names}

rows = []
rows.append(['model_dict_keys', ';'.join(sorted(keys))])
rows.append(['requested_in_scripts', ';'.join(sorted(requested))])
rows.append(['UNDEFINED_keys_requested', ';'.join(undefined)])
for b, present in baseline_present.items():
    rows.append([f'baseline_model_file:{b}', 'PRESENT' if present else 'ABSENT'])

with open(OUT, 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['key', 'value'])
    w.writerows(rows)

for r in rows:
    print(r)
print('\nWrote', OUT)
