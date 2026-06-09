"""Inventory the repo for the artefacts a complete submission needs (supports
findings `no-eval-or-metric-code`, `no-deps-spec`, `missing-weights-and-data`,
`no-restoration-network-rtheta`). Read-only; pure filesystem scan, no imports
of the repo.
"""
import os
import json

REPO = os.path.join(os.path.dirname(__file__), "..", "code", "lyd-2022__Latent-Harmony")
REPO = os.path.abspath(REPO)


def walk_py():
    for root, _, files in os.walk(REPO):
        if "__pycache__" in root:
            continue
        for f in files:
            yield os.path.join(root, f)


def main():
    all_files = list(walk_py())
    rel = [os.path.relpath(p, REPO) for p in all_files]

    # dependency spec
    dep_specs = [r for r in rel if os.path.basename(r).lower() in
                 ("requirements.txt", "environment.yml", "environment.yaml",
                  "setup.py", "pyproject.toml", "setup.cfg", "conda.yaml")]

    # eval / test / inference scripts
    eval_like = [r for r in rel if any(k in os.path.basename(r).lower()
                 for k in ("test_", "eval", "infer", "demo", "predict"))
                 and r.endswith(".py")]
    # exclude metric-definition files (they only define metrics, not run eval)
    eval_like = [r for r in eval_like if not r.startswith("basicsr/metrics")]

    # download / data prep scripts
    download_like = [r for r in rel if any(k in os.path.basename(r).lower()
                     for k in ("download", "prepare", "fetch", "make_dataset"))]

    # shell run scripts
    sh = [r for r in rel if r.endswith(".sh")]

    # weights / checkpoints (exclude the niqe params shipped with basicsr)
    weights = [r for r in rel if r.endswith((".pth", ".ckpt", ".pt",
               ".safetensors")) and "niqe" not in r]

    # readme content
    readme = os.path.join(REPO, "README.md")
    readme_text = open(readme).read() if os.path.exists(readme) else ""
    readme_lines = [l for l in readme_text.splitlines() if l.strip()]

    report = {
        "total_files": len(rel),
        "py_files": len([r for r in rel if r.endswith(".py")]),
        "dependency_specs": dep_specs,
        "eval_test_infer_scripts": eval_like,
        "download_dataprep_scripts": download_like,
        "shell_scripts": sh,
        "model_weight_files (excl niqe)": weights,
        "readme_nonblank_lines": readme_lines,
        "datasets_dir_exists": os.path.isdir(os.path.join(REPO, "datasets")),
        "weights_dir_exists": os.path.isdir(os.path.join(REPO, "weights")),
    }

    print(json.dumps(report, indent=2))
    out = os.path.join(os.path.dirname(__file__), "out", "completeness.json")
    with open(out, "w") as fh:
        json.dump(report, fh, indent=2)
    print(f"\nWritten to {out}")


if __name__ == "__main__":
    main()
