"""Read-only greps that support the 'missing'/'bug'/'methodology' findings:
- CSM/epoch-selection code absent (epoch-selection-mechanism-absent)
- Friedman/Nemenyi/CD test code absent (friedman-nemenyi-tests-missing)
- explanation/attribution/MNIST code absent (explanation-mnist-code-missing)
- run_knn.sh references a non-existent Full_experiments.py (run-knn-wrong-filename)
- per-dataset epoch lookup range, vs fixed-default baselines (asymmetric-epoch-tuning-vs-baselines)
Outputs a JSON summary under out/."""
import os, re, glob, json

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "code", "ZhongLIFR__TCCM-NIPS"))
py_files = glob.glob(os.path.join(REPO, "**", "*.py"), recursive=True)

def grep_any(patterns):
    hits = []
    rx = re.compile("|".join(patterns), re.I)
    for f in py_files:
        for i, line in enumerate(open(f, errors="ignore"), 1):
            if rx.search(line):
                hits.append(f"{os.path.relpath(f, REPO)}:{i}: {line.strip()}")
    return hits

out = {}
out["csm_epoch_selection_hits"] = grep_any([r"\bCSM\b", r"contrast score", r"\bmargin\b",
                                            r"top.?k", r"select.?epoch", r"epoch.?select",
                                            r"candidate.?epoch", r"unsupervised.*tun"])
out["statistical_test_hits"] = grep_any([r"friedman", r"nemenyi", r"critical.?difference",
                                         r"posthoc", r"scikit_posthoc", r"\bCD\b.*diagram",
                                         r"wilcoxon", r"kruskal"])
out["explanation_hits"] = grep_any([r"explain", r"attribut", r"feature.?wise", r"feature.?level",
                                    r"heatmap", r"importance", r"\bmnist\b",
                                    r"per.?feature", r"contribution"])

# run_knn.sh wrong filename
knn = os.path.join(REPO, "bash_files", "run_knn.sh")
knn_src = open(knn).read()
out["run_knn_calls_Full_experiments"] = "Full_experiments.py" in knn_src
out["FullExperiments_exists"] = os.path.isfile(os.path.join(REPO, "FullExperiments.py"))
out["Full_experiments_exists"] = os.path.isfile(os.path.join(REPO, "Full_experiments.py"))

# per-dataset epoch range
fsrc = open(os.path.join(REPO, "FMAD", "functions.py")).read()
epochs = [int(m) for m in re.findall(r"epoch_size\s*=\s*(\d+)", fsrc)]
out["tccm_epoch_branches"] = len(epochs)
out["tccm_epoch_min"] = min(epochs)
out["tccm_epoch_max"] = max(epochs)

print(json.dumps({k: (v if not isinstance(v, list) else {"count": len(v), "sample": v[:5]})
                  for k, v in out.items()}, indent=2))
os.makedirs(os.path.join(os.path.dirname(__file__), "out"), exist_ok=True)
with open(os.path.join(os.path.dirname(__file__), "out", "missing_components.json"), "w") as f:
    json.dump(out, f, indent=2)
