# Audit runner — sealed sandbox

You are running inside a **sealed sandbox**: this run directory.
Treat this directory as the entire world.

## Hard isolation rules (do not violate)
- Read ONLY files inside this directory: `paper.pdf`, `paper_text.txt`,
  `metadata.txt`, `code_links.txt`, the `code/` tree, `auditowl_prompt_neurips.md`,
  `findings-schema.md`.
- Do NOT read, list, glob, or grep anything OUTSIDE this directory. In
  particular never touch `../`, any sibling `run_*/`, the `audits/` tree,
  `_summary/`, `_robustness/`, or any pre-existing
  `audit.md` / `findings.json`.
- Do NOT use the network, `git`, `gh`, or any web/search tool. Do NOT re-clone
  or fetch code. The `code/` tree is READ-ONLY.
- Write everything (audit.md, `_audit_code/`, `out/`, findings.json,
  token_cost.json) INSIDE this run directory only.

## The paper: PDF + text (use BOTH, exactly as `auditowl_prompt_neurips.md` says)
- `paper.pdf` is the **source of truth** for reading, verifying, and quoting —
  only the PDF preserves equations, figures, tables, and layout. Read and quote
  from it; findings cite `file: paper.pdf`.
- `paper_text.txt` is a faithful plain-text extraction of that same PDF — use it
  to `grep`/search fast, then re-locate and confirm each quote in `paper.pdf`.
- Do NOT install PDF libraries or re-extract the PDF; the extraction is provided.

## Task
1. Audit this paper by following `auditowl_prompt_neurips.md` **exactly**. The
   cloned repo is under `code/<owner>__<repo>/`; the paper is `paper.pdf` (with
   `paper_text.txt` as the searchable extraction); metadata in `metadata.txt`.
   Findings schema is `findings-schema.md`.
2. Write `audit.md` with the YAML finding blocks.
3. Extract the sidecar:
   `python extract_findings.py audit.md --out findings.json`
4. Stop. Do not verify your own findings (a separate verifier pass does that).
