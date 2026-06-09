"""Greps the repo for code producing each paper figure/result; supports missing-figure findings. Read-only."""
import os, subprocess

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "code", "ZhongLIFR__TCCM-NIPS"))

def grep(pattern):
    r = subprocess.run(["grep", "-rniE", pattern, "--include=*.py", "."],
                       cwd=REPO, capture_output=True, text=True)
    return [l for l in r.stdout.splitlines()]

checks = {
    "Figure_12_time_embedding": "Time_Embedding_Figure_12",
    "Figure_13_sensitivity_t": "Sensitivity_t_Figure_13",
    "Figure_14_noise": "Noise_Injection_Figure_14",
    "Figure_15_contamination_ablation": "Contamination_Figure_TCCM|Figure_15",
    "Figure_16_feature_normalization_ABLATION": "Figure_16",
    "Figure_17_time_interpolated_inputs": "Figure_17",
    "Autoencoder_plus_TimeEmbedding_comparison": "autoencoder.*time|reconstruction.*ablat",
    "Figure_4_explainability_mnist_digit": "Figure_4|explain|feature.*contribut|imshow.*score",
}

out = os.path.join(os.path.dirname(__file__), "out", "missing_artifacts.txt")
with open(out, "w") as f:
    for label, pat in checks.items():
        hits = grep(pat)
        status = "FOUND" if hits else "NOT FOUND"
        f.write(f"{label}: {status} ({len(hits)} hits)\n")
        for h in hits[:5]:
            f.write(f"    {h}\n")
        print(f"{label}: {status} ({len(hits)} hits)")
