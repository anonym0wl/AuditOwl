# Audit — AuditOwl: "Evaluating the evidence trace of NeurIPS 2025 contributions with agentic code auditing"

## Summary

This is a self ("inception") audit of the AuditOwl repository, which both implements the
agentic-audit pipeline the paper describes AND ships the audit data the paper's numbers are
computed from (`audits/*/findings.json`, `findings_verified.json`, `_summary/data/*.json`,
`_robustness/data/*.json`, `token_cost.json`). I audited the git-tracked tree at commit
`fa45b50` strictly read-only, and re-derived every headline quantity deterministically from
the released data rather than trusting the prose. My checks live in
`_audit_code/`: `count_findings.py` (re-totals all 87 `findings.json` + verifier verdicts →
`out/count_findings.txt`) and `recompute_coverage.py` (re-imports the repo's own
`build_coverage_figure.py` and re-parses every `audit.md` coverage table read-only →
`out/recompute_coverage.txt`). I also re-ran the repo's own scripts where they are
data-only: `random_list.py` (seed-42 sample reproduction), `print_funnel.py` (the headline
funnel), and `aggregate.py` (regenerates `figure_data.json`).

**Headline verdict: the paper's quantitative claims reconcile cleanly against the released
data.** I re-derived, independent of the prose, all of: 100 sampled / 87 code-present / 13
no-code; 606 raised → 605 surviving findings; the 4-way category split (missing 307,
mismatch 151, bug 96, methodology 51) and the 51%/25% discussion shares; the evidence-trail
fractions (99.8% quote-anchored, 86% code-located, 52% check-backed); the funnel 100→87→47→9;
the "44% missing" coverage; the 1,009 traced artifacts; Figure 2a per-paper prevalence
(79/38/43/29); the entire Figure S1 severity×confidence heatmap (134/7/0 · 201/42/3 ·
149/67/3); the scorecard percentages (87/66/78/24/74/77/83); the human-eval error rate
(5/80 = 6.25% ≈ 6.2%) with the exact 74/5/1 split; the robustness detection rates
(0.71/0.37/0.26, overall 0.38, n=14/30/36); and the cost/timing (6.9M tokens/paper,
509M+94M total, 9.8 min mean, 23.4 min longest). The sampling fully reproduces: the released
5,286-row frame + `seed=42` regenerates `list.csv` byte-for-byte, and all 106 audited folders
map to the first 106 positions of that draw. **No headline number failed to reconcile.**

The findings below are reproducibility-hygiene and internal-consistency issues, none of which
changes a conclusion: (1) two committed JSON files (`stats.json`, `funnel.json`) carry stale
50-paper numbers that contradict the paper and are read by nothing; (2) `aggregate.py`'s
install/runnable/scorecard rows and its alternate funnel cannot be regenerated from the public
release because they scan the git-ignored upstream `code/` trees; (3) two co-existing
definitions of "all results trace cleanly" (9 vs 6 papers) — the paper uses the looser 9; (4)
small paper-internal / README-vs-data wording mismatches (84% vs 86% code-located; README
$13/paper vs data $14/paper).

## Traceability table

