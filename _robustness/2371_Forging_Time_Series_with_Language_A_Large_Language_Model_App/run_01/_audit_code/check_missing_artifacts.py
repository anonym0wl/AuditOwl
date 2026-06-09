"""Deterministic file-existence checks in the supplemental reproduction package.
Supports findings: baselines-generation-missing, conditional-knn-eval-missing.
Read-only: scans code/SDForger__neurips_supplemental for baseline / classifier code.
"""
import os, re, json

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..",
                                    "code", "SDForger__neurips_supplemental"))

py_files = []
for dp, _, fns in os.walk(ROOT):
    for fn in fns:
        if fn.endswith(".py"):
            py_files.append(os.path.join(dp, fn))

baseline_terms = ["TimeVAE", "TimeVQVAE", "RtsGAN", "RTSGAN", "SdeGAN", "SDEGAN", "LS4"]
baseline_hits = {}
for p in py_files:
    txt = open(p, encoding="utf-8", errors="ignore").read()
    for t in baseline_terms:
        if re.search(r"\b" + re.escape(t) + r"\b", txt):
            baseline_hits.setdefault(t, []).append(os.path.relpath(p, ROOT))

# classifier / conditional-eval terms (Section 6, Figure 2, 0.81 accuracy)
clf_terms = ["KNeighbors", "KNeighborsClassifier", "accuracy_score", ".score(",
             "skfda", "ramos", "NearestNeighbors", "classif"]
clf_hits = {}
for p in py_files:
    txt = open(p, encoding="utf-8", errors="ignore").read()
    for t in clf_terms:
        if t.lower() in txt.lower():
            clf_hits.setdefault(t, []).append(os.path.relpath(p, ROOT))

# notebook scan (only conditional_generation.ipynb)
nb_path = os.path.join(ROOT, "notebook", "conditional_generation.ipynb")
nb_clf = []
if os.path.exists(nb_path):
    nb = json.load(open(nb_path))
    for i, c in enumerate(nb["cells"]):
        if c["cell_type"] == "code":
            src = "".join(c["source"])
            for t in clf_terms:
                if t.lower() in src.lower():
                    nb_clf.append((i, t))

lines = []
lines.append(f"Python files scanned: {len(py_files)}")
lines.append(f"Baseline generation/eval references in .py files: "
             f"{baseline_hits if baseline_hits else 'NONE'}")
lines.append(f"Classifier/conditional-eval references in .py files: "
             f"{clf_hits if clf_hits else 'NONE'}")
lines.append(f"Classifier refs in conditional_generation.ipynb cells: "
             f"{nb_clf if nb_clf else 'NONE'}")
lines.append("Conclusion: baseline generation code = "
             + ("PRESENT" if baseline_hits else "ABSENT"))
lines.append("Conclusion: conditional KNN-accuracy (Sec 6 / Fig 2, 0.81) eval code = "
             + ("PRESENT" if (clf_hits or nb_clf) else "ABSENT"))

os.makedirs(os.path.join(os.path.dirname(__file__), "out"), exist_ok=True)
with open(os.path.join(os.path.dirname(__file__), "out", "missing_artifacts.txt"), "w") as f:
    f.write("\n".join(lines) + "\n")
print("\n".join(lines))
