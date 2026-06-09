"""For every OLinear_C/var-corr script whose root_path points at a *bundled* dataset,
check whether the referenced q_channel_file exists in the repo. Supports a 'missing' finding.
Read-only. Output: out/channel_files_missing.csv
"""
import os, re, glob, csv

REPO = os.path.join(os.path.dirname(__file__), '..', 'code', 'jackyue1994__OLinear')
SCRIPTS = os.path.join(REPO, 'scripts')
OUT = os.path.join(os.path.dirname(__file__), 'out', 'channel_files_missing.csv')

# bundled dataset dirs (have csv + temporal Q present in repo)
bundled = {'cars', 'covid', 'DowJones', 'ILI', 'nasdaq', 'power', 'SP500',
           'unemployment', 'weather', 'website', 'wiki'}

rows = []
for sh in glob.glob(os.path.join(SCRIPTS, '**', '*.sh'), recursive=True):
    txt = open(sh, errors='ignore').read()
    rp = re.search(r'--root_path\s+\S*dataset/([^/\s]+)/', txt)
    if not rp:
        continue
    ds = rp.group(1)
    if ds not in bundled:
        continue
    cf = re.search(r'--q_channel_file\s+(\S+)', txt)
    if not cf:
        continue
    fname = cf.group(1)
    # strip shell var interpolation if any
    if '$' in fname:
        # only ratio/seq are interpolated; channel files here are literal in practice
        pass
    full = os.path.join(REPO, 'dataset', ds, fname)
    exists = os.path.isfile(full)
    rel = os.path.relpath(sh, REPO)
    rows.append([rel, ds, fname, 'EXISTS' if exists else 'MISSING'])

with open(OUT, 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['script', 'dataset', 'q_channel_file', 'status'])
    w.writerows(rows)

missing = [r for r in rows if r[3] == 'MISSING']
for r in rows:
    print(r)
print(f'\n{len(missing)}/{len(rows)} referenced channel files MISSING (bundled datasets only)')
print('Wrote', OUT)