| Paper artefact | Repo location | Computed value | Matches paper | Status |
|---|---|---|---|---|
| Abstract "100 randomly sampled empirical papers" | `random_list.py:34` (seed=42) + `neurips_2025_main_track.csv` (5,286 rows) → `list.csv` | seed-42 draw reproduces `list.csv` byte-for-byte; 106 audited dirs = first 106 draws | ✓ | Verified (`_audit_code/out/count_findings.txt`) |
| "N = 5,286 papers" frame | `neurips_2025_main_track.csv` | 5,286 data rows | ✓ | Verified |
| 100 → 87 code-present → 13 no-code | `audits/[0-9]*/findings.json` presence | 100 dirs, 87 with findings.json, 13 without | ✓ | Verified |
| "605 discrepancies … 605 survived" | `audits/*/findings_verified.json` (keep+lowered) | 606 gross, 605 survive (603 keep, 2 lower, 1 reject) | ✓ | Verified |
| "averaging 6.1 per paper" | 605/100 = 6.05 | 6.05 (≈6.1) | ≈ | Verified (rounding) |
| "median 7 (range 2–13)" | per-paper finding counts | median 7, min 2, max 13 | ✓ | Verified |
| Category split (Fig 2 / S1) | `figure_data.json:by_category` | missing 307, diff 151, bug 96, meth 51 | ✓ | Verified |
| "missing 51%", "mismatch 25%" (Discussion) | 307/605, 151/605 | 50.7%, 25.0% | ✓ | Verified |
| "1,009 result artifacts" | `coverage_status.json:n_artefacts` (parsed from audit.md tables) | 1,009 | ✓ | Verified (`recompute_coverage.txt`) |
| Funnel 100→87→47→9 (Fig 1) | `print_funnel.py` ← `coverage_status.json` | 100, 87, 47, 9 | ✓ | Verified |
| "44% of traced artifacts missing" (Fig 3 / Disc.) | `coverage_status.json` mean/median missing_frac | mean 0.434 / median 0.444 | ✓ | Verified |
| "9 of 100 substantiate every result" | `coverage_status.json` missing_frac==0 | 9 | ✓ | Verified |
| Evidence: 99.8% quote-anchored | `aggregate.py:546` n_quote/N | 605/606 = 99.8% | ✓ | Verified |
| Evidence: "84%"/"86%" code-located | `aggregate.py:547` evidence_kind=="code" | 519/606 = 85.6% | ✗ (paper §4.1 says 84%) | MISMATCH → finding `code-located-pct-84-vs-86` |
| Evidence: "52%" check-backed | `aggregate.py:548` n_check/N | 315/606 = 52.0% | ✓ | Verified |
| Fig 2a prevalence 79/38/43/29 (excl. low sev) | per-paper surviving findings by category | 79, 38, 43, 29 of 87 | ✓ | Verified |
| Fig S1 heatmap cells | `audits/*/findings.json` sev×conf (gross) | high[134,7,0] med[201,42,3] low[149,67,3] | ✓ | Verified |
| "no high-sev finding at low confidence" | sev=high ∧ conf=low | 0 | ✓ | Verified |
| Fig 4 scorecard 87/66/78/24/74/77/83 | `figure_data.json:scorecard_with_med` | 87/66/78/24/74/77/83 | ✓ | Verified (values frozen; see finding `aggregate-funnel-needs-codetree`) |
| "10 of 87 high-sev methodology" | `figure_data.json:severity_breakdown:high_papers:methodology` | 10 | ✓ | Verified |
| Verifier "corrected 3 of 606" | `findings_verified.json` verdicts | 2 lowered + 1 reject = 3 | ✓ | Verified |
| Human-eval "error rate 6.2%" | `human_eval_summary.json:pooled` | 5 false / 80 = 6.25% | ✓ | Verified |
| Human-eval 74 correct / 5 false / 1 unsure | `human_eval_summary.json:pooled` | 74 / 5 / 1 | ✓ | Verified |
| Robustness detection 0.71/0.37/0.26 (Fig 5a) | `robustness_figure_data.json:by_severity_majority:merged` | 0.714/0.373/0.256, n=14/30/36 | ✓ | Verified |
| Robustness overall mean 0.38 | `robustness_figure_data.json:overall_mean_detection:merged` | 0.38 | ✓ | Verified |
| Cost 6.9M tokens/paper (Fig S2a) | `compute_cost.json` audit+verify per code paper | 6.927M | ✓ | Verified |
| 509M audit + 94M verify tokens (Repro. Stmt) | `compute_cost.json:totals` | 509.1M + 93.5M | ✓ | Verified |
| "≈92% cache reads" | per-paper `token_cost.json` cache_read share | 93.4% | ≈ | Verified (rounding) |
| 9.8 min mean, 23.4 min longest (Fig S2b) | `compute_cost.json` wall_min | 9.81 mean, 23.42 max | ✓ | Verified |
| README "$13/paper" (NOT in paper body) | `compute_cost.json` audit_cost_usd | mean $14.09 / median $12.73 / total $1,409 | ✗ (README says $13.32/$12.16/$1,332) | MISMATCH → finding `readme-cost-vs-data` |
| Committed `stats.json` / `funnel.json` | `_summary/data/stats.json`, `funnel.json` | 50 papers / 323 findings / funnel total 50 | ✗ (contradict the 100/606 paper) | STALE → finding `stale-stats-funnel-json` |

