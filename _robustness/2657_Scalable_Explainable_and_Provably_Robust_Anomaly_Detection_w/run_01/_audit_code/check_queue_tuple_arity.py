"""Checks queue.put arity vs queue.get unpack arity in FullExperiments/ContaminationStudies.
Supports finding 'worker-error-tuple-arity-mismatch': the worker's except branch puts a
2-tuple while run_model_with_timeout unpacks 4 values, so an exception raised OUTSIDE
train_and_eval's own try/except would raise ValueError in the parent instead of being logged.
Read-only static check (regex + simulated unpack)."""
import re, os, json

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "code", "ZhongLIFR__TCCM-NIPS"))
out = {}
for fname in ["FullExperiments.py", "ContaminationStudies.py"]:
    path = os.path.join(REPO, fname)
    src = open(path).read()
    puts = re.findall(r"queue\.put\((.*?)\)\s*$", src, flags=re.M)
    # arity of the unpack target on the get line
    get_unpack = re.findall(r"^\s*([\w,\s]+)=\s*queue\.get\(\)", src, flags=re.M)
    unpack_arity = None
    if get_unpack:
        unpack_arity = len([t for t in get_unpack[0].split(",") if t.strip()])
    put_arities = []
    for p in puts:
        # crude tuple-element count for the top-level literal tuple
        if p.strip().startswith("("):
            inner = p.strip()[1:-1]
            # count commas not inside parens
            depth = 0; n = 1; counted_empty = inner.strip() == ""
            for ch in inner:
                if ch in "([{": depth += 1
                elif ch in ")]}": depth -= 1
                elif ch == "," and depth == 0: n += 1
            put_arities.append(0 if counted_empty else n)
        else:
            put_arities.append(1)  # putting a single variable (the func result)
    out[fname] = {
        "queue_put_exprs": [p.strip() for p in puts],
        "queue_put_literal_tuple_arities": put_arities,
        "queue_get_unpack_arity": unpack_arity,
        "mismatch_present": any(a not in (None, unpack_arity) and a != 1 for a in put_arities),
    }

# Simulate the failing unpack to demonstrate the runtime error
demo = None
try:
    status, result, train_time, test_time = ("ModERROR", "some error")  # the except-branch put
except ValueError as e:
    demo = f"ValueError on unpack: {e}"
out["_demo_unpack_2tuple_into_4"] = demo

print(json.dumps(out, indent=2))
with open(os.path.join(os.path.dirname(__file__), "out", "queue_tuple_arity.json"), "w") as f:
    json.dump(out, f, indent=2)
