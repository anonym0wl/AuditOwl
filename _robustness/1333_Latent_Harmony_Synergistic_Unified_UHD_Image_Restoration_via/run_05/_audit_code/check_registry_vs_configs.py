"""Check that every network/model `type:` named in the YAML configs is actually
registered in the repo (supports finding `stage2-ravae-arch-missing`).

Statically scans basicsr/ for class names registered via @ARCH_REGISTRY.register()
and @MODEL_REGISTRY.register(), then checks the `type:` fields in the configs.
Read-only; does not import torch.
"""
import ast
import os
import re
import json

REPO = os.path.join(os.path.dirname(__file__), "..", "code", "lyd-2022__Latent-Harmony")
REPO = os.path.abspath(REPO)


def registered_names():
    """Return {'arch': set(), 'model': set(), 'loss': set(), 'dataset': set(), 'metric': set()}."""
    out = {"arch": set(), "model": set(), "loss": set(), "dataset": set(), "metric": set()}
    reg_map = {
        "ARCH_REGISTRY": "arch",
        "MODEL_REGISTRY": "model",
        "LOSS_REGISTRY": "loss",
        "DATASET_REGISTRY": "dataset",
        "METRIC_REGISTRY": "metric",
    }
    for root, _, files in os.walk(REPO):
        if "__pycache__" in root:
            continue
        for f in files:
            if not f.endswith(".py"):
                continue
            path = os.path.join(root, f)
            try:
                src = open(path, encoding="utf-8").read()
                tree = ast.parse(src)
            except Exception:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    for dec in node.decorator_list:
                        # decorator like ARCH_REGISTRY.register()
                        reg = None
                        if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute):
                            if isinstance(dec.func.value, ast.Name):
                                reg = dec.func.value.id
                        elif isinstance(dec, ast.Attribute) and isinstance(dec.value, ast.Name):
                            reg = dec.value.id
                        if reg in reg_map:
                            out[reg_map[reg]].add(node.name)
    return out


def types_in_config(path):
    """Return list of (key_context, type_value) found via simple regex on a yml file."""
    found = []
    for ln in open(path, encoding="utf-8"):
        m = re.search(r"^\s*type:\s*([A-Za-z_][\w]*)\s*$", ln)
        if m:
            found.append(m.group(1))
    return found


def main():
    reg = registered_names()
    # All registry names we might reference as a network arch or model
    all_arch = reg["arch"]
    all_model = reg["model"]
    all_loss = reg["loss"]
    all_dataset = reg["dataset"]

    results = []
    cfg_dir = os.path.join(REPO, "configs")
    for cfg in sorted(os.listdir(cfg_dir)):
        if not cfg.endswith(".yml"):
            continue
        path = os.path.join(cfg_dir, cfg)
        types = types_in_config(path)
        for t in types:
            in_any = (
                t in all_arch or t in all_model or t in all_loss or t in all_dataset
            )
            results.append({
                "config": cfg,
                "type": t,
                "in_arch": t in all_arch,
                "in_model": t in all_model,
                "in_loss": t in all_loss,
                "in_dataset": t in all_dataset,
                "resolves": in_any,
            })

    print("Registered ARCH names:", sorted(all_arch))
    print("Registered MODEL names:", sorted(all_model))
    print("Registered LOSS names:", sorted(all_loss))
    print("Registered DATASET names:", sorted(all_dataset))
    print()
    print("=== config `type:` resolution ===")
    unresolved = []
    for r in results:
        flag = "OK " if r["resolves"] else "!! UNRESOLVED"
        print(f"{flag}  {r['config']:24s} type={r['type']}")
        if not r["resolves"]:
            unresolved.append(r)

    out_path = os.path.join(os.path.dirname(__file__), "out", "registry_check.json")
    with open(out_path, "w") as fh:
        json.dump({"results": results, "unresolved": unresolved,
                   "registered": {k: sorted(v) for k, v in reg.items()}}, fh, indent=2)
    print()
    print(f"UNRESOLVED COUNT: {len(unresolved)}  (written to {out_path})")


if __name__ == "__main__":
    main()
