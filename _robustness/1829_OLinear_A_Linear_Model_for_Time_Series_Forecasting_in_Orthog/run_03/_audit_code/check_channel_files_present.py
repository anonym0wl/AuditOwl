"""Counts which *_COV_channel_*.npy files the OLinear-C scripts require vs which
are actually shipped in dataset/. Supports finding: olinear-c-channel-mats-missing.
Read-only; lists present/absent precomputed channel correlation matrices."""
import os, re, glob

REPO = os.path.join(os.path.dirname(__file__), "..", "code", "jackyue1994__OLinear")
OUT = os.path.join(os.path.dirname(__file__), "out")
os.makedirs(OUT, exist_ok=True)

# required by OLinear_C scripts
req = set()
for sh in glob.glob(os.path.join(REPO, "scripts", "OLinear_C", "**", "*.sh"), recursive=True):
    with open(sh) as f:
        for line in f:
            m = re.search(r"--q_channel_file\s+(\S+\.npy)", line)
            if m:
                req.add(m.group(1))

present = set(os.path.basename(p) for p in glob.glob(os.path.join(REPO, "dataset", "**", "*COV_channel*.npy"), recursive=True))

missing = sorted(req - present)
lines = []
lines.append(f"required by OLinear_C scripts: {len(req)}")
lines.append(f"present in dataset/:           {len(present)} -> {sorted(present)}")
lines.append(f"MISSING ({len(missing)}):")
for m in missing:
    lines.append(f"  - {m}")
out = "\n".join(lines)
print(out)
with open(os.path.join(OUT, "check_channel_files_present.txt"), "w") as fh:
    fh.write(out + "\n")
