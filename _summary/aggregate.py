#!/usr/bin/env python3
"""Objective data layer for the NeurIPS-2025 reproducibility-audit figures.

Single pass over every `audits/<paper>/findings.json` (excluding `audits/theory/`)
plus the cloned `code/<owner>__<repo>/` trees, emitting ONE inspectable artifact,
`_summary/data/figure_data.json`, that the figure script consumes verbatim.

The point of the split is epistemic: every number a figure shows is computed here,
from structured fields and deterministic filesystem checks — never from the auditor's
subjective `severity` label, and never re-derived from prose. Open `figure_data.json`
to audit exactly what each figure rests on.

Run:  python _summary/aggregate.py
"""
from __future__ import annotations
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "_summary" / "data"
DATA.mkdir(parents=True, exist_ok=True)

# ---- deterministic repo detectors (shared with the build_*_figure.py scripts) ----
INSTALL_FILES = {
    "requirements.txt", "environment.yml", "environment.yaml", "setup.py",
    "pyproject.toml", "Pipfile", "poetry.lock", "Dockerfile", "conda.yaml",
    "setup.cfg",
}
RUN_RE = re.compile(r"(train|main|run|eval|test|demo|experiment)", re.I)

# ---- code-coverage gates (topic-anchored, not regex-over-paper_ref) --------
# A finding's `topic` is the auditor's structured label. Two families of
# *missing*-category findings tell us about code coverage:
#   • result-traceability gap — a specific reported result (a Table/Figure/
#     number) has no committed code that produces it.
#   • wholesale-missing code  — the repo is a stub / the contribution's code is
#     largely absent (no code released, repo provenance, code-completeness).
# Neither executes code; both are read straight from the structured `topic`.
WHOLESALE_TOPICS = (
    "code availability", "expected code completeness", "code completeness",
    "repository provenance", "repository completeness",
)


def is_dropped(f: dict) -> bool:
    """A finding excluded from the *reproducibility-reality* counts (availability,
    code-coverage, severity, scorecard): either refuted by the two-stage verifier
    (`verdict == "reject"`) OR shown to be a false positive once the NeurIPS
    supplemental zip was fetched (`supplement_verdict == "false_positive"`).

    The verification figures (fig7–9) still report the verifier's own verdicts
    verbatim — this predicate only governs what counts as a real defect, so a
    finding the auditor raised against absent code is not held against a paper
    whose code in fact shipped in the supplement.

    A third correction (`provenance_verdict == "false_positive"`) comes from the
    repo-provenance pass: a "no code in workspace" finding raised against a paper
    whose author code was in fact cloned (just after the audit ran, or on a
    non-default branch) is likewise not a real defect. See repo_provenance.json.
    """
    return (f.get("verdict") == "reject"
            or f.get("supplement_verdict") == "false_positive"
            or f.get("provenance_verdict") == "false_positive")


def is_traceability_gap(f: dict) -> bool:
    return (f.get("category") == "missing"
            and "traceab" in (f.get("topic", "") or "").lower()
            and not is_dropped(f))


def is_wholesale_missing(f: dict) -> bool:
    if f.get("category") != "missing" or is_dropped(f):
        return False
    t = (f.get("topic", "") or "").lower()
    return any(w in t for w in WHOLESALE_TOPICS)


# README-documented install instructions (when no dependency FILE is shipped):
# pip / conda / mamba / poetry / uv / pipenv / setup.py / make / install.sh …
INSTALL_README_RE = re.compile(
    r"(pip3?\s+install|python\s+-m\s+pip\s+install|"
    r"uv\s+(pip\s+install|sync|add)|"
    r"conda\s+(create|install|env)|mamba\s+(create|install)|"
    r"poetry\s+(install|add)|pipenv\s+install|"
    r"setup\.py\s+install|make\s+install|"
    r"(bash|sh)\s+\S*(install|setup)\S*\.sh)", re.I)


def repo_has_install(repo: Path) -> bool:
    # 1) a dependency / environment FILE anywhere in the tree
    if any(p.name in INSTALL_FILES for p in repo.rglob("*")):
        return True
    # 2) otherwise, install instructions documented in a README (root or one level
    #    down — bounded so we don't scan vendored node_modules etc.)
    readmes = list(repo.glob("README*")) + list(repo.glob("*/README*"))
    for rm in readmes[:10]:
        try:
            if INSTALL_README_RE.search(rm.read_text(errors="replace")[:20000]):
                return True
        except OSError:
            continue
    return False


