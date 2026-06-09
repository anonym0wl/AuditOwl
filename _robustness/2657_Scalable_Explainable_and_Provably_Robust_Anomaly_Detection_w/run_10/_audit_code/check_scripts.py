"""Deterministic checks: (1) run_knn.sh references a non-existent script;
(2) run_semisupervise.sh model-index range omits KNN_semisup (index 51).
Supports findings run-knn-wrong-script and semisup-missing-knn."""
import os, re
ROOT = os.path.join(os.path.dirname(__file__), "..", "code", "ZhongLIFR__TCCM-NIPS")
out = []

# (1) Does run_knn.sh call a file that exists?
knn = open(os.path.join(ROOT, "bash_files", "run_knn.sh")).read()
called = sorted(set(re.findall(r'python\s+(\S+\.py)', knn)))
out.append(f"run_knn.sh invokes python scripts: {called}")
for s in called:
    out.append(f"  exists({s}) = {os.path.isfile(os.path.join(ROOT, s))}")

# (2) Model index range in run_semisupervise.sh vs force_inductive count
semi = open(os.path.join(ROOT, "bash_files", "run_semisupervise.sh")).read()
ranges = re.findall(r'for j in \{(\d+)\.\.(\d+)\}', semi)
out.append(f"run_semisupervise.sh j-ranges: {ranges}")
# Reconstruct MODEL_NAMES order
deep=['TCCM','VAE','SO_GAAL','MO_GAAL','AutoEncoder','DeepSVDD','LUNAR','DIF','ALAD','AE1SVM','AnoGAN']
trans=['ABOD','COF','LOF','PCA','KPCA','KNN','INNE']
induc=['CBLOF','IForest','LODA','FeatureBagging','Sampling','MCD','CD','ECOD','HBOS','OCSVM','KDE','GMM','QMCD','LMDD']
add=['DAGMM','GANomaly','NormalizingFlow','DROCC','DTEDDPM','DTEGaussian','DTEInverseGamma','DTECategorical','DTENonParametric','ICL','GOAD','SLAD','MCM']
fi=['ABOD_semisup','COF_semisup','LOF_semisup','PCA_semisup','KPCA_semisup','INNE_semisup','KNN_semisup']
names=deep+trans+induc+add+fi
covered=set()
for lo,hi in ranges:
    covered.update(range(int(lo),int(hi)+1))
fi_indices = {i for i,n in enumerate(names) if n in fi}
out.append(f"force_inductive indices = {sorted(fi_indices)} -> {[names[i] for i in sorted(fi_indices)]}")
missing = sorted(fi_indices - covered)
out.append(f"force_inductive indices NOT covered by run_semisupervise.sh = {missing} -> {[names[i] for i in missing]}")
# run_knn.sh j range
kr = re.findall(r'for j in \{(\d+)\.\.(\d+)\}', knn)
out.append(f"run_knn.sh j-ranges: {kr} -> model at j=50 is '{names[50]}' (NOT KNN_semisup at 51)")

txt="\n".join(out)
print(txt)
open(os.path.join(os.path.dirname(__file__),"out","check_scripts.txt"),"w").write(txt+"\n")
