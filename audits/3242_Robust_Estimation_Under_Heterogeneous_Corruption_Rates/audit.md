# Audit — Robust Estimation Under Heterogeneous Corruption Rates (NeurIPS 2025, #3242)

> **RE-AUDIT (2026-06-04).** The original audit ran *before* the NeurIPS
> supplemental zip was fetched and concluded **"no resolvable code"** (three
> `missing` findings + one methodology question). That conclusion was a fetch
> artefact: the authors' **runnable code ships in the supplement** —
> `code/supplement/experiments.ipynb` (Figure 2a/2b) and
> `code/supplement/depth-map.ipynb` (Figure 1). This file re-audits the paper
> against that code. The three "no code / unlinked codebase / Fig-2 code missing"
> findings are **false** (the code is present and reproduces the figures) and have
> been **removed**; the genuine code-vs-paper discrepancy the real code *does*
> exhibit is filed below. The pre-supplement audit is preserved in
> `_superseded_audit/`.

## 1. Summary

This is a **theoretical robust-statistics paper**: minimax upper/lower bounds for
mean estimation (bounded, univariate/multivariate Gaussian) and Gaussian linear
regression under a "λ-contamination" model with heterogeneous per-sample
corruption rates. The paper states "the main contribution of this work is
theoretical" (paper_text.txt:258); the empirical content is two **illustrative /
preliminary** figures on synthetic data (no tables, no headline numbers, no
significance tests).

**The supplement code is real and faithful.** `experiments.ipynb` implements
Appendix A end to end and reproduces both panels of Figure 2; `depth-map.ipynb`
implements the weighted-Tukey-depth visualisation (three weighting schemes A/B/C)
for Figure 1. I checked every protocol detail against the code:

| Paper artefact (Appendix A) | Repo location | Status |
|---|---|---|
| n = 10⁴ samples | `experiments.ipynb` cells 3,7 (`N = 10000`) | MATCHES |
| 10⁴ dataset resamples per q | cells 3,7 (`trials = 10000`) | MATCHES |
| Bounded: point mass at 0 clean / corrupted value 1 | cell 3 (`p=0`→`P=Binomial(1,0)=0`; `Q=Binomial(1,1)=1`) | MATCHES |
| Gaussian: clean N(0,1) / outliers N(100,1) | cell 7 (`P=randn+0`, `Q=randn+100`) | MATCHES |
| Bounded statistic: mean squared-error ± SD | `opt_linear`/`thresh_linear`/`sample_mean` return (mean, std); cell 3 bands | MATCHES |
| Gaussian statistic: 4/5, 15/20, 17/20 quantiles | cell 6 (`q=0.8`, `ql=0.75`, `qh=0.85`) | MATCHES |
| Baselines: sample mean (bounded), sample median (Gaussian) | `sample_mean`, `sample_median` | MATCHES |
| Hyperparameters deferred to "the codebase" (c, q, tol, seed) | `experiments.ipynb` (`c=3`, `q=0.8`, `tol=1e-6`, `seed(1)`) | PRESENT (resolves the old "unlinked codebase" finding) |
| Corruption-rate CDF F(t)=1−(1−t)^q | cell 3,7 `lambd = 1 - exp(-Exponential(scale=q))` ⇒ F(t)=1−(1−t)^(1/q) | **MISMATCH (F1)** |

**What I did.** I read every code cell of both notebooks, mapped each against the
Appendix A protocol and the Figure 1/2 captions, and re-derived the corruption-rate
distribution the code actually samples. The exact hyperparameters the paper had
deferred to "the linked codebase" are present in `experiments.ipynb` (c=3, the 0.8
quantile, tol 1e-6, seed 1), so the figures are reproducible. The only discrepancy
is the printed CDF formula (F1); a minor illustrative-scope note is filed as F2.

## 2. Findings

**F1 `corruption-cdf-mismatch` (difference, medium).** Appendix A
(paper_text.txt:1327-1328) states the corruption rates are drawn with cdf
**F(t)=1−(1−t)^q** and that "as q increases we can expect a higher corruption
rate." The code draws `lambd = 1 - np.exp(-np.random.exponential(x, N))` with
`x = q` (cell 3 bounded, cell 7 Gaussian; `depth-map.ipynb` uses `Exponential(2)`).
Because numpy's `exponential(scale=q)` has mean q, `lambd = 1−e^{−E}` has cdf
**F(t)=1−(1−t)^(1/q)** (Beta(1, 1/q), mean q/(q+1)) — *not* 1−(1−t)^q. The two
agree only at q=1. The paper's printed formula is moreover **internally
inconsistent**: 1−(1−t)^q is Beta(1,q) with mean 1/(1+q), which *decreases* as q
grows — the opposite of the paper's own monotonicity sentence. The code's 1/q
exponent is the one consistent with the text and the plotted x-axis. Low stakes
(the experiment is illustrative, the contribution theoretical), but a concrete,
verifiable code↔paper mismatch in the released artefact.

**F2 `fig2-illustrative-single-baseline` (methodology, low).** Each Figure-2 panel
compares the proposed estimators to a single homogeneous baseline (sample mean /
sample median) on an extreme construction (point-mass-at-0 vs constant-1; N(0,1) vs
N(100,1)), reporting the 80th-percentile squared error for the Gaussian panel. No
heterogeneity-aware robust baseline is included, so the figure is illustrative (as
the paper labels it) rather than a stress test. Does not affect the theoretical
contribution.

## 3. Removed — original "no code" findings were false (code ships in the supplement)

`no-public-code-repository`, `linked-codebase-not-resolvable`, and
`fig2-experiment-code-missing` each asserted the code/hyperparameters were absent.
The supplement ships `experiments.ipynb` (computes Figure 2, holds c=3 / q=0.8 /
tol=1e-6 / seed=1) and `depth-map.ipynb` (computes Figure 1), so all three are
false and have been removed from the findings set. (The paper still gives no public
repository URL/DOI in the PDF — the code is supplement-only — but the artefacts are
present and reproduce the figures, so this is no longer a missing-code defect.) The
original pre-supplement audit is kept verbatim in `_superseded_audit/`.

## 4. Items that genuinely look fine

- The code faithfully implements the Appendix A protocol on every checked axis
  (sample sizes, trial count, clean/outlier distributions, plotted quantiles,
  baselines) — see the table in §1.
- The paper is honest about scope: it states the contribution is theoretical and
  labels the experiments "preliminary" / "illustrative."
- The hyperparameters the text deferred to "the codebase" are in fact in
  `experiments.ipynb`, so Figures 1–2 are reproducible from the supplement.

See `findings.json` / `findings_verified.json` for the structured findings and
`_build_reaudit.py` for the script that emits them.