## missing

(No `missing` finding rises to a real defect. The paper's "Supplementary Information — Audit for
this contribution" is marked "TBA" in the released text — see `paper.pdf` §S1.2 — but that is an
acknowledged placeholder in a work under review, explicitly excluded by Rule "ignore minor issues
the authors have already acknowledged", and is not a result-producing artefact. Reported as an open
question below rather than a finding.)

## bug

```yaml finding
id: aggregate-funnel-needs-codetree
category: bug
topic: "result traceability / reproducibility scope"
title: "aggregate.py funnel + scorecard rows can't regenerate from the public release (need git-ignored code/ trees)"
severity: medium
confidence: high
status: finding
file: _summary/aggregate.py
line_start: 480
line_end: 484
quote: |
      has_code = len(repos) > 0 and prov_core != "no"
      cl = d / "code_links.txt"
      url_ok = cl.exists() and bool(cl.read_text().strip())
      inst_ok = any(repo_has_install(r) for r in repos)
      run_ok = any(repo_has_runnable(r) for r in repos)
claim: "aggregate.py derives has_code / inst_ok / run_ok (and thus its funnel stages 'Source code present'..'Runnable entrypoint' and the scorecard install/runnable rows) by scanning per-paper code/<owner>__<repo>/ trees, but those upstream trees are git-ignored (`.gitignore:16` `**/code/`) and absent from the released repo, so `repos` is empty for every paper."
concern: "Re-running `python _summary/aggregate.py` on the public release collapses the funnel to 100→0→0→0→0→0 and cannot reproduce the committed figure_data.json funnel [100,87,66,62,45,3] or the Fig 4 install/runnable scorecard percentages (66%/78%); those figure numbers are frozen in figure_data.json and not independently reproducible from released artefacts."
resolution: "Either commit the per-paper repo fingerprints aggregate.py needs (install-file/runnable booleans, code-file counts) as data so the funnel/scorecard regenerate offline, or document in the README that aggregate.py's environment-readiness rows require the upstream code/ trees while the coverage funnel (print_funnel.py) and finding counts are release-reproducible."
cross_refs: ["stale-stats-funnel-json", "trace-clean-9-vs-6"]
check_script: _audit_code/recompute_coverage.py
paper_ref: "Figure 1 funnel; Figure 4 scorecard rows 'Install/environment' and 'Runnable entrypoint'"
validator_pass:
  quote_match: true
  control_flow: true
  condition_satisfiable: true
```

## difference

```yaml finding
id: stale-stats-funnel-json
category: difference
topic: "reproducibility hygiene / stale artefacts"
title: "Committed stats.json / funnel.json hold stale 50-paper numbers that contradict the paper"
severity: low
confidence: high
status: finding
file: _summary/data/stats.json
line_start: 2
line_end: 3
quote: |
  "n_papers": 50,
  "n_findings": 323,
claim: "_summary/data/stats.json (n_papers=50, n_findings=323) and _summary/data/funnel.json (stage counts 50/42/24/20/4, total 50) are committed but describe an earlier 50-paper run; grep finds no .py that reads OR writes either file, so they feed no figure or headline number."
concern: "A reader inspecting _summary/data/ sees two top-level summary files asserting 50 papers / 323 findings, flatly contradicting the paper's 100 papers / 606 findings, with nothing flagging them as superseded."
resolution: "Delete the orphaned stats.json/funnel.json or regenerate them from the current 100-paper audit set (the live equivalents are figure_data.json and print_funnel.py's coverage_status.json, both of which carry the correct numbers)."
cross_refs: ["aggregate-funnel-needs-codetree"]
check_script: _audit_code/count_findings.py
paper_ref: "Abstract '605 discrepancies'; Figure 1 funnel"
validator_pass:
  quote_match: true
  control_flow: true
  condition_satisfiable: true
```

