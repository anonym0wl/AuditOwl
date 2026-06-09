"""Deterministic scan of the whole repo for code implementing three paper artefacts:
(1) feature-level attribution / explainability validation (Table 3: ExactMatch, Jaccard, top-k);
(2) statistical tests (Appendix D.5: Friedman, Nemenyi, critical-difference);
(3) the unsupervised CSM epoch-selection procedure (Appendix B.3/B.6, Li et al. 2025b).
Prints which keyword sets have ZERO hits across all .py files. Read-only."""
import os, re, csv

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "code", "ZhongLIFR__TCCM-NIPS"))

groups = {
    "explainability_table3": [r"exactmatch", r"exact_match", r"jaccard", r"top.?k feature",
                              r"topk", r"top_k", r"argsort", r"feature.?importance",
                              r"feature.?wise", r"attribution"],
    "stat_tests_D5": [r"friedman", r"nemenyi", r"critical difference", r"\bcrit_dist\b",
                      r"wilcoxon", r"demsar", r"posthoc", r"scikit_posthocs", r"\bCD\b diagram"],
    "csm_epoch_selection": [r"\bcsm\b", r"contrast score", r"margin", r"select.{0,12}epoch",
                            r"epoch.{0,12}select", r"internal evaluation", r"Li et al"],
}

# gather all py files
pyfiles = []
for root, _, files in os.walk(REPO):
    if ".git" in root:
        continue
    for f in files:
        if f.endswith(".py"):
            pyfiles.append(os.path.join(root, f))

rows = []
for gname, pats in groups.items():
    total_hits = 0
    hit_detail = []
    for pf in pyfiles:
        txt = open(pf, errors="ignore").read()
        for pat in pats:
            for m in re.finditer(pat, txt, re.IGNORECASE):
                # exclude obvious false positives: 'CD' as pyod model, 'top10', comments listing baseline names
                line = txt[:m.start()].count("\n") + 1
                snippet = txt.splitlines()[line-1].strip()[:80]
                total_hits += 1
                hit_detail.append((os.path.relpath(pf, REPO), line, pat, snippet))
    rows.append((gname, total_hits))
    print(f"\n=== {gname}: {total_hits} hits ===")
    for d in hit_detail[:20]:
        print(f"   {d[0]}:{d[1]}  /{d[2]}/  -> {d[3]}")
    if total_hits == 0:
        print("   >>> ABSENT: no code implements this artefact <<<")

out_csv = os.path.join(os.path.dirname(__file__), "out", "missing_experiments.csv")
with open(out_csv, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["artefact_group", "total_keyword_hits_in_repo"])
    w.writerows(rows)
print(f"\nScanned {len(pyfiles)} .py files. Wrote {out_csv}")
