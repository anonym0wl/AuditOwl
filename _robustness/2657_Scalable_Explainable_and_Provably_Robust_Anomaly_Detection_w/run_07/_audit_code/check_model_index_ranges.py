"""Maps the bash model-index ranges to MODEL_NAMES entries to detect off-by-one / omitted models.
Supports finding: knn-semisup-omitted-from-bash. Read-only. Output -> out/model_index_ranges.csv
"""
import os, ast, csv

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "code", "ZhongLIFR__TCCM-NIPS"))
src = open(os.path.join(REPO, "FullExperiments.py")).read()
tree = ast.parse(src)
dicts = {}
for node in tree.body:
    if isinstance(node, ast.Assign) and isinstance(node.value, ast.Dict):
        name = node.targets[0].id if isinstance(node.targets[0], ast.Name) else None
        if name:
            dicts[name] = [k.value for k in node.value.keys]

order = (dicts['deep_models'] + dicts['transductive_models'] + dicts['inductive_models']
         + dicts['additional_models'] + dicts['force_inductive_models'])

ranges = {
    "run_main.sh {0..44}": range(0, 45),
    "run_semisupervise.sh {45..50}": range(45, 51),
    "run_knn.sh {50..50}": range(50, 51),
}

rows = []
print("Total MODEL_NAMES:", len(order))
for label, rng in ranges.items():
    covered = [order[i] for i in rng if i < len(order)]
    rows.append({"bash_loop": label, "indices": f"{rng.start}..{rng.stop-1}",
                 "models_run": ";".join(covered)})
    print(label, "->", covered)

force_inductive = dicts['force_inductive_models']
fi_indices = [order.index(m) for m in force_inductive]
omitted = [order[i] for i in range(len(order)) if i not in set(range(0, 51)) and order[i] in force_inductive]
print("force_inductive indices:", dict(zip(force_inductive, fi_indices)))
print("force_inductive models NOT covered by {45..50}:", omitted)
rows.append({"bash_loop": "force_inductive omitted by {45..50}", "indices": "51",
             "models_run": ";".join(omitted)})

out = os.path.join(os.path.dirname(__file__), "out", "model_index_ranges.csv")
with open(out, "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print("Wrote", out)
