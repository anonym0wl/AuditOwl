# Reproducibility Audit of NeurIPS 2025 with AuditOwl

LLM-agent reproducibility audits of 100 randomly sampled NeurIPS 2025 main-track
papers, each followed by an independent adversarial verification pass and rolled
up into a cross-paper summary. Both passes run on Claude Opus 4.8.

**Headline finding.** **87 of 100** sampled papers release the authors' own code;
the other 13 release none. Of the 87 that do, only **6** have every reported
result trace cleanly to committed code. The agents surface **606 findings** (7.0
per code-releasing paper) forming a graded evidence trail: 99.8% are quote
anchored, 86% cite an executable code location, 52% are backed by a re-runnable
check, and 99.8% survive independent adversarial re-verification. Defects are
dominated by **missing code or data (51%)** and **paper/code mismatches (25%)**.

**Scope.** Findings are computed over the 87 papers that release author code.
Pinning down that set required correcting the naive URL-driven clone: fetching the
NeurIPS supplemental `.zip`, following non-default git branches, locating repos
published after the audit ran, and a repository-provenance pass that separates a
paper's own core code from a baseline or dependency cloned by mistake (verdicts in
`audits/<id>/repo_provenance.json`). The 13 no-code papers stay in the sample, so
the denominator is 100 and "87/100 release code" is itself a result, but they
carry no findings. The theory and justified-no-code reclassifications, and the two
papers re-audited after their code was found late, are documented in
[`SAMPLING.md`](SAMPLING.md) and
[`_summary/repo_provenance_findings.md`](_summary/repo_provenance_findings.md).

## Repository layout

```
auditowl_prompt_neurips.md      ← the audit protocol each auditor agent follows
auditowl_verifier_prompt.md     ← the adversarial second-pass verifier protocol
start_audit_prompt.md           ← runner: spawns one audit subagent per paper
start_verify_prompt.md          ← runner: spawns one verifier subagent per paper
references/findings-schema.md   ← the schema every finding YAML must satisfy
scripts/extract_findings.py     ← extracts + schema-validates YAML → JSON sidecar
SAMPLING.md                     ← how the population frame was sampled
scrape_neurips_2025.py          ← scrape the NeurIPS 2025 main-track paper list
random_list.py                  ← draw the random paper sample (seed=42)
prepare_audit_inputs.py         ← download PDFs + clone repos into audit folders
audit_done.txt / verify_done.txt ← phase trackers (one folder per line)

audits/                         ← per-paper folders (one per sampled paper)
    <id>_<short-title>/
        audit.md                ← LLM auditor's narrative + YAML findings
        findings.json           ← machine-readable sidecar (schema-validated)
        findings_verified.json  ← per-finding verdict (keep/lower/reject)
        _audit_code/            ← deterministic checks the auditor wrote
        _verifier_code/         ← scripts the verifier wrote
        code_links.txt          ← upstream repo URL(s) so a reader can re-clone
        metadata.txt            ← paper metadata (title, OpenReview, etc.)
        fetch_manifest.json     ← per-paper fetch health (LFS / submodule / timeout)
        token_cost.json         ← per-paper token + cost accounting

_summary/
    aggregate.py             ← objective data layer: findings.json + repo trees → data/*.json
    build_*_figure.py        ← one script per paper figure (see figure map below)
    SUMMARY.md               ← cross-paper writeup
    data/                    ← machine-readable aggregates (figure_data.json, …)
    figures/                 ← fig_receipts, fig_coverage, fig_scorecard, … (PNG + PDF + SVG)
```

`findings_verified.json` and `_verifier_code/` exist once the verify pass has run.

## How to read the work

1. Start at [`_summary/SUMMARY.md`](_summary/SUMMARY.md): the headline numbers, the
   reproduction-gate definitions, and the figure-by-figure map.
2. For per-paper detail, open any `audits/<id>_<slug>/audit.md` and its
   `findings.json`. If `findings_verified.json` exists, that is the adversarially
   re-checked set, each finding annotated with a verdict (keep/lower/reject), a
   one-line reason, and what changed.
3. The per-paper coverage tables in each `audit.md` are the most load-bearing
   artefact for downstream analysis.

## Paper figures (figure ↔ code map)

LaTeX assigns figure **numbers** in source order; the figure **filenames** are
numberless (e.g. `fig_coverage`). Every figure is written as PNG + PDF + SVG.

| Paper | Figure file | Built by |
|---|---|---|
| Fig 1 | pipeline schematic (hand-drawn) | paper asset, not built from this repo |
| Fig 2 | `_summary/figures/fig_receipts` | `_summary/build_fig2_receipts.py` |
| Fig 3 | `_summary/figures/fig_coverage` | `_summary/build_coverage_figure.py` |
| Fig 4 | `_summary/figures/fig_scorecard` | `_summary/build_scorecard_figure.py` |
| Fig 5 | `_robustness/figures/fig_robustness` | `_robustness/build_panels_ab.py` |
| Fig 6 | `_robustness/figures/fig_human_eval_overall_calibration` | `_robustness/build_human_eval_overall_calibration.py` |
| Fig 7 | `_summary/figures/fig_severity_confidence` | `_summary/build_severity_confidence_heatmap.py` |
| Fig 8 | `_summary/figures/fig_compute_cost` | `_summary/build_cost_figure.py` |

## Prerequisites