```yaml finding
id: trace-clean-9-vs-6
category: difference
topic: "result traceability / definition"
title: "Two co-existing 'all results trace cleanly' counts (9 vs 6 papers); paper uses the looser 9"
severity: low
confidence: high
status: finding
file: _summary/print_funnel.py
line_start: 28
line_end: 29
quote: |
        (sum(p["missing_frac"] < 0.5 for p in real),   "producing code found for >50% of traced artifacts"),
        (sum(p["missing_frac"] == 0.0 for p in real),  "producing code found for every traced artifact"),
claim: "print_funnel.py defines 'every result traces' as a paper whose audit.md coverage table has zero MISSING rows (missing_frac==0.0) → 9 papers (the paper's Fig 1 / abstract '9%'); aggregate.py and _summary/SUMMARY.md define it via a topic-anchored surviving-finding gate (no 'result traceability' missing finding) → 6 papers (figure_data.json funnel stage = 3 once also gated on install+runnable; SUMMARY reports 6/87)."
concern: "The same English phrase ('all published results trace cleanly') maps to two different numbers in the repo (9 by coverage table, 6 by finding topic), and the abstract/Figure 1 silently use the more favourable 9 while the README headline uses 6; a reader cannot tell which definition produced the headline without reading both scripts."
resolution: "State in the paper which operationalization '9%' uses (coverage-table missing_frac==0 over 87 source-present papers) and note the stricter topic-anchored count is 6/87, so the two are not conflated."
cross_refs: ["aggregate-funnel-needs-codetree"]
check_script: _audit_code/recompute_coverage.py
paper_ref: "Abstract 'for just 9% all analyzed published findings trace cleanly'; Figure 1 ('9')"
validator_pass:
  quote_match: true
  control_flow: true
  condition_satisfiable: true
```

```yaml finding
id: code-located-pct-84-vs-86
category: difference
topic: "evidence-trail reporting"
title: "Paper §4.1 says 84% of findings cite source code; the repo's own metric is 86% (519/606)"
severity: low
confidence: high
status: finding
file: paper.pdf
quote: |
  For 84% of the 606 discrepancies, the cited evidence is a line of the authors’ source code that a verifier confirmed is reachable rather than dead code
claim: "The aggregate.py evidence_kind=='code' share is 519/606 = 85.6% (README rounds it to 86%, README.md:12). The paper §4.1 reports 84%, evidently a stricter subset — code-located AND verifier-confirmed-reachable (code ∧ validator_pass.control_flow=true = 501/606 = 82.7%) — but the text does not state the stricter denominator, so the same quantity reads as 84% in the paper and 86% in the README."
concern: "An internal inconsistency (84% in the paper, 86% in the README) on the same evidence-trail statistic, with the paper's stricter '84%' definition unstated; minor but it is a headline evidence-quality number."
resolution: "Reconcile the paper's 84% and the README's 86%: either report the same evidence_kind=='code' figure (86%) in both, or define the 'verifier-confirmed-reachable' subset (code ∧ control_flow) and cite the script that computes it."
cross_refs: []
check_script: _audit_code/count_findings.py
paper_ref: "Section 4.1, '84% of the 606 discrepancies'"
validator_pass:
  quote_match: true
  control_flow: true
  condition_satisfiable: true
```

