"""Checks which dataset CSVs and Q-matrix .npy files referenced by the OLinear
shell scripts are actually present in the repo. Supports the `missing-headline-
datasets-and-qmats` finding."""
import os, re, glob, csv

REPO = os.path.join(os.path.dirname(__file__), '..', 'code', 'jackyue1994__OLinear')
REPO = os.path.abspath(REPO)
OUT = os.path.join(os.path.dirname(__file__), 'out', 'missing_data.csv')

# Collect (root_path, data_path, q_mat_file, q_out_mat_file) referenced in scripts.
scripts = glob.glob(os.path.join(REPO, 'scripts', '**', '*.sh'), recursive=True)

def grab(text, key):
    m = re.search(r'--%s\s+(\S+)' % re.escape(key), text)
    return m.group(1) if m else None

rows = []
referenced_roots = set()
for sp in scripts:
    txt = open(sp).read()
    root = grab(txt, 'root_path')
    data = grab(txt, 'data_path')
    if root:
        referenced_roots.add(root)
        # resolve relative to repo
        rp = os.path.normpath(os.path.join(REPO, root.lstrip('./')))
        present = os.path.isdir(rp)
        rows.append(('root_dir', root, 'present' if present else 'MISSING',
                     os.path.relpath(sp, REPO)))

# Dedup
seen = set()
dedup = []
for r in rows:
    k = (r[0], r[1])
    if k in seen:
        continue
    seen.add(k)
    dedup.append(r)

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['kind', 'path_referenced', 'status', 'example_script'])
    for r in sorted(dedup):
        w.writerow(r)

missing = [r for r in dedup if r[2] == 'MISSING']
present = [r for r in dedup if r[2] == 'present']
print('Distinct dataset root_path values referenced by scripts:', len(dedup))
print('  present :', len(present))
print('  MISSING :', len(missing))
print()
print('MISSING dataset directories (referenced by scripts, absent from repo):')
for r in sorted(missing):
    print('   ', r[1], '   (e.g.', r[3], ')')
print()
print('PRESENT dataset directories:')
for r in sorted(present):
    print('   ', r[1])
print()
print('Wrote', OUT)
