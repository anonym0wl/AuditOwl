"""Checks (a) no statistical-test/std/CI code exists for Tables 13/14/15/26 and
(b) the single hardcoded seed / no seed-sweep, supporting findings
no-significance-test-code and no-seed-sweep-code. Read-only over code/."""
import os, re, json

REPO = os.path.join(os.path.dirname(__file__), "..", "code", "jackyue1994__OLinear")
REPO = os.path.abspath(REPO)

stat_patterns = re.compile(r"ttest|t_test|ttest_rel|ttest_ind|scipy|stats\.t|"
                           r"confidence|conf_int|np\.std\(|\.std\(|significan|"
                           r"interval", re.IGNORECASE)
seed_patterns = re.compile(r"seed", re.IGNORECASE)

stat_hits, seed_hits = [], []
py_files = []
for root, _, files in os.walk(REPO):
    if "__pycache__" in root or "/.git" in root:
        continue
    for fn in files:
        if fn.endswith(".py"):
            p = os.path.join(root, fn)
            py_files.append(p)
            with open(p, encoding="utf-8", errors="ignore") as fh:
                for i, line in enumerate(fh, 1):
                    if stat_patterns.search(line):
                        stat_hits.append((os.path.relpath(p, REPO), i, line.strip()))
                    if seed_patterns.search(line):
                        seed_hits.append((os.path.relpath(p, REPO), i, line.strip()))

# Count distinct seed VALUES set in run.py
seed_values = set()
with open(os.path.join(REPO, "run.py"), encoding="utf-8") as fh:
    for line in fh:
        m = re.search(r"fix_seed\s*=\s*(\d+)", line)
        if m:
            seed_values.add(m.group(1))

out = {
    "n_py_files": len(py_files),
    "statistical_test_hits": stat_hits,
    "n_statistical_test_hits": len(stat_hits),
    "distinct_hardcoded_seed_values_in_run_py": sorted(seed_values),
    "seed_setting_lines": [s for s in seed_hits if s[0] == "run.py"],
}
with open(os.path.join(os.path.dirname(__file__), "out", "stats_seed.json"), "w") as fh:
    json.dump(out, fh, indent=2)
print(json.dumps(out, indent=2))
