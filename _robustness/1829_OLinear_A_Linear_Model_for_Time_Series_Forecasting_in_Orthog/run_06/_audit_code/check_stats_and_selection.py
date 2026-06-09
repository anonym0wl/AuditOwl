"""Checks (read-only) for OLinear audit: (1) no std/CI/t-test computation code exists for
Tables 13/14/15/26; (2) requirements.txt is unpinned and lists 'pywt' (wrong PyPI name);
(3) run.py best-of-itr test-set selection exists. Supports findings: missing-stats-code,
unpinned-deps-pywt, best-of-itr-test-selection."""
import os, re, json

REPO = os.path.join(os.path.dirname(__file__), "..", "code", "jackyue1994__OLinear")
REPO = os.path.abspath(REPO)
out = {}

# (1) search every .py / .ipynb for any statistical-test / std / CI keyword
stat_pat = re.compile(r"ttest|t_test|stats\.t|scipy|np\.std|numpy\.std|\.std\(|confidence|wilcoxon|p_value|pvalue", re.I)
hits = []
for root, _, files in os.walk(REPO):
    if "__pycache__" in root:
        continue
    for fn in files:
        if fn.endswith((".py", ".ipynb")):
            p = os.path.join(root, fn)
            try:
                txt = open(p, encoding="utf-8", errors="ignore").read()
            except Exception:
                continue
            for m in stat_pat.finditer(txt):
                ln = txt[:m.start()].count("\n") + 1
                hits.append((os.path.relpath(p, REPO), ln, m.group(0)))
out["stat_keyword_hits"] = hits
out["n_stat_hits"] = len(hits)

# (2) requirements.txt
req_path = os.path.join(REPO, "requirements.txt")
req_lines = [l.strip() for l in open(req_path).read().splitlines() if l.strip()]
out["requirements"] = req_lines
out["any_pinned"] = any(re.search(r"[=<>~]", l) for l in req_lines)
out["lists_pywt_exact"] = "pywt" in req_lines

# (3) run.py best-of-itr test selection
run_txt = open(os.path.join(REPO, "run.py")).read().splitlines()
sel_lines = [(i+1, l.rstrip()) for i, l in enumerate(run_txt)
             if "best_mse + best_mae" in l or "if mse0 < mse" in l or "best_mse, best_mae, best_ii" in l]
out["run_py_selection_lines"] = sel_lines

os.makedirs(os.path.join(os.path.dirname(__file__), "out"), exist_ok=True)
with open(os.path.join(os.path.dirname(__file__), "out", "stats_and_selection.json"), "w") as f:
    json.dump(out, f, indent=2)

print("n_stat_keyword_hits:", out["n_stat_hits"])
print("stat hits:", hits)
print("requirements any_pinned:", out["any_pinned"], "| lists 'pywt' exactly:", out["lists_pywt_exact"])
print("run.py selection lines:")
for ln, t in sel_lines:
    print(f"  L{ln}: {t.strip()}")
