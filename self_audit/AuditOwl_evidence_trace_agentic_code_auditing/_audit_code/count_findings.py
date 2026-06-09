"""Independently re-count findings totals from raw audits/*/findings.json + findings_verified.json, replicating aggregate.py's is_dropped() logic, to check the paper's 605/606/categories/evidence-trail headline numbers. Supports findings: total-count, category, evidence-trail, verifier-survival."""
import json, sys
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parent.parent / "code" / "anonym0wl__AuditOwl"

def is_dropped(f):
    return (f.get("verdict") == "reject"
            or f.get("supplement_verdict") == "false_positive"
            or f.get("provenance_verdict") == "false_positive")

def evidence_kind(ff):
    ff = ff or ""
    if ff.endswith(".pdf"): return "paper"
    if ff.startswith("http"): return "url"
    if "out/" in ff or (ff.endswith((".csv", ".txt")) and "check" in ff): return "script_output"
    if ff: return "code"
    return "none"

# Gather the 100 numbered paper dirs (exclude theory/excluded subgroupings counted separately)
audit_dirs = sorted([d for d in (ROOT / "audits").glob("*") if d.is_dir()])
numbered = [d for d in audit_dirs if d.name[0].isdigit()]
theory = sorted((ROOT / "audits" / "theory").glob("*/"))
excluded = sorted((ROOT / "audits" / "excluded_justified_no_code").glob("*/"))

print(f"numbered paper dirs: {len(numbered)}")
print(f"theory dirs: {len(theory)}  excluded_justified_no_code dirs: {len(excluded)}")

# Count code-present (has findings.json) among numbered
with_findings = [d for d in numbered if (d / "findings.json").exists()]
no_findings = [d for d in numbered if not (d / "findings.json").exists()]
print(f"numbered with findings.json (code present): {len(with_findings)}")
print(f"numbered without findings.json (no code): {len(no_findings)}")

# Aggregate findings — replicate aggregate.py: iterate metadata.txt, exclude theory subtree
all_findings = []
per_paper_counts = []
for meta in sorted((ROOT / "audits").glob("*/metadata.txt")):
    d = meta.parent
    if d.name == "theory" or d.parent.name == "theory":
        continue
    fjp = d / "findings.json"
    findings = json.loads(fjp.read_text()).get("findings", []) if fjp.exists() else []
    fvp = d / "findings_verified.json"
    if fvp.exists():
        vmap = {vf.get("id"): vf for vf in json.loads(fvp.read_text()).get("findings", [])}
        for f in findings:
            vf = vmap.get(f.get("id"), {})
            f["verdict"] = vf.get("verdict")
            f["supplement_verdict"] = vf.get("supplement_verdict")
            f["provenance_verdict"] = vf.get("provenance_verdict")
    all_findings.extend(findings)
    if findings:
        per_paper_counts.append((d.name, len(findings)))

N = len(all_findings)
SURV = [f for f in all_findings if not is_dropped(f)]
print(f"\n=== GROSS findings (all, pre-drop): {N} ===")
print(f"=== SURVIVING (not dropped by verifier/supplement/provenance): {len(SURV)} ===")
print(f"dropped: {N - len(SURV)}")

print("\nby_category (GROSS):", dict(Counter(f.get('category') for f in all_findings)))
print("by_category (SURV):", {c: sum(1 for f in SURV if f.get('category')==c) for c in ['missing','difference','bug','methodology']})
print("by_severity (GROSS):", dict(Counter(f.get('severity') for f in all_findings)))
print("by_severity (SURV):", dict(Counter(f.get('severity') for f in SURV)))

# Verifier survival from findings_verified.json directly
verdicts = Counter()
n_verified = 0
for fvp in sorted((ROOT / "audits").glob("*/findings_verified.json")):
    if fvp.parent.parent.name == "theory":
        continue
    vj = json.loads(fvp.read_text())
    for f in vj.get("findings", []):
        n_verified += 1
        verdicts[f.get("verdict")] += 1
survived = verdicts.get("keep",0) + verdicts.get("lowered",0)
print(f"\n=== VERIFIER: n_verified={n_verified}  verdicts={dict(verdicts)}  survived(keep+lowered)={survived} ===")

# Evidence trail (over GROSS all_findings, matching aggregate.py)
n_quote = sum(1 for f in all_findings if f.get("quote"))
n_code = sum(1 for f in all_findings if evidence_kind(f.get("file","")) == "code")
n_check = sum(1 for f in all_findings if f.get("check_script"))
print(f"\n=== evidence trail (denominator N={N}) ===")
print(f"quote-anchored: {n_quote}  ({100*n_quote/N:.1f}%)")
print(f"cites code location: {n_code}  ({100*n_code/N:.1f}%)")
print(f"backed by check_script: {n_check}  ({100*n_check/N:.1f}%)")

# Per-paper finding stats (code-releasing papers)
counts = [c for _, c in per_paper_counts]
counts_sorted = sorted(counts)
import statistics
print(f"\n=== per-paper (papers with findings, n={len(counts)}) ===")
print(f"total findings over these papers: {sum(counts)}")
print(f"mean per paper: {sum(counts)/len(counts):.3f}")
print(f"median: {statistics.median(counts)}  min: {min(counts)}  max: {max(counts)}")
# mean over 100 papers
print(f"mean over 100 papers (incl no-code as 0): {N/100:.3f}")
print(f"mean over 87 code papers: {N/87:.3f}")
print(f"surviving mean over 87: {len(SURV)/87:.3f}")
