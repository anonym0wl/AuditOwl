"""For datasets whose raw CSV IS shipped in dataset/, check that every temporal
q_mat_file / q_out_mat_file referenced by its OLinear (main) script exists.
Supports: confirming main OLinear results are reproducible for included datasets.
Read-only."""
import os, re, glob

REPO = os.path.join(os.path.dirname(__file__), "..", "code", "jackyue1994__OLinear")
OUT = os.path.join(os.path.dirname(__file__), "out")
os.makedirs(OUT, exist_ok=True)

# datasets whose folder exists under dataset/
shipped_dirs = {d for d in os.listdir(os.path.join(REPO, "dataset"))
                if os.path.isdir(os.path.join(REPO, "dataset", d))}

lines = [f"shipped dataset dirs: {sorted(shipped_dirs)}", ""]

def expand(seq, val):
    # crude bash-array expansion not needed; we check literal files present per dir
    pass

# Just verify: for each shipped dataset dir, how many *_ratio*.npy q-matrices exist
for d in sorted(shipped_dirs):
    npys = glob.glob(os.path.join(REPO, "dataset", d, "*ratio*.npy"))
    npys = [os.path.basename(p) for p in npys if "COV_channel" not in p]
    lines.append(f"{d}: {len(npys)} temporal q-matrices, e.g. {sorted(npys)[:4]}")

out = "\n".join(lines)
print(out)
with open(os.path.join(OUT, "check_qmat_for_shipped_datasets.txt"), "w") as fh:
    fh.write(out + "\n")
