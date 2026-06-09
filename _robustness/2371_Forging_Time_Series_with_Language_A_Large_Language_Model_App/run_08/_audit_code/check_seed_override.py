"""Checks whether the config `seed` reaches the SDForger LLM (supports finding sdforger-seed-hardcoded).
Read-only static check: confirms sdforger_augmentation constructs SDForger() without a seed kwarg,
so SDForger.__init__ falls back to its default seed=42 for the LLM fine-tuning/generation RNG.
"""
import re, os, json

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CODE = os.path.join(ROOT, "code", "SDForger__neurips_supplemental")

aug = open(os.path.join(CODE, "utils/augmentation/sdforger_augmentation.py")).read()
core = open(os.path.join(CODE, "utils/augmentation/sdforger.py")).read()

# 1. The SDForger(...) constructor call inside sdforger_augmentation
m = re.search(r"SDForger\((.*?)\)", aug, re.S)
ctor_call = m.group(0) if m else "NOT FOUND"
ctor_has_seed = bool(m and "seed" in m.group(1))

# 2. Default seed fallback in SDForger.__init__
default_seed_line = next((l.strip() for l in core.splitlines()
                          if "self.seed" in l and "kwargs" in l and "42" in l), "NOT FOUND")

# 3. set_seed() is called in __init__ (resets RNG to self.seed)
calls_set_seed_in_init = "self.set_seed()" in core

out = {
    "sdforger_constructor_call": " ".join(ctor_call.split()),
    "constructor_passes_seed": ctor_has_seed,
    "default_seed_fallback_line": default_seed_line,
    "init_calls_set_seed": calls_set_seed_in_init,
    "verdict": ("config 'seed' is NOT propagated to SDForger; LLM RNG is hardcoded to default 42"
                if (not ctor_has_seed and "42" in default_seed_line and calls_set_seed_in_init)
                else "seed appears to be propagated"),
}
os.makedirs(os.path.join(os.path.dirname(__file__), "out"), exist_ok=True)
with open(os.path.join(os.path.dirname(__file__), "out", "seed_override.json"), "w") as f:
    json.dump(out, f, indent=2)
print(json.dumps(out, indent=2))