def repo_has_runnable(repo: Path) -> bool:
    return (any(RUN_RE.search(p.stem) for p in repo.rglob("*.py"))
            or any(repo.rglob("*.sh")))


# ---- stub detector (deterministic, filesystem) ----------------------------
# A repo is a STUB only in the narrow sense the term should carry: it contains no
# real source code at all — a "code coming soon" placeholder, or just a
# README/LICENSE. This is NOT the old topic-based "the auditor flagged some
# missing piece" signal (which fired on 33/82 repos that ship real code). The
# only thing that makes a source-having paper a stub is: zero real code files.
# Verified against all on-disk repos (adversarial classification workflow):
# count==0 ⇒ stub is sound — exactly one repo (a "code coming soon" README) hits it.
CODE_EXT = {
    ".py", ".ipynb", ".m", ".cpp", ".cc", ".cxx", ".c", ".h", ".hpp", ".cu",
    ".cuh", ".java", ".js", ".ts", ".jsx", ".tsx", ".go", ".rs", ".sh", ".bash",
    ".r", ".jl", ".scala", ".lua", ".f90", ".f", ".mlx", ".pyx",
}
_SKIP_DIRS = {".git", "__pycache__", "node_modules", ".ipynb_checkpoints", ".github"}


def repo_code_file_count(repo: Path) -> int:
    n = 0
    for p in repo.rglob("*"):
        if any(s in p.parts for s in _SKIP_DIRS):
            continue
        if p.is_file() and p.suffix.lower() in CODE_EXT:
            n += 1
    return n


def evidence_kind(file_field: str) -> str:
    """Objective classification of where a finding's evidence lives."""
    ff = file_field or ""
    if ff.endswith((".pdf",)):
        return "paper"
    if ff.startswith("http"):
        return "url"
    if "out/" in ff or (ff.endswith((".csv", ".txt")) and "check" in ff):
        return "script_output"
    if ff:
        return "code"
    return "none"


# ---- finding-level taxonomy axes (all objective / structured) -------------
CATEGORIES = ["missing", "difference", "bug", "methodology"]

# ---- forensic receipts: verbatim, quote-anchored, de-identified ------------
# Each spec points at a real artifact under audits/<audit>/. aggregate.py reads
# the file, slices the matching lines verbatim, and anonymises the source to
# "Paper A/B/...". `kind` drives the card colour in the figure.
RECEIPT_SPECS = [
    {  # deterministic grep: the table's method has zero implementing code
        "audit": "1023_Over_squashing_in_Spatiotemporal_Graph_Neural_Networks",
        "source": "_audit_code/out/checks.txt",
        "match": "FOSR / RGCN search",
        "n_lines": 2,
        "kind": "missing",
        "command": "grep -ri 'fosr|rgcn|rewir' repo/",
        "consequence": "Table 2's rewiring method has no implementing code in the repo "
                       "— the entire experiment is unreproducible.",
    },
    {  # config mismatch: reported hyper-parameter absent; default differs 5x
        "audit": "768_A_High_Dimensional_Statistical_Method_for_Optimizing_Transfe",
        "source": "_audit_code/out/checks.txt",
        "match": "paper says lr=1e-5",
        "n_lines": 1,
        "kind": "difference",
        "command": "diff  paper_hparams  configs/*.json",
        "consequence": "The learning rate the paper reports is nowhere in the configs; "
                       "the committed default differs by 5×.",
    },
    {  # forensic admission, verbatim from the paper PDF (quote-anchored)
        "audit": "4598_Quantization_Error_Propagation_Revisiting_Layer_Wise_Post_Tr",
        "source": None,          # pulled from the finding quote (paper.pdf)
        "finding_match": "best seed",
        "n_lines": 2,
        "kind": "forensic",
        "command": "paper.pdf  →  Appendix D.3",
        "consequence": "Headline tables report the best seed per configuration; the "
                       "released code runs a single seed per invocation.",
    },
    {  # a CONFIRM: deterministic numeric check the claim passes (fairness)
        "audit": "1829_OLinear_A_Linear_Model_for_Time_Series_Forecasting_in_Orthog",
        "source": "_audit_code/out/q_matrices.csv",
        "match": "weather_96",
        "n_lines": 1,
        "header_line": True,
        "kind": "confirm",
        "command": "check_orthonormality(Q)  →  max|QᵀQ−I|",
        "consequence": "Confirmed: the orthogonal basis really is orthonormal "
                       "(error 4×10⁻⁷). The auditor confirms, not only refutes.",
    },
]


