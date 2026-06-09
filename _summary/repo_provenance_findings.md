# Repo-provenance meta-audit: is the cloned code the paper's *core*?

For every paper marked source-present, we re-checked whether the repo the audit
cloned is actually the paper's **own core-method implementation**, or whether the
URL-driven clone step pulled a **baseline / dependency / library / different
paper / mirror / stub** and the auditor then wrote findings against the wrong
code. One agent per paper compared the cloned repo's contents (README, layout,
owner-vs-authors, advertised arXiv id/venue) against the paper's stated core
contribution, writing a verdict to `audits/<id>/repo_provenance.json`. Every
non-`correct` verdict below was then hand-verified against the current
`findings_verified.json` and `code/` snapshot before any number was patched.

## Result across the source-present papers reviewed

| Verdict | Count | Meaning |
|---|--:|---|
| `correct` | 76 | a cloned repo genuinely implements the paper's core |
| `contaminated_extra_repos` | 4 | core present, but a non-core repo was also cloned (findings correctly scoped) |
| `stale_no_code_finding` | 3 | author core present, but a finding claims none exists |
| `misclassified_missing_code` | 3* | the cloned set is all non-core → source-present unjustified |

\* one of the three (#263) was overturned on hand-review, see below, so only
**2 papers actually flip** out of source-present.

## The 10 flagged papers (verified)

### Genuine misclassification → flipped out of source-present (2)

| # | Paper | Cloned repo | What it actually is | Action |
|---|---|---|---|---|
| **543** | ProRL (NVIDIA) | `open-thought/reasoning-gym` | third-party RL **task-suite dependency** (different org, arXiv 2505.24760); ProRL released **weights only**, no training/eval code | `has_code → false` |
| **2254** | Differentiable Structure Learning (BINOTEARS) | `xunzheng/notears` | the **NOTEARS baseline library** (Zheng 2018), not BINOTEARS; `[author-cue]` tag was a false positive from shared co-author Aragam | `has_code → false` |

In both cases the *findings were already correct* ("ProRL training pipeline not
released", "No BINOTEARS code released"), only the paper-level source-present
flag was wrong, because a baseline/dependency repo sat in `code/`.

### Overturned on hand-review: stays source-present (1)

| # | Paper | Why the agent flagged it | Why it stays source-present |
|---|---|---|---|
| **263** | On the Closed-Form of Flow Matching | the two cloned repos (`annegnx/PnP-Flow` = a co-author's *different* ICLR-25 paper; `atong01/conditional-flow-matching` = the TorchCFM library) are both non-core | `audit.md` + verifier confirm the audit actually ran against the **real** repo `generativemodels/closedformfm` (verified `mean_cfm.py:136-188` faithful to Eq. 8). The core *was* released and audited, it is just **absent from the local snapshot**, while two spurious repos remain. Defect is snapshot integrity, not missing code. |

Action (DONE): re-cloned `generativemodels/closedformfm` into `code/` (11 `.py`
+ `src/`, `conf/`, `NOTES.md`, the files the findings cite) and recorded it in
`fetch_manifest.json`; corrected `263/repo_provenance.json`
(`core_present: yes`, `contaminated_extra_repos`). Existing findings retained and
now reproducible. The two non-core repos were left in place (documented in the
sidecar).

### Stale "no code" findings: author code present (3)

| # | Paper | Status | Action |
|---|---|---|---|
| **1339** | Embodied Cognition E³AD | core on the non-default **E-VAD branch**; audit cloned only the shallow `main` stub ("code coming soon") | **already corrected**, the 4 "no code" findings carry `supplement_verdict=false_positive`; specific-gap findings (EEG data, closed-loop harness, 2 frameworks) remain valid. No-op. |
| **2585** | Sample Complexity DR Avg-Reward | core recovered from the NeurIPS **supplemental zip** (only confirmed-present, never defect-audited) | **RE-AUDITED** against `code/supplement/` (standard protocol, Opus audit + Sonnet verify): 7 findings, all `keep`, the −1/2 slope reproduces, but every results-driver crashes on an uncreated save-dir (2 med bugs) + a Table-2 baseline-fairness question. Old "no code" findings replaced. |
| **828** | Steganographic CoT | the audit ran when `code/` was **empty**; both author repos (`neurips_encoded_rl` by 1st author McCarthy; `mars-steg`) were cloned **after** the audit/verifier ran → the real implementation was never examined | **RE-AUDITED** against both repos (standard protocol, Opus audit + Sonnet verify): 8 findings, all `keep` (1 high). Mechanism (penalty→encoded-CoT) verified faithful by re-implementation, but headline numbers/Fig 3 not reproducible + a headline ToM config mismatch (code splits on *objects*, paper narrates *names*). Stale "no code" findings replaced. |

### Contaminated but benign: core present, findings correctly scoped (4)

| # | Paper | Core repo | Extra non-core repo(s) |
|---|---|---|---|
| **1764** | AlphaZero Zipf | `OrenNeumann/alphazero_zipfs_law` (1st author) | `AlphaZeroZipf/...` = anonymized **mirror** |
| **2188** | Detoxifying (ARGRE) | `xiaoyisong/ARGRE` (lead author) | `unitaryai/detoxify` = eval-scorer **dependency** |
| **2371** | Forging Time Series (SDForger) | `SDForger/neurips_supplemental` | `IBM/fms-dgt` = author's **partial** public release (generator only) |
| **5208** | RF-Agent | `deng-ai-lab/RF-Agent` (NeurIPS Spotlight official) | `RishiHazra/Revolve` = **baseline**; `isaac-sim/IsaacGymEnvs` = simulator **dependency** |

No patch needed: the audit wrote all findings against the core repo in every case.

## Aggregate impact (patched + regenerated)

- **#543 and #2254 flipped out of source-present** (`aggregate.py` lowers
  `has_code` when `repo_provenance.json` says `core_present=="no"`).
- **#828 and #2585 re-audited** → findings.json/findings_verified.json replaced
  with real code-level findings (8 and 7, all `keep`); **#263 re-cloned**. #828
  added a new `headline-eval-harnesses-missing` high-severity finding.
- Track B all-results-trace fell (the real audits surfaced genuine
  traceability/packaging gaps in #828/#2585 that the empty-code audits couldn't).
- Mechanism mirrors the supplement-fetch correction: per-paper
  `repo_provenance.json` (`core_present`) gates `has_code`; the per-finding
  `provenance_verdict` field is honoured by `is_dropped()` (centralized across
  `aggregate.py` / `build_severe_findings.py`), though after the #828/#2585
  re-audits their stale findings are simply gone rather than flagged.

## Method note / limitations

- One agent per source-present paper, in two waves (Opus, then Sonnet after the
  first wave hit rate-limit starvation); recovery was idempotent via the durable
  sidecars.
- The tag-based pre-screen (`code_links.txt` `[author-cue]`/`[title-match]`)
  **misses confident mis-tags**: #2254 (`notears`) and #263 (`PnP-Flow`) were
  both tagged author-ish yet are non-core, only the content check caught them.
- Conversely the content check over-flagged #263 by judging the snapshot alone;
  hand-review against `audit.md` was required to overturn it. Treat single-pass
  agent verdicts as candidates, not ground truth.
