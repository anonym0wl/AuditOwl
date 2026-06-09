#!/usr/bin/env python3
"""
status.py — progress + batch driver for the robustness runs.

State is derived entirely from the artefacts on disk (no separate mutable
tracker), so it is always consistent and resumable:

    audit_done(run)  := run_NN/findings.json exists and parses
    verify_done(run) := run_NN/findings_verified.json exists and parses

A run is PENDING until verify_done. Runs are ordered paper-major (selection
order) then run-minor, so batch 1 = paper 1's run_01..run_10, etc.

Usage:
    python _robustness/status.py                 # progress table
    python _robustness/status.py --next 10        # human list of next batch
    python _robustness/status.py --next 10 --json # JSON to pass as Workflow args:
                                                  #   {"records":[{paper,dir,run}, ...]}
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RB = Path(__file__).resolve().parent


def _parses(p: Path) -> bool:
    if not p.exists():
        return False
    try:
        json.loads(p.read_text())
        return True
    except Exception:
        return False


def scan() -> list[dict]:
    sel = json.loads((RB / "selection.json").read_text())
    rows = []
    for r in sel["selected"]:                       # selection order = paper-major
        paper = r["paper"]
        pdir = RB / paper
        for rd in sorted(pdir.glob("run_*")):       # run-minor
            adone = _parses(rd / "findings.json")
            vdone = _parses(rd / "findings_verified.json")
            rows.append({
                "paper": paper,
                "run": rd.name,
                "dir": str(rd.relative_to(ROOT)),
                "audit_done": adone,
                "verify_done": vdone,
                "pending": not vdone,
            })
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--next", type=int, metavar="N", help="emit the next N pending runs")
    ap.add_argument("--paper", help="restrict --next to runs whose paper contains this substring")
    ap.add_argument("--json", action="store_true", help="machine output for Workflow args")
    args = ap.parse_args()

    rows = scan()
    if not rows:
        print("no sandboxes yet — run: python _robustness/build_sandboxes.py --runs 10")
        return

    if args.next:
        pending = [r for r in rows if r["pending"]]
        if args.paper:
            pending = [r for r in pending if args.paper in r["paper"]]
        batch = pending[: args.next]
        if args.json:
            print(json.dumps({"records": [{"paper": r["paper"], "dir": r["dir"], "run": r["run"]} for r in batch]}))
            return
        print(f"next batch ({len(batch)} of {sum(r['pending'] for r in rows)} pending):")
        for r in batch:
            need = "audit+verify" if not r["audit_done"] else "verify"
            print(f"  {r['paper'][:40]:40s} {r['run']}  needs {need}")
        print("\nto run it, pass this as Workflow args:")
        print("  python _robustness/status.py --next %d --json" % args.next)
        return

    # progress table
    from collections import defaultdict
    by = defaultdict(lambda: [0, 0, 0])
    for r in rows:
        by[r["paper"]][0] += 1
        by[r["paper"]][1] += r["audit_done"]
        by[r["paper"]][2] += r["verify_done"]
    print(f"{'paper':42s}  runs  audited  verified")
    tot = [0, 0, 0]
    for p, (n, a, v) in by.items():
        print(f"{p[:42]:42s}  {n:4d}  {a:7d}  {v:8d}")
        tot[0] += n; tot[1] += a; tot[2] += v
    print(f"{'TOTAL':42s}  {tot[0]:4d}  {tot[1]:7d}  {tot[2]:8d}")
    pend = sum(r["pending"] for r in rows)
    print(f"\n{pend} pending. next: python _robustness/status.py --next 10 --json")


if __name__ == "__main__":
    main()
