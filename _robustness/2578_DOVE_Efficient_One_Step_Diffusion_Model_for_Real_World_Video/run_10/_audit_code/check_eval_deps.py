"""Checks: the VQA/temporal-consistency metric scripts (eval_dover, eval_ewarp,
eval_vbench) reference modules/paths that do not exist in the repo, and pyiqa is
not pinned in requirements.txt. Supports findings eval-vqa-temporal-missing-deps
and pyiqa-missing-from-requirements. Read-only.
Output: out/eval_deps.txt
"""
import os

HERE = os.path.dirname(__file__)
REPO = os.path.join(HERE, "..", "code", "zhengchen1999__DOVE")
out_dir = os.path.join(HERE, "out"); os.makedirs(out_dir, exist_ok=True)

def exists(rel):
    return os.path.exists(os.path.join(REPO, rel))

checks = []
# eval_ewarp.py: chdir to finetune/scripts, then sys.path RAFT and chdir(original/RAFT)
checks.append(("finetune/scripts/RAFT dir (eval_ewarp sys.path + chdir target)", exists("finetune/scripts/RAFT")))
checks.append(("ewarp.py module anywhere in repo (eval_ewarp imports it)",
               any(f == "ewarp.py" for _, _, fs in os.walk(REPO) for f in fs)))
checks.append(("finetune/scripts/models/raft-things.pth (eval_ewarp default --model)",
               exists("finetune/scripts/models/raft-things.pth")))
checks.append(("finetune/utils/RAFT/raft-things.pth (actual checkpoint location)",
               exists("finetune/utils/RAFT/raft-things.pth")))
# eval_dover.py: from DOVER.evaluate_a_set_of_videos import evaluate_set
checks.append(("DOVER package dir in repo (eval_dover imports DOVER.*)", exists("DOVER")))
checks.append(("DOVER under finetune/scripts (cwd after chdir)", exists("finetune/scripts/DOVER")))
# eval_vbench.py: chdir to finetune/scripts/VBench, from evaluate import calculate_final
checks.append(("finetune/scripts/VBench dir (eval_vbench chdir target)", exists("finetune/scripts/VBench")))
# requirements
req = open(os.path.join(REPO, "requirements.txt")).read().lower()
checks.append(("pyiqa pinned/listed in requirements.txt (eval_metrics imports pyiqa)", "pyiqa" in req))

lines = [f"{'PRESENT' if ok else 'ABSENT ':8s} {desc}" for desc, ok in checks]
result = "\n".join(lines)
print(result)
with open(os.path.join(out_dir, "eval_deps.txt"), "w") as f:
    f.write(result + "\n")
