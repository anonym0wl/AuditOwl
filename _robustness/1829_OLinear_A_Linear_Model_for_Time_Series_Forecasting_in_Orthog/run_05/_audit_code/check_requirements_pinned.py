"""Checks whether requirements.txt pins any dependency versions, supporting
finding unpinned-dependencies. Read-only over code/."""
import os, json, re

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "code", "jackyue1994__OLinear"))
req = os.path.join(REPO, "requirements.txt")
lines = [l.strip() for l in open(req, encoding="utf-8") if l.strip()]
pinned = [l for l in lines if re.search(r"[=<>~!]=|[<>]", l)]
out = {
    "requirements_lines": lines,
    "n_total": len(lines),
    "n_pinned": len(pinned),
    "pinned_lines": pinned,
    "python_version_specified": any("python" in l.lower() for l in lines),
}
with open(os.path.join(os.path.dirname(__file__), "out", "requirements.json"), "w") as fh:
    json.dump(out, fh, indent=2)
print(json.dumps(out, indent=2))