```yaml finding
id: readme-cost-vs-data
category: difference
topic: "cost accounting"
title: "README per-paper cost ($13.32/$12.16/$1,332) disagrees with committed compute_cost.json ($14.09/$12.73/$1,409)"
severity: low
confidence: high
status: finding
file: README.md
line_start: 256
line_end: 257
quote: |
  - ~\$13 per paper for the audit pass (median \$12.16, mean \$13.32, \$1,332 total
    over all 100 papers; the two-stage verification adds ~\$2/paper, \$214 total)
claim: "README quotes mean $13.32 / median $12.16 / $1,332 total audit cost over 100 papers, but _summary/data/compute_cost.json (the committed source) totals audit_cost_usd = $1,409.09 (mean $14.09, median $12.73 over 100 papers), and the verify total is $232.69 not $214."
concern: "The README cost figures predate or diverge from the committed compute_cost.json by ~$77 (audit) / ~$19 (verify); the paper body itself states no per-paper dollar amount (only 'reasonable cost' + token counts, which DO reconcile), so no paper claim is affected, but the repo's two cost statements disagree."
resolution: "Regenerate the README cost line from the current compute_cost.json (or note the pricing/date the README figures used); the paper's token-based cost claims (6.9M/paper, 509M+94M total) are unaffected and reconcile exactly."
cross_refs: []
check_script: _audit_code/count_findings.py
paper_ref: "Section 4.3 'reasonable cost' (paper states no $ figure); README cost profile"
validator_pass:
  quote_match: true
  control_flow: true
  condition_satisfiable: true
```

## methodology

```yaml finding
id: coverage-heuristic-text-classifier
category: methodology
topic: "result traceability / denominator construction"
title: "Headline coverage numbers (1009 artifacts, 44% missing, funnel 9) rest on a regex classifier over free-text Status cells"
severity: low
confidence: high
status: finding
file: _summary/build_coverage_figure.py
line_start: 95
line_end: 99
quote: |
  def classify(art: str, raw: str) -> str | None:
      """Map a (artefact, Status) row to one of six outcome buckets.

      The Status cells are free text written by the auditor, so this is heuristic.
      Ordering is load-bearing:
claim: "The 1,009-artifact denominator, the 44%-missing rate, and the 9-papers-clean funnel are all produced by parsing each audit.md coverage table and running classify() — a hand-tuned cascade of substring rules ('leads_missing', RUN_FAIL keywords, NA_CUES) over Status cells the LLM auditor wrote in free text; the auditor also self-selected which artefacts to trace (the denominator is explicitly auditor-selected, skewed to suspect claims, per the script docstring and Fig 3 caption)."
concern: "Two layers of subjectivity sit under the headline coverage funnel — auditor-chosen denominators and a heuristic text classifier — so the precise 44%/9 values are sensitive to wording and rule order; the paper does acknowledge the auditor-selected denominator (Fig 3 caption) but not the classifier's heuristic mapping."
resolution: "Report a robustness check on classify() (e.g. hand-label a sample of Status cells and give the classifier's agreement), or have the auditor emit a structured status enum per artefact instead of free text, so the coverage counts do not depend on regex over prose."
cross_refs: ["trace-clean-9-vs-6"]
check_script: _audit_code/recompute_coverage.py
paper_ref: "Figure 3 caption ('the denominator is the auditor-selected set'); Discussion '44%'"
validator_pass:
  quote_match: true
  control_flow: true
  condition_satisfiable: true
```

## Scoreboard

| Category    | # findings | Max severity | Note (one line)                                                        |
|-------------|------------|--------------|------------------------------------------------------------------------|
| missing     | 0          | -            | No missing result-producing artefact; S1.2 "TBA" is an acknowledged placeholder (open question). |
| bug         | 1          | medium       | aggregate.py funnel/scorecard rows can't regenerate from the public release (need git-ignored code/). |
| difference  | 4          | low          | Stale stats/funnel.json; 9-vs-6 clean-trace defs; 84%-vs-86%; README-vs-data cost. |
| methodology | 1          | low          | Coverage headline numbers rest on a heuristic text classifier over auditor-written Status cells. |

## Top take-aways (≤6)

1. **Every headline number reconciles against the released data.** [all categories] I
   re-derived, independently of the prose, 605/606 findings, the category split, the
   evidence-trail fractions, the funnel (100→87→47→9), "44% missing", 1,009 artifacts, the
   full S1 heatmap, the scorecard percentages, the 6.2% human-eval error rate, the robustness
   detection rates, and the cost/timing — all match. The seed-42 sample reproduces byte-for-byte.
