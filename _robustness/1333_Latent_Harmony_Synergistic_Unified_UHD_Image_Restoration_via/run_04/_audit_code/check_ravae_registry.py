"""Checks that stage2 config's vae_config.type ('RAVAE') is NOT registered in
ARCH_REGISTRY, while only 'RAVAE_EQ' is. Supports finding: stage2-ravae-not-registered.

Static analysis only (no heavy imports): scans the arch source files for classes
decorated with @ARCH_REGISTRY.register() and compares against the type names that
the YAML configs request.
"""
import ast
import os
import re

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "code", "lyd-2022__Latent-Harmony"))
ARCHS_DIR = os.path.join(REPO, "basicsr", "archs")
CONFIGS_DIR = os.path.join(REPO, "configs")
OUT = os.path.join(os.path.dirname(__file__), "out", "ravae_registry.txt")


def is_register_deco(dec):
    # matches @ARCH_REGISTRY.register() and @ARCH_REGISTRY.register
    if isinstance(dec, ast.Call):
        dec = dec.func
    if isinstance(dec, ast.Attribute):
        return dec.attr == "register" and isinstance(dec.value, ast.Name) and dec.value.id == "ARCH_REGISTRY"
    return False


def registered_arch_names():
    names = set()
    # only *_arch.py files are auto-imported by basicsr/archs/__init__.py
    for fn in os.listdir(ARCHS_DIR):
        if not fn.endswith("_arch.py"):
            continue
        path = os.path.join(ARCHS_DIR, fn)
        with open(path) as f:
            tree = ast.parse(f.read(), filename=path)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for dec in node.decorator_list:
                    if is_register_deco(dec):
                        names.add(node.name)
    return names


def config_vae_types():
    types = {}
    for fn in os.listdir(CONFIGS_DIR):
        path = os.path.join(CONFIGS_DIR, fn)
        with open(path) as f:
            txt = f.read()
        # collect all 'type: X' under network_g / vae_config
        for m in re.finditer(r"type:\s*([A-Za-z0-9_]+)", txt):
            types.setdefault(fn, []).append(m.group(1))
    return types


def main():
    registered = registered_arch_names()
    cfg_types = config_vae_types()
    lines = []
    lines.append(f"Registered arch classes (from *_arch.py): {sorted(registered)}")
    lines.append("")
    lines.append("Config 'type:' values:")
    for fn, ts in cfg_types.items():
        lines.append(f"  {fn}: {ts}")
    lines.append("")
    ravae_registered = "RAVAE" in registered
    ravae_eq_registered = "RAVAE_EQ" in registered
    lines.append(f"'RAVAE' registered?    {ravae_registered}")
    lines.append(f"'RAVAE_EQ' registered? {ravae_eq_registered}")
    # stage2 config requests RAVAE under vae_config
    stage2 = cfg_types.get("stage2_hflora.yml", [])
    lines.append(f"stage2_hflora.yml requests types: {stage2}")
    verdict = "BUG" if (("RAVAE" in stage2) and not ravae_registered) else "OK"
    lines.append(f"VERDICT: {verdict} (stage2 requests RAVAE but it is not registered)")
    out = "\n".join(lines)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        f.write(out + "\n")
    print(out)


if __name__ == "__main__":
    main()
