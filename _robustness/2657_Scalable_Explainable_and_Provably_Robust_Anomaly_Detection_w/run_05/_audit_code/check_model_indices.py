"""Reconstruct MODEL_NAMES ordering and index ranges used by bash files."""
deep_models = ["TCCM","VAE","SO_GAAL","MO_GAAL","AutoEncoder","DeepSVDD","LUNAR","DIF","ALAD","AE1SVM","AnoGAN"]
transductive_models = ["ABOD","COF","LOF","PCA","KPCA","KNN","INNE"]
inductive_models = ["CBLOF","IForest","LODA","FeatureBagging","Sampling","MCD","CD","ECOD","HBOS","OCSVM","KDE","GMM","QMCD","LMDD"]
additional_models = ["DAGMM","GANomaly","NormalizingFlow","DROCC","DTEDDPM","DTEGaussian","DTEInverseGamma","DTECategorical","DTENonParametric","ICL","GOAD","SLAD","MCM"]
force_inductive_models = ["ABOD_semisup","COF_semisup","LOF_semisup","PCA_semisup","KPCA_semisup","INNE_semisup","KNN_semisup"]
# NOTE: in utils.py order, force_inductive dict order is ABOD,COF,LOF,PCA,KPCA,INNE,KNN  -> check both
MODEL_NAMES = deep_models + transductive_models + inductive_models + additional_models + force_inductive_models
print("len deep:", len(deep_models), "trans:", len(transductive_models), "ind:", len(inductive_models), "add:", len(additional_models), "force:", len(force_inductive_models))
print("Total MODEL_NAMES:", len(MODEL_NAMES))
print("Indices 0..44 (run_main 45 models):")
for i in range(0,45):
    print(f"  {i}: {MODEL_NAMES[i]}")
print("Force-inductive indices:")
for i in range(45, len(MODEL_NAMES)):
    print(f"  {i}: {MODEL_NAMES[i]}")
print("\nrun_semisupervise uses j in {45..50} -> 6 indices; force_inductive count is", len(force_inductive_models))
print("Index 51 (omitted by semisup if present):", MODEL_NAMES[51] if len(MODEL_NAMES)>51 else "N/A")
print("\nKNN is at index:", MODEL_NAMES.index("KNN"))
print("run_knn.sh uses j in {50..50} = index 50 =", MODEL_NAMES[50])