def _slice_file(path: Path, match: str, n_lines: int, header: bool = False):
    lines = path.read_text(errors="replace").splitlines()
    for i, ln in enumerate(lines):
        if match in ln:
            block = []
            if header and i > 0:
                block.append(lines[0])      # keep the CSV header for context
            block.extend(lines[i:i + n_lines])
            return "\n".join(block)
    return None


# ---- per-paper binary scorecard (papers × properties, for the strip heatmap) -
def _sev_categories(level):
    """audit -> set(categories with a kept finding at the given severity `level`."""
    out = {}
    for fvp in sorted(ROOT.glob("audits/*/findings_verified.json")):
        if fvp.parent.parent.name == "theory":
            continue
        vj = json.loads(fvp.read_text())
        cats = set()
        for f in vj.get("findings", []):
            if is_dropped(f):
                continue
            if (f.get("severity") or "").lower() == level:
                cats.add(f.get("category"))
        out[vj.get("audit", "")] = cats
    return out


def build_scorecard(papers, with_med=False):
    """Boolean matrix: each row a positive property (green=holds), each column a paper.

    Polarity is uniform — green is always 'good' — so sorting by #green ranks papers
    best→worst. The high-severity rows are post-verification (rejected dropped).

    When `with_med` is set, the four severity rows become tri-state: green = no kept
    finding of that category, yellow ("med") = a kept *medium* finding but no high,
    red = a kept *high* finding. The binary rows above them are unchanged either way.
    """
    high = _sev_categories("high")
    med = _sev_categories("medium") if with_med else {}

    def sev_test(cat):
        """Severity row: False=has high, 'med'=medium-only (yellow), True=clean."""
        def t(p):
            audit = p["audit"]
            if cat in high.get(audit, set()):
                return False
            if with_med and cat in med.get(audit, set()):
                return "med"
            return True
        return t

    # All 100 papers are columns, scored top-down as a cascade:
    #   • "Repository link resolves" is scored for EVERY paper (green = repo on
    #     disk, red = none).
    #   • "Real implementation (not a stub)" is scored for papers whose repo
    #     resolves (green = real code, red = stub); null (→ black) if no repo.
    #   • every row BELOW that needs real code, so it is null (→ black) for both the
    #     no-repo papers AND the stub — there is nothing to score.
    # null cells render as a solid soft-black block; for source-having non-stub
    # papers all rows are the usual green/red.
    has_code = lambda p: p["has_code"]
    real_code = lambda p: p["has_code"] and not p["is_stub"]
    always = lambda p: True
    # (label, test, gate): cell is null (→ black) wherever gate(p) is False
    ROWS = [
        ("Repository link resolves", lambda p: p["has_code"], always),
        ("Real implementation (not a stub)",
         lambda p: not p["is_stub"], has_code),
        ("Install / environment specifications provided", lambda p: p["inst_ok"], real_code),
        ("Runnable entrypoint present", lambda p: p["run_ok"], real_code),
        # Each bottom row names the audit DIMENSION, not a verdict: a green cell
        # means "no high-severity finding surfaced" — absence of evidence, not proof
        # the property holds — so the label must not assert correctness/soundness.
        # The colour (green/yellow/red) + the left % carry the result; the legend
        # carries the severity tiers, so no single "high" cut fights the 3 colours.
        ("Artifact completeness", sev_test("missing"), real_code),
        ("Code correctness", sev_test("bug"), real_code),
        ("Methodology", sev_test("methodology"), real_code),
        ("Paper–code agreement", sev_test("difference"), real_code),
    ]

    def cell(p, test, gate):
        if not gate(p):
            return None                  # None → black (no code to score)
        v = test(p)
        return v if v == "med" else bool(v)   # "med" → yellow; else green/red
    matrix = [[cell(p, test, gate) for _, test, gate in ROWS] for p in papers]
    return {"row_labels": [lab for lab, _, _ in ROWS], "matrix": matrix}


# ---- verification layer ----------------------------------------------------
# Two-stage adversarial re-check (start_verify_prompt.md): a fresh Sonnet agent
# re-verifies every finding "assume-wrong-until-proven", then an Opus pass
# re-judges any non-keep verdict. Output lands in findings_verified.json with
# per-finding `verdict` / `reason` / `changed`. Each finding also carries the
# auditor's own structured self-checks in `validator_pass` — the same three
# questions the verifier re-asks (quote anchored, code path reachable, trigger
# condition satisfiable). All counts below are read straight from those fields.
VERDICTS = ["keep", "lowered", "reject"]
GATES = ["quote_match", "control_flow", "condition_satisfiable"]
GATE_LABELS = {
    "quote_match": "Quote anchored to file:line",
    "control_flow": "Cited code path is reachable",
    "condition_satisfiable": "Trigger condition can occur",
}


