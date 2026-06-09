# Sampling methodology

The study audits **100 empirical NeurIPS 2025 main-track papers** drawn as a
**uniform random sample** from the full accepted-paper population, with theory
papers excluded. The draw is reproducible (`seed=42`) end to end.

## Population frame

- **Source:** the official NeurIPS 2025 proceedings index,
  <https://papers.nips.cc/paper_files/paper/2025>.
- **Built by:** `scrape_neurips_2025.py`, which keeps only abstract pages tagged
  `-Abstract-Conference.html` (the **Main Conference Track**) and drops the
  Datasets & Benchmarks and Position tracks.
- **Frame size:** `N = 5,286` papers, written to `neurips_2025_main_track.csv`
  (columns `title, authors, track, url`), one row per paper in index order.

## Random draw

- `random_list.py` draws **500 distinct row numbers** from `1..N` using Python's
  standard library, `random.Random(42).sample(range(1, N+1), 500)`, uniform,
  without replacement, recorded **in draw order** to `list.csv`.
- The fixed seed makes the draw fully reproducible: re-running against the same
  `neurips_2025_main_track.csv` yields the same `list.csv`.
- No stratification by topic, oral/poster, or popularity.

## Walk-and-collect (with theory exclusion)

`prepare_audit_inputs.py` walks `list.csv` **in draw order** and, for each paper:

1. downloads the paper PDF (via the abstract page's `citation_pdf_url`, cached
   by paper number under `.pdf_cache/`);
2. classifies it as **theory** or **empirical**. A paper is flagged theory only
   when its NeurIPS reproducibility-checklist entry for *open access to data and
   code* (or *experimental result reproducibility*) is answered `NA` **and** the
   author's own justification states the work has no experiments, boilerplate
   guideline text is deliberately not read, so empirical papers that merely
   deferred a code release are not mis-flagged;
3. mines author/primary code repositories and clones them (see below).

It keeps going until **100 empirical papers** have been collected; theory papers
are set aside (written under `audits/theory/`), not counted toward the target.
Because the 100 are the leading empirical entries of a uniform random
permutation, they are a uniform random sample of empirical main-track papers.

- **Rows consumed:** the first **103** rows of the draw yielded the initial
  target, **100 empirical** papers plus **3 theory** papers set aside (`218`,
  `1906`, `2788`). A later reclassification (see *Post-audit reclassification*
  below) set **3 more** papers aside and walked the draw to row **106**, so the
  final sample is the leading **100 empirical** papers of the draw after **6**
  set-aside papers (4 theory + 2 justified-no-code).
- Empirical papers land in `audits/<num>_<slug>/`; theory papers in
  `audits/theory/<num>_<slug>/`; justified-no-code exclusions in
  `audits/excluded_justified_no_code/<num>_<slug>/`.

## Post-audit reclassification (theory + justified no-code)

After the initial audit, three papers were reclassified out of the empirical
sample and the draw was walked three rows further to backfill 100 empirical
papers. This is a deliberate scope decision layered on top of the seed-42 draw,
recorded here in full so the headline denominator is honest:

- **#459** (*Sampling from multi-modal distributions … via reverse diffusion*) -
  pure sampling-complexity theory (only a numerical illustration) that escaped the
  automatic theory filter. Moved to `audits/theory/`.
- **#1308** (*Neural Collapse is Globally Optimal …*) and **#4393**
  (*Self-Supervised Discovery of Neural Circuits …*), **empirical**, but the
  authors answered the NeurIPS code-release checklist **No** with an accepted
  justification (#1308: *"standard architectures … readily reproduced without …
  the code"*; #4393: *"experiments … simple enough to reproduce without … code …
  available upon request"*). These are excluded under a **new criterion, an
  accepted no-code justification, kept distinct from theory** in
  `audits/excluded_justified_no_code/`. This criterion is *not* part of the
  original uniform draw; treat it as a scope choice, not a property of the seed-42
  sample.
- **Backfill:** the next three empirical papers in draw order, **#1171** (row
  104), **#2170** (row 105), **#2021** (row 106), were fetched and audited. All
  three in fact release the authors' own code, which the URL-mining pass had
  missed (project page / `github.io` / repo name not overlapping the title); the
  repos were recovered by hand and cloned. **#2021**'s repo carries a disclaimer
  that it is a *re-implementation* with the original withheld under a protected
  license and prompts that "may not be the original", source-present but
  bottom-tier on result-traceability.

Set-aside papers carry **no findings** and are excluded from every figure and
aggregate (`aggregate.py` skips both `audits/theory/` and
`audits/excluded_justified_no_code/`). The empirical sample remains **100**;
source-present is **87 / 100**.

