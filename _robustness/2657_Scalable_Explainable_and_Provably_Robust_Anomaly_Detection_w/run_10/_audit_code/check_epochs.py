"""Compare hardcoded TCCM epochs in FMAD/functions.py against paper Table 5.
Supports finding epoch-selection-csm-missing (epochs hardcoded, no CSM code)."""
import re, os
ROOT = os.path.join(os.path.dirname(__file__), "..", "code", "ZhongLIFR__TCCM-NIPS")
src = open(os.path.join(ROOT, "FMAD", "functions.py")).read()
# Parse the elif "<name>" in dataset_name: epoch_size = N
pairs = re.findall(r'(?:if|elif)\s+"([^"]+)"\s+in\s+dataset_name:\s*\n\s*epoch_size\s*=\s*(\d+)', src)
code_epochs = {k:int(v) for k,v in pairs}
# Paper Table 5 epochs (read from paper_text.txt) -- high_dim+large subset (first 20 rows)
paper = {
 "census":5,"backdoor":200,"campaign":50,"mnist":500,"speech":500,"optdigits":2000,
 "spambase":5000,"musk":5,"internetads":50,"donors":30,"http":100,"cover":10,"fraud":75,
 "skin":110,"celeba":2,"smtp":2,"aloi":100,"shuttle":200,"magic.gamma":10,"mammography":20,
}
out=[f"parsed {len(code_epochs)} hardcoded dataset epochs from FMAD/functions.py"]
mism=[]
for k,v in paper.items():
    cv = code_epochs.get(k)
    ok = (cv==v)
    if not ok: mism.append((k,v,cv))
    out.append(f"  {k:14s} paper={v:5d} code={cv} {'OK' if ok else 'MISMATCH'}")
out.append(f"MISMATCHES vs Table5(subset): {mism if mism else 'NONE'}")
out.append("Note: no CSM / unsupervised-epoch-selection code found in repo (grep returned only comment hits).")
txt="\n".join(out); print(txt)
open(os.path.join(os.path.dirname(__file__),"out","check_epochs.txt"),"w").write(txt+"\n")
