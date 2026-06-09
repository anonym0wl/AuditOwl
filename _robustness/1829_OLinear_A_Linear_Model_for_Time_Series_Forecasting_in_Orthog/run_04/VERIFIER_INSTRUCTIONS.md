# Verify runner — sealed sandbox

You are running inside a **sealed sandbox**: this run directory.
A prior pass in THIS directory produced `audit.md` + `findings.json`. Verify them.

## Hard isolation rules (do not violate)
- Read ONLY files inside this directory.
- Do NOT read any sibling `run_*/`, the `audits/` tree, `_summary/`, or any
  other paper's files. Do NOT use the network, `git`, `gh`, or web/search.
- `code/` is READ-ONLY. Write only `findings_verified.json` and `_verifier_code/`.

## Task
Verify the audit by following `verifier-prompt.md` **exactly**: re-open each
finding's cited `file:line` in `code/<owner>__<repo>/`, compare against the
quote, and assign `verdict` (keep / lower / reject / cannot-verify) with a
`reason` and `changed`. A finding's `file` is relative to the repo root inside
`code/`; for paper-side claims (`file: paper.pdf`) re-locate the quote in
`paper.pdf` (use `paper_text.txt` to search). Budget ~3-5 tool calls per
finding; cited-location-only. Write
`findings_verified.json` once at the end (original findings + the new fields).
