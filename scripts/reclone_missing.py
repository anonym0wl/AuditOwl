#!/usr/bin/env python3
"""Re-clone author repos for audit folders whose `code/` is missing or empty.

`**/code/` is gitignored and for a batch of papers the clone was never persisted.
This finds each paper's author repo URL from the committed evidence — the paper
text, `code_links.txt`, and `code/<owner>__<repo>/` prefixes inside findings —
filters out cited baselines / dependencies / datasets, picks the most
author-like repo (name-token overlap with the title), and shallow-clones it into
`audits/<paper>/code/<owner>__<repo>/`.

Idempotent; LFS smudge and credential prompts disabled so clones fail fast.
Run:  python scripts/reclone_missing.py
"""
import json
import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENV = {**os.environ, "GIT_TERMINAL_PROMPT": "0", "GIT_LFS_SKIP_SMUDGE": "1"}
URL_RE = re.compile(r"https?://(?:github\.com|gitlab\.com)/[A-Za-z0-9_.\-]+/[A-Za-z0-9_.\-]+")
# orgs that only ever host baselines / frameworks / dependencies, never the paper's repo
BASELINE_ORG = re.compile(
    r"/(huggingface|pytorch|facebookresearch|google-research|google|openai|microsoft|"
    r"NVIDIA|rwightman|pyg-team|Lightning-AI|tloen|volcengine|black-forest-labs|"
    r"open-mmlab|ultralytics|CompVis|stability-ai|Jiayi-Pan|Kuuuube|"
    r"jamesrobertlloyd|isaac-sim)/", re.I)
DATASET_NAME = re.compile(r"(dataset|adbench|benchmark)", re.I)
# specific non-author repos seen mis-picked: TinyZero is an upstream RL framework
# (not the steganography paper's code); Circular_Area is an osu! tablet-area tool
# cited only in a HyPlaneHead footnote.
WRONG_REPO = re.compile(r"/(TinyZero|Circular_Area)$", re.I)


def candidates(folder: Path):
    urls = set()
    for fn in ("paper_text.txt", "code_links.txt"):
        p = folder / fn
        if p.exists():
            for m in URL_RE.findall(p.read_text(errors="replace")):
                urls.add(m.rstrip(".),"))
    fj = folder / "findings.json"
    if fj.exists():
        for f in json.load(open(fj)).get("findings", []):
            m = re.match(r"code/([^/]+)__([^/]+)/", f.get("file", "") or "")
            if m:
                urls.add(f"https://github.com/{m.group(1)}/{m.group(2)}")
    # drop baseline orgs and obvious dataset/benchmark repos
    return {u for u in urls if not BASELINE_ORG.search(u)
            and not WRONG_REPO.search(u) and not DATASET_NAME.search(u.split("/")[-1])}


def pick_author(folder: Path, urls):
    """Pick the repo whose name best overlaps the paper title tokens."""
    title = ""
    md = folder / "metadata.txt"
    if md.exists():
        for line in md.read_text().splitlines():
            if line.lower().startswith("title:"):
                title = line.split(":", 1)[1].lower()
    tokens = {t for t in re.findall(r"[a-z0-9]{4,}", title)}

    def score(u):
        name = u.split("/")[-1].lower().replace(".git", "")
        nm = set(re.findall(r"[a-z0-9]{3,}", name))
        return len(nm & tokens)
    return sorted(urls, key=lambda u: (-score(u), len(u)))[0]


def dest_name(url: str) -> str:
    parts = url.replace(".git", "").rstrip("/").split("/")
    return f"{parts[-2]}__{parts[-1]}"


def main():
    todo = []
    for fjp in sorted(ROOT.glob("audits/*/findings.json")):
        folder = fjp.parent
        if folder.parent.name == "theory":
            continue
        code = folder / "code"
        if code.exists() and any(p.is_dir() for p in code.glob("*/")):
            continue
        urls = candidates(folder)
        if urls:
            todo.append((folder, pick_author(folder, urls)))

    print(f"{len(todo)} papers with a findable author repo\n", flush=True)
    results = []
    for folder, url in todo:
        dest = folder / "code" / dest_name(url)
        if dest.exists() and any(dest.iterdir()):
            results.append((folder.name, url, "cached"))
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        print(f"  clone {url}", flush=True)
        try:
            r = subprocess.run(
                ["git", "clone", "--depth", "1", "--recurse-submodules",
                 "--shallow-submodules", url, str(dest)],
                capture_output=True, text=True, timeout=300, env=ENV)
            status = "ok" if r.returncode == 0 else \
                "FAILED: " + (r.stderr.strip().splitlines() or ["?"])[-1][:80]
        except subprocess.TimeoutExpired:
            status = "TIMEOUT"
        results.append((folder.name, url, status))

    print("\n=== RESULTS ===", flush=True)
    for n, u, s in results:
        print(f"  [{s[:42]:42s}] {n[:40]:40s} {u}", flush=True)
    ok = sum(1 for _, _, s in results if s in ("ok", "cached"))
    print(f"\n{ok}/{len(results)} cloned", flush=True)


if __name__ == "__main__":
    main()