2. **`aggregate.py`'s funnel + install/runnable scorecard rows are not release-reproducible.**
   [bug] They scan the git-ignored upstream `code/` trees; re-running on the public repo
   collapses the funnel to `87→0`. Those figure values are frozen in `figure_data.json`. The
   paper's load-bearing funnel ("9") comes from the data-only `print_funnel.py` and DOES
   reproduce.
3. **Two co-existing definitions of "all results trace cleanly" (9 vs 6 papers); the paper
   uses the looser 9.** [difference] The abstract/Fig 1 "9%" is the coverage-table count;
   the README/SUMMARY headline is the stricter topic-anchored 6/87. Both trace to code, but
   the paper should state which operationalization "9%" uses.
4. **Stale `stats.json` / `funnel.json` contradict the paper (50 papers / 323 findings).**
   [difference] Orphaned — read and written by nothing — but they sit in `_summary/data/`
   asserting the wrong totals.
5. **The headline coverage numbers rest on a heuristic regex classifier over free-text Status
   cells** the LLM auditor wrote, plus auditor-selected denominators. [methodology] The
   auditor-selected denominator is disclosed (Fig 3 caption); the classifier heuristic is not,
   and a robustness check on it would strengthen the coverage claims.
6. **Minor paper-internal / README-vs-data wording mismatches.** [difference] §4.1 "84%" vs
   README "86%" code-located; README "$13/paper" vs data "$14/paper" (the paper body states no
   $ figure, so its actual cost claims are unaffected).

## Items that genuinely look fine

- **Sampling is fully reproducible and honest.** Released 5,286-row frame + `seed=42`
  regenerates `list.csv` exactly; all 106 audited folders are the first 106 draws, consistent
  with the "walk the draw, screen for empirical, backfill" procedure the paper and `SAMPLING.md`
  describe (`_audit_code/out/count_findings.txt`).
- **The adversarial verifier is real and matches the paper.** `auditowl_verifier_prompt.md`
  implements the "assume-wrong-until-proven", re-open-file:line, re-run-check stance; verdicts
  (603 keep / 2 lower / 1 reject) reconcile with "corrected 3 of 606", and `findings_verified.json`
  exists for all 87 code papers.
- **`aggregate.py`'s epistemic design is sound:** figure numbers are computed from structured
  fields and filesystem checks, never from the LLM severity label; the `is_dropped()` correction
  layer (verifier reject + supplement FP + provenance FP) is applied consistently to the
  reproducibility-reality counts while the verification figures report gross verdicts — and
  re-running it reproduced `figure_data.json` exactly except for the code-tree-dependent funnel.
- **Human-eval and robustness data are complete and self-consistent**: per-paper + pooled
  human-eval JSON sum to the reported 74/5/1; the robustness severity strata (n=14/30/36) and
  the saturation curve match Figure 5.
- **Cost/timing claims reconcile to the token-level data** (6.9M/paper, 509M+94M, 9.8/23.4 min,
  ~93% cache reads).

## Open questions for the authors

- **S1.2 "Supplementary Information — Audit for this contribution" is "TBA"** in the released
  text (`paper.pdf` §S1.2). Will the camera-ready include AuditOwl's self-audit, and is it the
  one in this folder? (Not filed as a finding: acknowledged placeholder in a paper under review.)
- **Which exact denominator gives "averaging 6.1 per paper"?** 605/100 = 6.05 and 606/100 = 6.06
  both round to ~6.1 only generously; 605/87 = 6.95 ≈ the README's 7.0. Confirm the abstract's
  "6.1" is surviving-findings ÷ 100-sampled. (Low-severity; the median "7 (2–13)" reconciles
  exactly.)
- **Will `stats.json` / `funnel.json` be removed or regenerated**, given they currently assert
  50-paper totals in the published data directory?
