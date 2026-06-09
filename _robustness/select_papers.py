#!/usr/bin/env python3
"""
select_papers.py — deterministically draw the robustness-experiment sample.

We re-run the full audit->verify pipeline N times on a handful of papers to
measure the *test-retest reliability* of the auditor. To make that test
meaningful the auditor must have had a real codebase to reason about, so the
eligible frame is "papers for which we retrieved a non-trivial codebase".

Eligibility (a paper folder under audits/, excluding audits/theory/):
  - has a code/ subdirectory,
  - code/ holds >= MIN_SRC real source files (so the audit saw actual code),
  - has findings.json (it was audited -> we have a reference run).

Draw: uniform random, fixed seed, recorded in draw order -> selection.json.
This mirrors the project's seed=42 sampling ethos (see SAMPLING.md).

Run:
    python _robustness/select_papers.py            # draw + write selection.json
    python _robustness/select_papers.py --list     # just print the eligible frame
"""
from __future__ import annotations
import argparse
import json
import os
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AUDITS = ROOT / "audits"
OUT = Path(__file__).resolve().parent / "selection.json"

SEED = 42
K = 5
MIN_SRC = 5

SRC_EXT = {
    ".py", ".ipynb", ".sh", ".cpp", ".cc", ".cu", ".cuh", ".c", ".h", ".hpp",
    ".java", ".m", ".jl", ".r", ".js", ".ts", ".go", ".rs", ".scala", ".lua",
}


def count_src(code_dir: Path) -> int:
    n = 0
    for dirpath, dirnames, filenames in os.walk(code_dir):
        # skip obvious vendored/cache junk so the count reflects authored code
        dirnames[:] = [d for d in dirnames if d not in {
            ".git", "node_modules", "__pycache__", ".venv", "venv",
            "site-packages", ".ipynb_checkpoints",
        }]
        for f in filenames:
            if Path(f).suffix.lower() in SRC_EXT:
                n += 1
    return n


def dir_kb(p: Path) -> int:
    total = 0
    for dirpath, _, filenames in os.walk(p):
        for f in filenames:
            fp = Path(dirpath) / f
            try:
                total += fp.stat().st_size
            except OSError:
                pass
    return total // 1024


def finding_stats(findings_json: Path) -> dict:
    try:
        data = json.loads(findings_json.read_text())
    except Exception:
        return {"n_findings": 0, "n_high": 0, "categories": {}}
    fs = data.get("findings", data if isinstance(data, list) else [])
    cats: dict[str, int] = {}
    n_high = 0
    for f in fs:
        cats[f.get("category", "?")] = cats.get(f.get("category", "?"), 0) + 1
        if f.get("severity") == "high":
            n_high += 1
    return {"n_findings": len(fs), "n_high": n_high, "categories": cats}


def eligible_frame() -> list[dict]:
    rows = []
    for d in sorted(AUDITS.iterdir()):
        if not d.is_dir() or d.name == "theory":
            continue
        code = d / "code"
        findings = d / "findings.json"
        if not code.is_dir() or not findings.exists():
            continue
        nsrc = count_src(code)
        if nsrc < MIN_SRC:
            continue
        row = {
            "paper": d.name,
            "src_files": nsrc,
            "code_kb": dir_kb(code),
            "has_verified": (d / "findings_verified.json").exists(),
            **finding_stats(findings),
        }
        rows.append(row)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true", help="print eligible frame and exit")
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("-k", type=int, default=K)
    args = ap.parse_args()

    frame = eligible_frame()
    frame_ids = sorted(r["paper"] for r in frame)
    print(f"eligible frame: {len(frame)} papers with retrieved codebase "
          f"(>= {MIN_SRC} source files + findings.json)")

    if args.list:
        for r in sorted(frame, key=lambda x: -x["src_files"]):
            print(f"  {r['src_files']:5d} src  {r['code_kb']:>9d}KB  "
                  f"{r['n_findings']:2d} find ({r['n_high']} high)  {r['paper']}")
        return

    picked_ids = random.Random(args.seed).sample(frame_ids, args.k)  # draw order
    by_id = {r["paper"]: r for r in frame}
    picked = [by_id[p] for p in picked_ids]

    sel = {
        "seed": args.seed,
        "k": args.k,
        "min_src_files": MIN_SRC,
        "frame_size": len(frame),
        "selected": picked,
    }
    OUT.write_text(json.dumps(sel, indent=2))
    print(f"\ndrew {args.k} papers (seed={args.seed}) -> {OUT.relative_to(ROOT)}")
    for r in picked:
        print(f"  - {r['paper']}")
        print(f"      {r['src_files']} src files, {r['code_kb']}KB, "
              f"{r['n_findings']} findings ({r['n_high']} high), "
              f"verified={r['has_verified']}, cats={r['categories']}")


if __name__ == "__main__":
    main()