## Code retrieval

For each empirical paper, `prepare_audit_inputs.py` identifies the **authors' own**
repository, not baselines, dependencies, or frameworks:

- candidate `github.com` / `gitlab.com` / `bitbucket.org` repo URLs are mined
  from both the PDF text and its embedded hyperlink annotations (tolerant of
  line-wrapped/space-broken URLs);
- a candidate is kept as author code when it has an author-code cue phrase
  nearby ("our code is available at", "we open-source", …), its repo name
  overlaps the paper title / method name / acronym, or it sits next to a
  DOI/Zenodo archive;
- links under known library orgs (`huggingface`, `facebookresearch`, `pytorch`,
  …) and links introduced as baselines/backbones ("based on", "we build upon",
  "pre-trained", …) are rejected unless a strong author signal overrides.

Each retained repository is shallow-cloned at the URL printed in the PDF
(`git clone --depth 1 --recurse-submodules --shallow-submodules`), followed by a
best-effort `git lfs pull`, so the clone reflects what the authors actually
shipped. Per-paper fetch health (clone timeouts, git-LFS pointer stubs, empty
submodules) is recorded in `fetch_manifest.json`; the cloned `code/` trees are
git-ignored, and `code_links.txt` preserves the URLs so any reader can re-clone.

In addition to git hosts, `prepare_audit_inputs.py` now fetches the paper's
**NeurIPS supplemental zip** (`…/file/<hash>-Supplemental-Conference.zip`, same
hash as the abstract page) and, **when it carries source code**, unpacks that
code, minus bundled virtualenvs / caches, into `code/supplement/`. Many papers
ship their only runnable code in the supplement rather than on a git host, so the
URL-mining pass never sees it. A supplement that is only a PDF appendix or a
dataset (no source files) is deliberately *not* unpacked into `code/`: that would
fake "source present" for a paper that released no code. The supplement URL is
recorded in `code_links.txt` and `fetch_manifest.json` (`__supplement__`).

## Known limitations of the frame

- The frame is the **Main Conference Track only**, Datasets & Benchmarks and
  Position papers are out of scope by construction.
- Repo identification is heuristic: a paper that links its code in an unusual
  way, or whose repo was not yet public at fetch time, can be recorded as
  "no author code" even though code exists; final source-present is
  **87 / 100** (several repos were recovered by hand after the automated pass -
  including all three backfill papers #1171/#2170/#2021, whose code the URL miner
  missed, see `_summary/SUMMARY.md`).
- When a paper ships multiple author repos, all matched ones are cloned, but a
  repo missed by the cues above is not.
- **Supplement-only code.** Some papers release their code *only* inside the
  NeurIPS supplemental zip, never on a git host. The original clone-only fetch
  step skipped these, so the auditor saw an empty `code/` tree and wrongly
  flagged "no code"; the adversarial verifier, re-checking the same on-disk
  artefacts, shared the blind spot and confirmed the absence. A later
  supplement-fetch pass (now built into `prepare_audit_inputs.py`) downloaded every
  in-scope supplement and reclassified missing-code findings on **2371, 2585, and
  3242** as false positives, and moved **2585** and **3242**
  from "no source" to "source present". Two residual caveats remain: (a) a few
  papers' supplements 404 on the proceedings site (their code, if any, may live
  on OpenReview, which this pipeline does not crawl); and (b) supplement-only code
  is camera-ready-frozen and not independently hosted, a durability/traceability
  caveat distinct from "code present", which is why e.g. 3242's *no-public-repo*
  finding still stands even though its figure code was located and run.

## Reproducing

```bash
# 1. build the population frame (→ neurips_2025_main_track.csv, N = 5,286)
python scrape_neurips_2025.py

# 2. draw the random sample (deterministic, seed = 42 → list.csv, 500 rows)
python random_list.py

# 3. walk the draw, set theory aside, fetch + clone until 100 empirical papers
python prepare_audit_inputs.py --nontheory 100 --outdir audits
```

Changing the seed, or re-scraping `papers.nips.cc` after the index changes, will
change which papers are drawn.

## Superseded approaches (historical)

Two earlier framings were discarded before this run:

- An initial frame built from **Paper Digest's** "NeurIPS 2025 Papers with Code
  & Data" page, a *papers-with-code* index that is automated and incomplete,
  and is **not** the full accepted-paper population. Replaced by the official
  `papers.nips.cc` frame above.
- Within that earlier frame, a first pass took the **first 20** entries rather
  than a random draw; Paper Digest's default ordering is by popularity, so the
  sample was heavily enriched for high-profile LLM/attention papers. Replaced by
  the uniform random draw above.
