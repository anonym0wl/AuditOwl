"""Confirms that tqdm/patoolib are on the import-time critical path of every
experiment yet absent from requirements.txt. Supports finding
'unlisted-deps-patoolib-tqdm'. Read-only: only greps source files."""
import os
import re

REPO = os.path.join(os.path.dirname(__file__), "..", "code", "jackyue1994__OLinear")


def grep(path, pattern):
    p = os.path.join(REPO, path)
    hits = []
    with open(p) as f:
        for i, line in enumerate(f, 1):
            if re.search(pattern, line):
                hits.append((i, line.rstrip("\n")))
    return hits


def main():
    rows = []
    # 1) m4.py imports the deps at top level
    rows.append("m4.py imports:")
    for i, l in grep("data_provider/m4.py", r"import (patoolib|tqdm)|from tqdm"):
        rows.append(f"  m4.py:{i}: {l}")
    # 2) import chain pulling m4 into every run
    rows.append("import chain (run -> exp_forecast -> data_factory -> data_loader -> m4):")
    for i, l in grep("data_provider/data_loader.py", r"from data_provider\.m4 import"):
        rows.append(f"  data_loader.py:{i}: {l}")
    for i, l in grep("data_provider/data_factory.py", r"from \.data_loader import"):
        rows.append(f"  data_factory.py:{i}: {l}")
    for i, l in grep("experiments/exp_forecast.py", r"from data_provider\.data_factory import"):
        rows.append(f"  exp_forecast.py:{i}: {l}")
    for i, l in grep("run.py", r"from experiments\.exp_forecast import"):
        rows.append(f"  run.py:{i}: {l}")
    # 3) requirements.txt does NOT list them
    req = os.path.join(REPO, "requirements.txt")
    with open(req) as f:
        reqs = f.read().lower()
    rows.append("requirements.txt presence:")
    for pkg in ("tqdm", "patool", "pyunpack", "pywavelets"):
        rows.append(f"  {pkg}: {'PRESENT' if pkg in reqs else 'ABSENT'}")
    rows.append(f"requirements.txt raw lines: {sorted(l.strip() for l in open(req) if l.strip())}")

    out = os.path.join(os.path.dirname(__file__), "out", "imports.txt")
    with open(out, "w") as f:
        f.write("\n".join(rows) + "\n")
    print("\n".join(rows))


if __name__ == "__main__":
    main()
