"""Checks run_semisupervise.sh loop bound vs the MODEL_NAMES index map.

Supports finding `semisup-loop-off-by-one`: the bash loop `for j in {45..50}`
covers only 6 force-inductive models (indices 45-50) but the comment says
"7 models"; index 51 (INNE_semisup) is never executed, although the semi_only
aggregation expects all 7 force-inductive detectors. Output: out/semisup_index_range.txt
"""
import os

# MODEL_NAMES order is built in FullExperiments.py as:
deep_models = ['TCCM','VAE','SO_GAAL','MO_GAAL','AutoEncoder','DeepSVDD','LUNAR','DIF','ALAD','AE1SVM','AnoGAN']
transductive_models = ['ABOD','COF','LOF','PCA','KPCA','KNN','INNE']
inductive_models = ['CBLOF','IForest','LODA','FeatureBagging','Sampling','MCD','CD','ECOD','HBOS','OCSVM','KDE','GMM','QMCD','LMDD']
additional_models = ['DAGMM','GANomaly','NormalizingFlow','DROCC','DTEDDPM','DTEGaussian','DTEInverseGamma','DTECategorical','DTENonParametric','ICL','GOAD','SLAD','MCM']
force_inductive_models = ['ABOD_semisup','COF_semisup','LOF_semisup','PCA_semisup','KPCA_semisup','KNN_semisup','INNE_semisup']

MODEL_NAMES = deep_models + transductive_models + inductive_models + additional_models + force_inductive_models

# Bash `{45..50}` expands to inclusive 45..50 -> 6 values.
launched = list(range(45, 51))  # {45..50}
fi_indices = [i for i, m in enumerate(MODEL_NAMES) if m in force_inductive_models]

out = []
out.append(f"total MODEL_NAMES = {len(MODEL_NAMES)}")
out.append(f"force_inductive indices (expected to run) = {fi_indices} -> {[MODEL_NAMES[i] for i in fi_indices]}")
out.append(f"run_semisupervise.sh launches j in {{45..50}} = {launched} -> {[MODEL_NAMES[i] for i in launched]}")
missing = [i for i in fi_indices if i not in launched]
out.append(f"NOT launched (force-inductive index missing from loop) = {missing} -> {[MODEL_NAMES[i] for i in missing]}")
out.append(f"comment claims '7 models'; loop actually launches {len(launched)} models -> off-by-one = {len(launched) != len(fi_indices)}")

text = "\n".join(out)
print(text)
here = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(here, "out", "semisup_index_range.txt"), "w") as f:
    f.write(text + "\n")
