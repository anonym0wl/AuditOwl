"""Re-run build_coverage_figure.py's parse_audit+classify+collect logic READ-ONLY (no file writes) and diff the recomputed coverage_status totals against the committed _summary/data/coverage_status.json, to confirm the 1009-artifact / 44%-missing / 87-47-9 funnel reproduces from the audit.md coverage tables. Supports findings: coverage-traceability, funnel-reproduces."""
import json, glob, os, statistics, importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "code" / "anonym0wl__AuditOwl"

# import the repo's own build_coverage_figure module without running main()
spec = importlib.util.spec_from_file_location("bcf", ROOT / "_summary" / "build_coverage_figure.py")
# It imports matplotlib at top; guard
try:
    bcf = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bcf)
except Exception as e:
    print("could not import module directly:", e)
    raise

# monkeypatch its ROOT to the cloned repo (it set ROOT to its own parent.parent which is correct here)
bcf.ROOT = ROOT
papers = bcf.collect()
real = [p for p in papers if not p.get("is_nocode")]
n_nocode = len(papers) - len(real)
from collections import Counter
totals = {k: sum(p["counts"][k] for p in real) for k in bcf.COL}
recomputed = {
    "n_papers": len(papers),
    "n_nocode_papers": n_nocode,
    "n_artefacts": sum(p["traced"] for p in real),
    "totals_by_status": totals,
    "median_missing_frac": statistics.median([p["missing_frac"] for p in real]),
}
committed = json.load(open(ROOT / "_summary" / "data" / "coverage_status.json"))

print("=== RECOMPUTED (read-only re-parse of audit.md tables) ===")
for k in ["n_papers", "n_nocode_papers", "n_artefacts"]:
    print(f"  {k}: recomputed={recomputed[k]}  committed={committed[k]}  match={recomputed[k]==committed[k]}")
print(f"  totals_by_status recomputed: {recomputed['totals_by_status']}")
print(f"  totals_by_status committed:  {committed['totals_by_status']}")
print(f"  median_missing_frac recomputed={recomputed['median_missing_frac']:.4f} committed={committed['median_missing_frac']:.4f}")

# funnel
print("\n=== FUNNEL (from recomputed real papers) ===")
print(f"  empirical papers: {len(papers)}")
print(f"  source code present: {len(real)}")
print(f"  >50% traced (missing_frac<0.5): {sum(p['missing_frac']<0.5 for p in real)}")
print(f"  every artifact traced (missing_frac==0): {sum(p['missing_frac']==0.0 for p in real)}")
print(f"  mean missing_frac over real: {statistics.mean([p['missing_frac'] for p in real]):.4f}")
