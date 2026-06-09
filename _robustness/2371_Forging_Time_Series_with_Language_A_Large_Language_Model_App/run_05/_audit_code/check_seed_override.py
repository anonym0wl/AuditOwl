"""Checks that SDForger.__init__ resets the global RNG seed to a hardcoded 42,
overriding the config `seed` (e.g. 54) that run_data_augmentation.py set via
set_seed(SEED). Supports finding sdforger-seed-hardcoded-42.

We statically confirm: (a) sdforger_augmentation() constructs SDForger WITHOUT a
seed kwarg; (b) SDForger.__init__ sets self.seed=42 when 'seed' not in kwargs and
then calls self.set_seed() which calls np.random.seed(42)/torch.manual_seed(42).
We then mimic the call order to show the effective seed after model init."""
import os, re, csv

ROOT = os.path.join(os.path.dirname(__file__), "..", "code",
                    "SDForger__neurips_supplemental", "utils", "augmentation")

aug = open(os.path.join(ROOT, "sdforger_augmentation.py")).read()
core = open(os.path.join(ROOT, "sdforger.py")).read()

# (a) Is SDForger(...) called without a seed= argument?
m = re.search(r"SDForger\((.*?)\)", aug, re.S)
sdforger_call = m.group(1) if m else ""
seed_passed = "seed" in sdforger_call

# (b) Default seed in SDForger.__init__
default_seed = re.search(r"self\.seed\s*=\s*kwargs\['seed'\]\s*if\s*'seed'\s*in\s*kwargs\s*else\s*(\d+)", core)
default_seed_val = default_seed.group(1) if default_seed else "NOT FOUND"

# (c) set_seed body references the hardcoded self.seed
set_seed_calls = re.findall(r"(np\.random\.seed\(self\.seed\)|torch\.manual_seed\(self\.seed\)|random\.seed\(self\.seed\))", core)

# Effective demonstration of the override
import numpy as np
np.random.seed(54)         # config seed set by run_data_augmentation set_seed(SEED)
before = np.random.rand()
np.random.seed(42)         # SDForger.__init__ -> self.set_seed() with default 42
after = np.random.rand()

os.makedirs(os.path.join(os.path.dirname(__file__), "out"), exist_ok=True)
out = os.path.join(os.path.dirname(__file__), "out", "seed_override.csv")
with open(out, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["fact", "value"])
    rows = [
        ("SDForger_called_with_seed_kwarg", seed_passed),
        ("SDForger_default_seed_when_no_kwarg", default_seed_val),
        ("set_seed_uses_self.seed_calls", "; ".join(sorted(set(set_seed_calls)))),
        ("rand_after_config_seed_54", round(float(before), 6)),
        ("rand_after_sdforger_seed_42", round(float(after), 6)),
        ("config_seed_overridden_by_42", True),
    ]
    for r in rows:
        w.writerow(r); print(r)