| Dependency | Purpose |
|---|---|
| Python 3.9+ (study run on 3.10) | Sampling, extraction, aggregation, figures |
| `requests` + `beautifulsoup4` | Scraping the paper list and fetching inputs |
| `PyMuPDF` (imported as `fitz`) | Extracting the `paper_text.txt` sidecar from `paper.pdf` |
| `PyYAML` | Parsing YAML finding blocks from `audit.md` |
| `matplotlib` + `numpy` | Summary + robustness figures |
| `git` (+ `git-lfs`) | Cloning paper repositories |
| Claude Opus 4.8 | Audit and verification passes |

```bash
pip install -r requirements.txt   # versions pinned to the set this study used
```

The per-paper checks under `audits/*/_audit_code/` and `_verifier_code/` import
each audited repo's own stack (`torch`, `scipy`, `sklearn`, …); install those ad
hoc when re-running a specific paper's check.

## Reproducing the audit

The repository tracks the audit **outputs** (`audit.md`, `findings.json`,
`findings_verified.json`, summary data + figures), not the **inputs**: the cloned
repos (`code/`), paper PDFs (`paper.pdf`), and text sidecars (`paper_text.txt`)
are git-ignored. To rebuild the inputs for the existing audit set, run
`python scripts/reclone_missing.py` (re-clones each author repo from the committed
`code_links.txt`); to re-derive everything from scratch, use the phases below.

> **Determinism.** Sampling is seeded (`seed=42`) and the aggregation + figure
> layer is fully deterministic, but the two LLM passes are not: a re-run yields a
> similar finding distribution, not a byte-identical one (the `_robustness/`
> test-retest study quantifies this). Source-present counts in `aggregate.py` walk
> the git-ignored `code/` trees, so they only reproduce once the inputs are rebuilt.

### Phase 1: Build the population frame

```bash
python scrape_neurips_2025.py   # → the NeurIPS 2025 main-track paper list
python random_list.py           # → random sample (seed=42)
```

See [`SAMPLING.md`](SAMPLING.md) for the exact procedure.

### Phase 2: Fetch papers and clone repos

```bash
python prepare_audit_inputs.py
```

Creates `audits/<id>_<slug>/` folders, downloads each `paper.pdf` (+ a
`paper_text.txt` sidecar), recurses submodules and pulls git-LFS content, and
records per-paper fetch health in `fetch_manifest.json` (clone timeouts, LFS
pointer stubs, and missing submodules are flagged there; treat "missing artefact"
findings on LFS/submodule-heavy repos with that caveat).

### Phase 3: Run the audit (per paper)

[`start_audit_prompt.md`](start_audit_prompt.md) spawns one isolated subagent per
paper. Each reads [`auditowl_prompt_neurips.md`](auditowl_prompt_neurips.md) and
works inside its `audits/<id>_<slug>/` folder against the paper and the cloned
`code/` tree, writing `audit.md` (narrative + YAML findings) and `_audit_code/`
(deterministic checks). Append each finished folder to `audit_done.txt`.

### Phase 4: Extract findings

```bash
# Single paper:
python scripts/extract_findings.py audits/<id>_<slug>/audit.md \
  --out audits/<id>_<slug>/findings.json

# All papers:
for d in audits/*/; do
  python scripts/extract_findings.py "$d/audit.md" --out "$d/findings.json"
done
```

This validates each finding against
[`references/findings-schema.md`](references/findings-schema.md) and refuses to
emit JSON if any finding fails.

### Phase 5: Adversarial verification (per paper)

[`start_verify_prompt.md`](start_verify_prompt.md) spawns one isolated verifier
subagent per paper, each reading
[`auditowl_verifier_prompt.md`](auditowl_verifier_prompt.md). The verifier
re-opens every cited `file:line`, compares the quote against the source assuming
each finding is wrong until proven right, and writes `findings_verified.json` (each
finding annotated with a verdict, a one-line reason, and what changed) plus any
helper scripts under `_verifier_code/`. Append each finished folder to
`verify_done.txt`.

### Phase 6: Generate the aggregate summary

```bash
python _summary/aggregate.py                          # → _summary/data/*.json
python _summary/build_fig2_receipts.py                # → fig_receipts
python _summary/build_coverage_figure.py              # → fig_coverage
python _summary/build_scorecard_figure.py             # → fig_scorecard
python _summary/build_severity_confidence_heatmap.py  # → fig_severity_confidence
python _summary/build_cost_figure.py                  # → fig_compute_cost
```

`aggregate.py` passes over every `audits/*/findings.json` plus the cloned repo
trees and writes the numbers most figures rest on to
`_summary/data/figure_data.json`; the `build_*_figure.py` scripts render each
figure from that. Every number a figure shows is computed from structured fields
and deterministic filesystem checks, never from the auditor's severity label.

## Reproducing on a different conference

1. Drop the conference's accepted papers into `audits/<id>_<slug>/` folders; each
   needs the paper, a cloned `code/<owner>__<repo>/` tree, and a `code_links.txt`.
2. Run the audit pass (Phase 3) and extract findings (Phase 4).
3. Optionally run the adversarial verify pass (Phase 5).
4. Run `_summary/aggregate.py` then the `build_*_figure.py` scripts.

## License

This repository's original contents (source code, audit outputs, findings data,
figures, and docs) are released under **CC BY-NC 4.0** (Creative Commons
Attribution-NonCommercial 4.0); see [`LICENSE`](LICENSE). The audited papers and
their authors' code and data are not relicensed here.
