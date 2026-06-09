# Robustness experiment: auditor test-retest reliability

**Question.** Re-running the full `audit → adversarial-verify` pipeline on the same
paper and the same frozen codebase, model, prompt, and temperature fixed, how
stably does it re-surface the same findings? This is a **reliability
characterisation** (detection rates, agreement, reliability coefficients with CIs),
not a hypothesis test. Everything needed to reproduce it lives in this folder.

## 1. Design

| Decision | Choice |
|---|---|
| Target | reliability of *our* findings, re-run the pipeline, measure output stability |
| Frame | 78 papers with a retrieved codebase (≥5 source files + a reference `findings.json`) |
| Sample | **5** papers, uniform random, **seed = 42** (`select_papers.py` → `selection.json`) |
| Runs / paper | **10** |
| Variation | **repeat-only** (model + prompt + temperature fixed), isolates intrinsic stochasticity |
| Pipeline / run | **audit + adversarial verify** (Opus audit → Sonnet verify → Opus escalation) |
| Alignment | objective anchors (category + file + line overlap) + semantic cross-check; never the severity label |
| Execution | batched + resumable, 10 runs at a time |

### The sample (seed = 42, draw order: from `selection.json`)

| # | paper | domain | src files | code size | ref. findings (high) |
|---|---|---|---:|---:|---|
| 1 | `1829_OLinear` | time-series forecasting | 169 | 30 MB | 5 (0) |
| 2 | `1333_Latent_Harmony` | UHD image restoration | 49 | 0.5 MB | 9 (4) |
| 3 | `2657_Scalable_Explainable_Anomaly_Detection` | anomaly detection | 28 | 172 MB | 5 (1) |
| 4 | `2578_DOVE` | one-step diffusion video | 56 | 189 MB | 5 (0) |
| 5 | `2371_Forging_Time_Series_with_Language` | LLM time-series | 303 | 70 MB | 7 (3) |

To re-draw or swap a paper, change the seed in `select_papers.py` and re-run;
`--list` prints the full eligible frame. 10 runs give 45 run-pairs per paper for
Jaccard and 10 "coders" for Krippendorff's α, SE(p̂) ≈ 0.16 at p = 0.5, enough to
separate a stable core (p̂ ≥ 0.8) from a flaky tail (p̂ ≤ 0.3).

## 2. Leak prevention (`build_sandboxes.py`)

Independence is enforced structurally:

1. **No answer-key in the sandbox.** Each `run_NN/` gets only auditor-visible
   inputs, `paper_text.txt`, `metadata.txt`, `code_links.txt`, `code/`, prompt,
   schema, extractor. Prior `audit.md` / `findings.json` / `findings_verified.json`
   / `_audit_code/` / `_verifier_code/` are never copied in.
2. **Frozen, identical inputs.** `code/` is snapshotted once per paper into a
   read-only `code_frozen/` and symlinked into all 10 runs, byte-identical, immutable.
3. **Fresh context per run.** Every run is a new subagent sharing no conversation;
   prompt caching reuses an identical prefix only, never another run's output.
4. **Sealed boundary.** `AGENT_INSTRUCTIONS.md` / `VERIFIER_INSTRUCTIONS.md` forbid
   reading anything outside the run dir, no `../`, no sibling runs, no `audits/` /
   `_summary/`, no network / `git` / web tools.
5. **No oracle leakage.** No OpenReview reviews, GitHub issues, tier labels, or our
   own summary are ever in scope.

## 3. Metrics (`analyze.py`)

Findings are aligned on **objective anchors**, `category` + `file` + overlapping
`line_start..line_end` (±10-line window), never on the severity label. A parallel
**semantic** alignment (TF-IDF cosine over title+claim+concern) is computed too;
every metric is reported under both matchers.

