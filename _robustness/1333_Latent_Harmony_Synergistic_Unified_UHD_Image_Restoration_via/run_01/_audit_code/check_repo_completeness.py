"""Static completeness scan: restoration network R_theta usage, test/eval entrypoints,
dependency spec, datasets, pretrained weights. Supports findings 'no-restoration-network',
'no-test-eval-script', 'no-dependency-spec', 'no-data-or-weights'. Read-only."""
import os, re, glob, json

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "code", "lyd-2022__Latent-Harmony"))

def find(patterns):
    hits = []
    for pat in patterns:
        for p in glob.glob(os.path.join(REPO, "**", pat), recursive=True):
            if "__pycache__" in p:
                continue
            hits.append(os.path.relpath(p, REPO))
    return sorted(set(hits))

# 1) restoration network R_theta: look for any usage where a separate restoration net
# (SFHformer/NAFNet/Restormer-as-restoration) is instantiated/applied to a latent in models.
rtheta_terms = ["sfhformer", "nafnet", "net_r ", "net_res", "restoration_net",
                "rtheta", "r_theta", "self.net_r", "build_network(self.opt['network_r"]
rtheta_hits = []
for p in glob.glob(os.path.join(REPO, "basicsr", "models", "*.py")):
    with open(p) as f:
        txt = f.read().lower()
    for t in rtheta_terms:
        if t in txt:
            rtheta_hits.append((os.path.relpath(p, REPO), t))

# What does stage-2 forward feed to the decoder? quote the forward path.
with open(os.path.join(REPO, "basicsr", "models", "VAEadapter_model.py")) as f:
    vae_adapter = f.read()
forward_uses_only_vae = "out = self.net_g(self.lq" in vae_adapter and "Rθ" not in vae_adapter

# 2) test / eval / inference entrypoints
test_scripts = find(["*test*.py", "*infer*.py", "*eval*.py", "demo*.py"])
# exclude metric impl files that merely contain 'test' in path text
test_scripts = [t for t in test_scripts if "metrics" not in t]

# 3) dependency spec
dep_files = find(["requirements*.txt", "setup.py", "setup.cfg", "pyproject.toml",
                  "environment*.yml", "environment*.yaml", "Dockerfile", "Pipfile", "conda*.yml"])

# 4) datasets / weights
data_dirs = [d for d in ["datasets", "weights", "data", "checkpoints", "pretrained"]
             if os.path.isdir(os.path.join(REPO, d))]
weight_files = find(["*.pth", "*.ckpt", "*.pt", "*.safetensors"])
image_files = find(["*.png", "*.jpg", "*.jpeg"])

out = {
    "rtheta_hits_in_models": rtheta_hits,
    "stage2_forward_feeds_only_vae(no_Rtheta)": forward_uses_only_vae,
    "test_eval_infer_scripts": test_scripts,
    "dependency_spec_files": dep_files,
    "data_or_weight_dirs": data_dirs,
    "weight_files": weight_files,
    "image_files": image_files,
}
outpath = os.path.join(os.path.dirname(__file__), "out", "repo_completeness.json")
with open(outpath, "w") as f:
    json.dump(out, f, indent=2)
print(json.dumps(out, indent=2))