def build_severity():
    """Severity × category, post-verification (rejected excluded, lowered reflected).

    Severity is the auditor's (LLM) judgment, NOT an objective check — this block
    exists only for the supplementary severity figure, never the headline suite.
    """
    SEV = ["high", "medium", "low"]
    by_cat = {c: {s: 0 for s in SEV} for c in CATEGORIES}
    high_papers = {c: set() for c in CATEGORIES}
    for fvp in sorted(ROOT.glob("audits/*/findings_verified.json")):
        if fvp.parent.parent.name == "theory":
            continue
        vj = json.loads(fvp.read_text())
        paper = vj.get("audit", "")
        for f in vj.get("findings", []):
            if is_dropped(f):
                continue                              # refuted / supplement FP / provenance FP — drop
            cat = f.get("category")
            sev = (f.get("severity") or "").lower()
            if cat in by_cat and sev in SEV:
                by_cat[cat][sev] += 1
                if sev == "high":
                    high_papers[cat].add(paper)
    return {
        "severity_order": SEV,
        "by_category": by_cat,
        "high_papers": {c: len(high_papers[c]) for c in CATEGORIES},
        "n_high": sum(by_cat[c]["high"] for c in CATEGORIES),
    }


def build_verification():
    verdicts = Counter()
    gate_pass = {g: 0 for g in GATES}
    gate_fail = {g: 0 for g in GATES}
    n_gated = 0
    cards = []
    n_verified = 0
    for fvp in sorted(ROOT.glob("audits/*/findings_verified.json")):
        if fvp.parent.parent.name == "theory":
            continue
        vj = json.loads(fvp.read_text())
        for f in vj.get("findings", []):
            n_verified += 1
            verdicts[f.get("verdict")] += 1
            vp = f.get("validator_pass")
            if vp:
                n_gated += 1
                for g in GATES:
                    if vp.get(g) is True:
                        gate_pass[g] += 1
                    elif vp.get(g) is False:
                        gate_fail[g] += 1
            ch = (f.get("changed") or "").strip()
            if ch and ch.lower() != "nothing":
                # the few findings the escalation pass actually modified
                if "revert" in ch.lower():
                    action = "Second pass overturned first pass"
                elif f.get("verdict") == "lowered":
                    action = "Downgrade confirmed on re-check"
                elif f.get("verdict") == "reject":
                    action = "Rejection upheld on re-check"
                else:
                    action = "Re-judged on escalation"
                cards.append({
                    "verdict": f.get("verdict"),
                    "severity": f.get("severity"),
                    "confidence": f.get("confidence"),
                    "action": action,
                    "title": f.get("title", ""),
                    "reason": f.get("reason", ""),
                    "changed": ch,
                })
    survived = sum(verdicts.get(v, 0) for v in ("keep", "lowered"))
    # anonymise the escalation cards (Paper A/B/...)
    for i, c in enumerate(cards):
        c["paper"] = f"Paper {chr(ord('A') + i)}"
    return {
        "n_findings": n_verified,
        "verdicts": {v: verdicts.get(v, 0) for v in VERDICTS},
        "survived": survived,
        "rejected": verdicts.get("reject", 0),
        "survival_rate": round(survived / n_verified, 4) if n_verified else 0,
        "n_changed": len(cards),
        "gates": {
            "n_gated": n_gated,
            "rows": [{"gate": g, "label": GATE_LABELS[g],
                      "pass": gate_pass[g], "fail": gate_fail[g]}
                     for g in GATES],
        },
        "escalation_cards": cards,
    }


def build_receipts(papers_by_audit):
    receipts, label = [], ord("A")
    for spec in RECEIPT_SPECS:
        adir = ROOT / "audits" / spec["audit"]
        text = None
        if spec["source"] is None:
            # pull verbatim from the matching finding's anchored quote
            fj = json.loads((adir / "findings.json").read_text())
            for f in fj.get("findings", []):
                q = (f.get("quote") or "")
                if spec["finding_match"].lower() in q.lower():
                    text = "\n".join(q.strip().splitlines()[: spec["n_lines"]])
                    break
        else:
            src = adir / spec["source"]
            if src.exists():
                text = _slice_file(src, spec["match"], spec["n_lines"],
                                   spec.get("header_line", False))
        if not text:
            print(f"  [receipt] WARN: no match for {spec['audit'][:24]} / {spec['match']!r}")
            continue
        receipts.append({
            "paper": f"Paper {chr(label)}",
            "kind": spec["kind"],
            "command": spec["command"],
            "output": text,
            "consequence": spec["consequence"],
        })
        label += 1
    return receipts


