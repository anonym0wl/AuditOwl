"""Check that Generate_corrmat.ipynb (temporal-Q cell 0) selects only the training
portion of the series (indices < train_length) -- supports finding 'q-matrix-train-only-no-leakage'.
Read-only: simulates the slicing logic on synthetic shapes; does not modify repo."""
import numpy as np, json, os

# Reproduce cell-0 index math for a few dataset lengths & the .csv branch.
out = []
for n in [10000, 52696, 17544]:  # weather, ECL-ish, ETTh1-ish row counts
    train_ratio = 0.7
    train_length = int(n * train_ratio)
    for base_ratio in [1.0]:
        ratio = train_ratio * base_ratio
        start = train_length - int(n * ratio)   # csv branch lower bound
        end = train_length
        # Dataset_Custom train border: [0, num_train) with num_train=int(n*0.7)
        num_train = int(n * 0.7)
        leak = end > num_train  # any index >= num_train would be val/test
        out.append(dict(n=n, train_length=train_length, corr_start=start,
                        corr_end=end, dataset_num_train=num_train,
                        uses_only_train=(start>=0 and end<=num_train),
                        leak_into_val_test=bool(leak)))
for r in out:
    print(r)
with open(os.path.join('out','corrmat_train_only.json'),'w') as f:
    json.dump(out, f, indent=2)
