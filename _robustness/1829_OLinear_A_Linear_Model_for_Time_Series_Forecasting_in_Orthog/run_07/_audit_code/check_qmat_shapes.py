"""Checks bundled Q-matrix .npy shapes match seq_len/pred_len and CSV channel count.
Supports the data-availability/runnability assessment (whether bundled datasets run end-to-end).
Read-only. Output: out/qmat_shapes.csv
"""
import os, glob, csv
import numpy as np
import pandas as pd

REPO = os.path.join(os.path.dirname(__file__), '..', 'code', 'jackyue1994__OLinear')
DS = os.path.join(REPO, 'dataset')
OUT = os.path.join(os.path.dirname(__file__), 'out', 'qmat_shapes.csv')

rows = []
for d in sorted(os.listdir(DS)):
    dpath = os.path.join(DS, d)
    if not os.path.isdir(dpath):
        continue
    csvs = glob.glob(os.path.join(dpath, '*.csv'))
    ncols = None
    if csvs:
        try:
            df = pd.read_csv(csvs[0], nrows=5)
            cols = [c for c in df.columns if c.lower() != 'date']
            ncols = len(cols)
        except Exception as e:
            ncols = f'ERR:{e}'
    npys = sorted(glob.glob(os.path.join(dpath, '*.npy')))
    for n in npys:
        base = os.path.basename(n)
        try:
            arr = np.load(n)
            shape = arr.shape
        except Exception as e:
            shape = f'ERR:{e}'
        rows.append([d, ncols, base, str(shape)])

with open(OUT, 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['dataset', 'csv_n_feature_cols', 'npy_file', 'npy_shape'])
    w.writerows(rows)

for r in rows:
    print(r)
print('\nWrote', OUT)