# ---- load -----------------------------------------------------------------
# Enumerate the WHOLE 100-paper sample via metadata.txt (present in every sampled
# folder), NOT just folders with findings.json. The 16 papers that release no
# author code are "stubbed" — their audit.md says "No code present" and their
# findings.json / findings_verified.json were retired to _superseded_audit/ — so
# they carry zero findings, but they MUST still count in the 100-paper denominator
# (the headline is "84 of 100 release the authors' code"). A stub paper therefore
# enters `papers` with findings=[] and has_code=False.
papers, papers_by_audit = [], {}
for meta in sorted(ROOT.glob("audits/*/metadata.txt")):
    d = meta.parent
    if d.name == "theory" or d.parent.name == "theory":
        continue
    fjp = d / "findings.json"
    findings = json.loads(fjp.read_text()).get("findings", []) if fjp.exists() else []
    # Attach the verified verdicts (two-stage verifier + supplement-fetch
    # correction) so the availability/coverage counts can honour is_dropped().
    fvp = d / "findings_verified.json"
    if fvp.exists():
        vmap = {vf.get("id"): vf
                for vf in json.loads(fvp.read_text()).get("findings", [])}
        for f in findings:
            vf = vmap.get(f.get("id"), {})
            f["verdict"] = vf.get("verdict")
            f["supplement_verdict"] = vf.get("supplement_verdict")
            f["provenance_verdict"] = vf.get("provenance_verdict")
    repos = list((d / "code").glob("*/")) if (d / "code").exists() else []
    # Repo-provenance correction (mirrors the supplement correction, but LOWERS
    # source-present): a paper whose cloned repos are ALL non-core — baseline /
    # dependency / different-paper / stub, recorded as core_present=="no" in
    # repo_provenance.json — released no author core in the snapshot, so it does
    # not count as source-present even though a code/ dir exists.
    prov_core = None
    pjp = d / "repo_provenance.json"
    if pjp.exists():
        try:
            prov_core = json.loads(pjp.read_text()).get("core_present")
        except Exception:
            prov_core = None
    has_code = len(repos) > 0 and prov_core != "no"
    cl = d / "code_links.txt"
    url_ok = cl.exists() and bool(cl.read_text().strip())
    inst_ok = any(repo_has_install(r) for r in repos)
    run_ok = any(repo_has_runnable(r) for r in repos)
    # OBJECTIVE code-coverage signals (topic-anchored, no severity):
    #   most_ok  — runnable repo with NO wholesale-missing-code finding
    #              ("the bulk of the code is committed, not a stub")
    #   trace_ok — additionally NO reported result lacks committed code
    #              ("every published result traces to committed code")
    n_trace_gap = sum(1 for f in findings if is_traceability_gap(f))
    n_wholesale = sum(1 for f in findings if is_wholesale_missing(f))
    # filesystem stub: a resolvable repo that ships NO real code (count==0)
    n_code_files = sum(repo_code_file_count(r) for r in repos)
    is_stub = has_code and n_code_files == 0
    p = {
        "audit": d.name,
        "n": len(findings),
        "url_ok": url_ok, "has_code": has_code, "prov_core": prov_core,
        "inst_ok": inst_ok, "run_ok": run_ok,
        "n_code_files": n_code_files, "is_stub": is_stub,
        "most_ok": n_wholesale == 0,
        "trace_ok": n_wholesale == 0 and n_trace_gap == 0,
        "n_trace_gap": n_trace_gap, "n_wholesale": n_wholesale,
        "cat": Counter(f.get("category") for f in findings),
        "findings": findings,
    }
    papers.append(p)
    papers_by_audit[d.name] = p

ALL = [f for p in papers for f in p["findings"]]
# SURV = findings that survive as real defects (drop verifier-rejected + supplement
# false positives). N stays the GROSS count (the audit surfaced N findings; the
# verification figures report how many of those survived).
SURV = [f for f in ALL if not is_dropped(f)]
NP, N = len(papers), len(ALL)

