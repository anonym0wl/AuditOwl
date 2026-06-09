"""Checks that run_semisupervise.sh's `for j in {45..50}` omits INNE_semisup (index 51).
Supports finding: semisupervise-range-off-by-one. Read-only.
"""
import os

REPO = os.path.join(os.path.dirname(__file__), "..", "code", "ZhongLIFR__TCCM-NIPS")

# Reconstruct MODEL_NAMES exactly as in FullExperiments.py / AggregateResults.py
deep = ["TCCM","VAE","SO_GAAL","MO_GAAL","AutoEncoder","DeepSVDD","LUNAR","DIF","ALAD","AE1SVM","AnoGAN"]
trans = ["ABOD","COF","LOF","PCA","KPCA","KNN","INNE"]
induc = ["CBLOF","IForest","LODA","FeatureBagging","Sampling","MCD","CD","ECOD","HBOS","OCSVM","KDE","GMM","QMCD","LMDD"]
addl = ["DAGMM","GANomaly","NormalizingFlow","DROCC","DTEDDPM","DTEGaussian","DTEInverseGamma","DTECategorical","DTENonParametric","ICL","GOAD","SLAD","MCM"]
force = ["ABOD_semisup","COF_semisup","LOF_semisup","PCA_semisup","KPCA_semisup","KNN_semisup","INNE_semisup"]
MODEL_NAMES = deep + trans + induc + addl + force

print("total models:", len(MODEL_NAMES))
print("force_inductive (7 models) indices:")
for i, name in enumerate(MODEL_NAMES):
    if name in force:
        print(f"  index {i}: {name}")

# run_semisupervise.sh uses `for j in {45..50}` -> indices 45..50 inclusive = 6 models
ran = set(range(45, 51))  # {45,46,47,48,49,50}
force_indices = {i for i, n in enumerate(MODEL_NAMES) if n in force}
missing = sorted(force_indices - ran)
print("\nIndices run by run_semisupervise.sh (j in {45..50}):", sorted(ran))
print("Force-inductive indices:", sorted(force_indices))
print("Force-inductive models NEVER run:", [(i, MODEL_NAMES[i]) for i in missing])

out = os.path.join(os.path.dirname(__file__), "out", "model_index_range.txt")
with open(out, "w") as f:
    f.write(f"total_models={len(MODEL_NAMES)}\n")
    f.write(f"ran_indices={sorted(ran)}\n")
    f.write(f"force_indices={sorted(force_indices)}\n")
    f.write(f"never_run={[(i, MODEL_NAMES[i]) for i in missing]}\n")
print("\nwrote", out)