- **Primary (objective):** count stability (mean / SD / CV / range of findings- and
  high-severity-per-run); per-issue detection rate `p̂` → stable core (p̂ ≥ 0.8) vs
  flaky tail (p̂ ≤ 0.3) + stable-core fraction; mean pairwise Jaccard over the 45
  run-pairs + bootstrap 95% CI; Krippendorff's α (nominal) on the run × issue matrix
  (validated against the textbook α = 0.743 example, `analyze.py --selftest`);
  headline reproduction (does "any high-severity finding?" agree across runs).
- **Secondary (label-based):** severity agreement on co-detected issues (within-issue
  SD on {low, med, high}, majority-match rate).
- **Verifier stage (post-verification = what ships):** per-run survival rate;
  detection-rate / stable-core / Jaccard / α recomputed on **kept** findings.

## 4. Running it (batched + resumable)

```bash
# 1. draw the sample (deterministic; already done)
python _robustness/select_papers.py            # -> selection.json (frame=78, k=5)
python _robustness/select_papers.py --list     # inspect the eligible frame

# 2. validate the metrics engine: free, no LLM calls
python _robustness/analyze.py --selftest

# 3. materialise the 50 sealed sandboxes (~0.5 GB; shared read-only code_frozen)
python _robustness/build_sandboxes.py --runs 10   # -> run_01..10/, sandboxes.json

# 4. run one batch (~10 runs) at a time
#    needs: pip install claude-agent-sdk  and  export ANTHROPIC_API_KEY=...
python _robustness/status.py               # progress table
python _robustness/run_batch.py --next 10  # audit -> verify -> escalate the next 10 pending runs
#   resumable: re-run until status.py shows 0 pending (finished runs self-skip)

# 5. analyse
python _robustness/analyze.py                   # -> data/metrics_*.json
```

Batches run in paper-major order (batch 1 = paper 1's 10 replicates, … ; 5 batches
total). State lives in the on-disk artefacts, so it resumes cleanly after interruption.

## 5. Cost (from each paper's committed `token_cost.json`)

| batch | paper | committed audit \$ | ≈ batch (×10 audit + verify) |
|---|---|---:|---:|
| 1 | `1829_OLinear` | \$35 / run | **\$380–430** (cache-heavy outlier) |
| 2 | `1333_Latent_Harmony` | \$14 | \$160–200 |
| 3 | `2657_Anomaly_Detection` | \$13 | \$150–190 |
| 4 | `2578_DOVE` | \$15 | \$170–210 |
| 5 | `2371_Forging_Time_Series` | \$7 | \$90–130 |

**Full 5 batches ≈ \$950–1,200.** Each run writes its own `token_cost.json`;
metering is per batch, so you can stop after any batch.

## 6. Folder layout

```
_robustness/
  README.md             this document
  selection.json        the seed=42 draw (source of truth for the sample)
  select_papers.py      draw the sample from the eligible frame
  build_sandboxes.py    materialise sealed, leak-proof run sandboxes
  status.py             FS-derived progress + next-batch emitter
  run_batch.py          portable batch runner (Claude Agent SDK): audit -> verify -> escalate
  analyze.py            alignment + reliability metrics (+ --selftest)
  sandboxes.json        run manifest (written by build_sandboxes.py)
  data/                 metrics_<paper>.json, metrics_all.json (written by analyze.py)
  <paper>/
    code_frozen/        read-only code snapshot, shared by the 10 runs
    run_01/ .. run_10/  sealed sandboxes (inputs only; outputs written here)
```

## 7. Caveats
- 5 papers is a deliberate reliability *characterisation*, not a population estimate;
  results are per-paper, pooled only descriptively.
- "Repeat-only" measures intrinsic stochasticity; it says nothing about robustness to
  nuisance perturbations (temperature, model, input order); that is a separate study.
- Stochasticity also enters through non-deterministic check scripts the auditor
  writes and runs; that variance is part of the pipeline and is counted.
- `code_frozen/` reflects the codebase as cloned for the original audit; upstream repo
  changes since then are deliberately excluded.