# ---- funnel: cumulative, monotone, every stage objective ------------------
STAGES = [
    ("Code URL linked", lambda p: p["url_ok"]),
    ("Source code present", lambda p: p["url_ok"] and p["has_code"]),
    ("Install / environment spec",
     lambda p: p["url_ok"] and p["has_code"] and p["inst_ok"]),
    ("Runnable entrypoint",
     lambda p: p["url_ok"] and p["has_code"] and p["inst_ok"] and p["run_ok"]),
    ("Most of the code committed (no completeness gap flagged)",
     lambda p: p["url_ok"] and p["has_code"] and p["inst_ok"] and p["run_ok"]
     and p["most_ok"]),
    ("All published results trace to committed code",
     lambda p: p["url_ok"] and p["has_code"] and p["inst_ok"] and p["run_ok"]
     and p["most_ok"] and p["trace_ok"]),
]
funnel = [{"label": lab, "count": sum(1 for p in papers if test(p))}
          for lab, test in STAGES]
# deepest stage index each paper reaches (0..len-1; -1 = fails first gate)
for p in papers:
    deepest = -1
    for i, (_, test) in enumerate(STAGES):
        if test(p):
            deepest = i
        else:
            break
    p["deepest"] = deepest


# ---- evidence-strength ladder (how each finding can be re-checked) ---------
n_quote = sum(1 for f in ALL if f.get("quote"))
n_code = sum(1 for f in ALL if evidence_kind(f.get("file", "")) == "code")
n_check = sum(1 for f in ALL if f.get("check_script"))
n_check_ondisk = sum(
    1 for p in papers for f in p["findings"]
    if f.get("check_script")
    and (ROOT / "audits" / p["audit"] / f["check_script"]).exists())

# ---- verification (two-stage adversarial re-check) -------------------------
verification = build_verification()
severity_breakdown = build_severity()
scorecard_with_med = build_scorecard(papers, with_med=True)

# ---- assemble & write -----------------------------------------------------
out = {
    "n_papers": NP,
    "n_findings": N,
    "funnel": funnel,
    "funnel_stage_labels": [lab for lab, _ in STAGES],
    "per_paper_deepest": sorted((p["deepest"] for p in papers), reverse=True),
    "by_category": {c: sum(1 for f in SURV if f.get("category") == c)
                    for c in CATEGORIES},
    "papers_by_category": {
        c: sum(1 for p in papers
               if any(f.get("category") == c and not is_dropped(f)
                      for f in p["findings"]))
        for c in CATEGORIES},
    "evidence_ladder": [
        {"label": "Verbatim quote, anchored to file:line",
         "count": n_quote, "tier": "anchored"},
        {"label": "Cites an executable code location",
         "count": n_code, "tier": "located"},
        {"label": "Backed by a re-runnable deterministic check",
         "count": n_check, "tier": "rerunnable"},
        # validator-survived band: findings kept or lowered (not rejected) after
        # the two-stage adversarial re-check (Sonnet re-verify → Opus escalation)
        {"label": "Survived independent adversarial validator",
         "count": verification["survived"], "tier": "validated"},
    ],
    "evidence_extra": {"n_quote": n_quote, "n_check_ondisk": n_check_ondisk},
    "category_labels": {
        "missing": "Missing code / data",
        "difference": "Paper–code mismatch",
        "bug": "Technical bug",
        "methodology": "Methodology / validity",
    },
    # severity kept ONLY as an annotation, never an organizing axis
    "severity_note": dict(Counter(f.get("severity") for f in SURV)),
    "receipts": build_receipts(papers_by_audit),
    "severity_breakdown": severity_breakdown,
    "scorecard_with_med": scorecard_with_med,
}
(DATA / "figure_data.json").write_text(json.dumps(out, indent=2, ensure_ascii=False))

print(f"Loaded {N} findings across {NP} papers")
print("funnel:", " → ".join(f"{s['count']}" for s in funnel))
print(f"evidence: quote {n_quote}/{N}  code {n_code}/{N}  "
      f"check {n_check}/{N} (on-disk {n_check_ondisk})")
print(f"receipts: {len(out['receipts'])} cards")
v = verification
print(f"verification: {v['survived']}/{v['n_findings']} survived "
      f"({v['survival_rate']*100:.1f}%), verdicts {v['verdicts']}, "
      f"{v['n_changed']} changed on escalation")
sb = severity_breakdown
print(f"severity: {sb['n_high']} high-severity findings — "
      + " ".join(f"{c}:{sb['by_category'][c]['high']}" for c in CATEGORIES))
print(f"wrote {DATA / 'figure_data.json'}")
