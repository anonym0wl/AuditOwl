#!/usr/bin/env python3
"""Portable runner for the robustness replicates, using the public Claude Agent SDK.

For each pending sealed sandbox (`<paper>/run_NN/`), this runs the same two-stage
pipeline the study used:
  1. AUDIT    (Opus)   reads run_NN/AGENT_INSTRUCTIONS.md, writes audit.md + findings.json
  2. VERIFY   (Sonnet) reads run_NN/VERIFIER_INSTRUCTIONS.md, writes findings_verified.json
  3. ESCALATE (Opus)   only if the verifier left any non-'keep' verdict

It replaces the authors' internal batch orchestrator: anyone with an API key can
run the experiment with the two commands below. Pending detection is delegated to
status.py, and every run self-skips if its output already exists, so an
interrupted batch resumes cleanly.

Prerequisites
  pip install claude-agent-sdk
  export ANTHROPIC_API_KEY=...                      # from https://platform.claude.com
  python _robustness/build_sandboxes.py --runs 10   # materialise the sandboxes first
                                                    # (needs the rebuilt audit inputs; see README)

Usage
  python _robustness/run_batch.py --next 10                 # run the next 10 pending runs
  python _robustness/run_batch.py --next 10 --dry-run       # list the batch, do nothing
  python _robustness/run_batch.py --next 10 --concurrency 4
"""
from __future__ import annotations
import argparse
import asyncio
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RB = Path(__file__).resolve().parent

# Same model split the study used: Opus audits + escalates, Sonnet first-pass verify.
OPUS = "claude-opus-4-8"
SONNET = "claude-sonnet-4-6"
TOOLS = ["Read", "Write", "Bash", "Grep", "Glob"]   # no network/git: isolation is in the prompts

try:
    from claude_agent_sdk import query, ClaudeAgentOptions
except ImportError:
    query = None   # reported in main() so --dry-run works without the SDK installed


def pending_records(n: int) -> list[dict]:
    """Ask status.py for the next n pending runs: [{paper, dir, run}, ...]."""
    out = subprocess.check_output(
        [sys.executable, str(RB / "status.py"), "--next", str(n), "--json"], text=True)
    return json.loads(out).get("records", [])


def _parses(p: Path) -> bool:
    try:
        json.loads(p.read_text())
        return True
    except Exception:
        return False


def _has_nonkeep(p: Path) -> bool:
    try:
        fv = json.loads(p.read_text())
        findings = fv.get("findings", fv) if isinstance(fv, dict) else fv
        return any(str(f.get("verdict", "keep")).lower() != "keep" for f in findings)
    except Exception:
        return False


async def _run_agent(prompt: str, cwd: Path, model: str) -> None:
    opts = ClaudeAgentOptions(cwd=str(cwd), model=model, allowed_tools=TOOLS,
                              permission_mode="bypassPermissions")
    async for _ in query(prompt=prompt, options=opts):
        pass   # the agent writes its outputs into cwd; we just drive it to completion


async def run_one(rec: dict) -> dict:
    d = ROOT / rec["dir"]
    # 1. AUDIT (skip if already done)
    if not _parses(d / "findings.json"):
        await _run_agent(
            "Read AGENT_INSTRUCTIONS.md in this directory and follow it exactly: "
            "produce audit.md, then run the extractor to write findings.json. "
            "Stay strictly inside this directory.", d, OPUS)
    # 2. VERIFY (Sonnet first pass)
    if not _parses(d / "findings_verified.json"):
        await _run_agent(
            "Read VERIFIER_INSTRUCTIONS.md in this directory and follow it exactly: "
            "re-check every finding in findings.json against its cited code location and "
            "write findings_verified.json. Stay strictly inside this directory.", d, SONNET)
    # 3. ESCALATE (Opus) only when the verifier left a non-'keep' verdict
    if _has_nonkeep(d / "findings_verified.json"):
        await _run_agent(
            "Read findings_verified.json in this directory. For every finding whose verdict "
            "is not 'keep' (reject / lowered / cannot-verify), re-open its cited file:line "
            "under code/ and confirm or correct that entry, rewriting only those entries "
            "(leave 'keep' findings untouched). Stay strictly inside this directory.", d, OPUS)
    return {"paper": rec["paper"], "run": rec["run"],
            "audited": _parses(d / "findings.json"),
            "verified": _parses(d / "findings_verified.json")}


async def _main_async(records: list[dict], concurrency: int) -> list[dict]:
    sem = asyncio.Semaphore(concurrency)

    async def guarded(rec: dict) -> dict:
        async with sem:
            print(f"[run] {rec['paper'][:12]}/{rec['run']}", flush=True)
            return await run_one(rec)

    return await asyncio.gather(*(guarded(r) for r in records))


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Run the next batch of robustness replicates via the Claude Agent SDK.")
    ap.add_argument("--next", type=int, default=10, help="how many pending runs to process")
    ap.add_argument("--concurrency", type=int, default=4, help="max runs in flight at once")
    ap.add_argument("--dry-run", action="store_true", help="list the batch and exit")
    args = ap.parse_args()

    records = pending_records(args.next)
    if not records:
        print("nothing pending: all runs are verified (check `python _robustness/status.py`).")
        return
    print(f"batch: {len(records)} pending run(s)")
    for r in records:
        print(f"  - {r['paper']}/{r['run']}  ({r['dir']})")
    if args.dry_run:
        return
    if query is None:
        sys.exit("claude-agent-sdk is not installed. Run: pip install claude-agent-sdk")

    results = asyncio.run(_main_async(records, args.concurrency))
    ok = sum(1 for r in results if r["verified"])
    print(f"\ndone: {ok}/{len(results)} verified. Re-run until status.py shows 0 pending, "
          f"then: python _robustness/analyze.py")


if __name__ == "__main__":
    main()
