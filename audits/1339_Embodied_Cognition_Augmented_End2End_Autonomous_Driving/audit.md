# Code-repository audit — Paper 1339: "Embodied Cognition Augmented End2End Autonomous Driving" (E³AD)

> **RE-AUDIT (2026-06-03).** The original audit cloned only the repo's **default
> `main` branch**, shallow, which holds a single `README.md` reading *"code coming
> soon"*, and concluded **"no code released"**. That conclusion was **false**: the
> implementation lives on the repo's **non-default `E-VAD` branch**
> (`github.com/AIR-DISCOVER/E-cubed-AD`, commit `ad78ad0`, public since **2026-01-29**,
> 565 files), which the original shallow single-branch clone never fetched. This file
> re-audits the paper against that branch (`code/AIR-DISCOVER__E-cubed-AD__E-VAD/`).
> The four "no code / no training / no eval / no ablation" findings are **false** (the
> code exists) and have been **removed** from the findings set; the genuine
> reproducibility gaps and code-vs-paper mismatches the real code *does* exhibit are
> filed below.

## 1. Summary

E³AD contrastively aligns a Video Swin encoder with a large EEG model (LaBraM) to
distil "human driving cognition" into an end-to-end (E2E) planner, then freezes that
"Driving-Thinking" model and injects its feature into the planning transformer. The
paper reports open-loop nuScenes results (Table 1) across five E2E baselines (UniAD,
VAD-Base, VAD-Tiny, GenAD, LAW), closed-loop Bench2Drive/CARLA results (Table 2), and
ablations over three cognition-injection frameworks (Table 4) and several
hyperparameters (Tables 3, A.2–A.4).

**The released `E-VAD` branch is a real, substantial codebase** (364 `.py` files plus
vendored CUDA ops and a torchvision fork). It contains a genuine two-part pipeline:

- **Stage-1** (`projects/eeg_vedio/`): a symmetric InfoNCE contrastive model
  (`src/models/contrastive_model.py`) aligning a Swin3D-B video encoder
  (`video_encoder/video_encoder.py`) with a faithfully-ported LaBraM transformer
  (`eeg_encoder/labram.py`); training loops in `src/run_model/train.py` and
  `train_ddp.py`.
- **Stage-2** (`projects/mmdet3d_plugin/EAD/`): `EAD`, a fork of **VAD-Base**, which
  loads the frozen Driving-Thinking video encoder (`EAD.py:100-112`) and cross-attends
  the planning feature against the brain feature in an `eeg_decoder`
  (`EAD_head.py:779-797`); trained via `tools/train.py` + `configs/EAD/EAD_based_pretrain.py`.

The **contrastive loss math and the encoder architectures faithfully match §3.2** and
should not be flagged. What the code does *not* support are several of the paper's
headline claims — see §3.

**What I did.** I cloned the `E-VAD` branch, mapped it against the paper's claimed
components, and fanned out three subsystem audits (stage-1/data, stage-2/injection,
eval/repro), each cross-checking the seven original findings and surfacing new ones.
I then independently re-verified every load-bearing claim by reading file:line in the
code and `paper_text.txt` (the LaBraM `assert config is not None` crash, the
config-vs-paper hyperparameters, the learnable-temperature line, the single shipped
config, and the missing `RealCarDataset`). Findings carry that file:line evidence.

## 2. Traceability table (Rule G)

| Paper artefact | Repo location | Status |
|---|---|---|
| Stage-1 contrastive alignment (InfoNCE, video↔EEG) | `eeg_vedio/src/models/contrastive_model.py:71-86` | PRESENT, matches §3.2 |
| LaBraM EEG encoder | `eeg_vedio/src/models/eeg_encoder/labram.py` | PRESENT (instantiation asserts — F08) |
| Video Swin encoder + projection head | `eeg_vedio/src/models/video_encoder/video_encoder.py` | PRESENT, matches §3.2 |
| Stage-1 training loop | `eeg_vedio/src/run_model/train.py`, `train_ddp.py` | PRESENT but **non-runnable** (F08) |
| Stage-1 schedule (batch 16 / 120 ep / lr 2e-5) | `cfgs/train_config.yaml:12-14` | MISMATCH: 30 ep / lr 1e-4 (F09) |
| Learnable log-temperature β | `contrastive_model.py:21` | MISMATCH: fixed 0.1 (F10) |
| Stage-2 planner + cognition injection (Framework 3) | `mmdet3d_plugin/EAD/EAD.py`, `EAD_head.py:779-797` | PRESENT, matches Eq. 9 |
| Stage-2 training | `tools/train.py` + `configs/EAD/EAD_based_pretrain.py` | PRESENT |
| Open-loop nuScenes L2 + collision (Table 1) | `EAD/planner/metric_stp3.py:166-308` | PRESENT |
| Baselines UniAD / VAD-Tiny / GenAD / LAW (Table 1) | (none) | MISSING — only VAD-Base/EAD (F06) |
| Closed-loop Bench2Drive/CARLA (Table 2) | (none) | MISSING — no harness (F05) |
| Injection Frameworks 1 & 2 (Table 4) | (none) | MISSING — only Framework 3 (F07) |
| Ablation switches (contrastive on/off; expert/novice/mixed) | (none) | MISSING — no selector |
| Paired EEG–video dataset | `RealCarDataset` import only | MISSING — class & data absent (F01) |
| EEG preprocessing pipeline | (none) | MISSING (F02) |
| Pretrained / E³AD checkpoints | dangling `ckpts/*` paths | MISSING (F03) |
| Dependency spec | `requirements.txt` | PRESENT |
| README run commands / results table | `README.md` (14 bytes) | MISSING (F03) |

## 3. Findings

Nine findings constitute the audit, all verified against the `E-VAD` code. The four
original "absence" findings asserted that *no code exists*; the code does exist, so
they are **false and have been removed** from `findings.json` / `findings_verified.json`
(each refutation is preserved in `_build_reaudit.py` for the record).

**Kept — still valid (carried over):**
- **F01 `eeg-video-dataset-absent` (missing, high)** — the paired EEG–video dataset
  is absent and unfetchable; the loader class `RealCarDataset` itself does not exist
  (imported at `train.py:18`, `train_ddp.py:23`), configs point at private absolute
  paths (`cfgs/train_config.yaml:2-4`).
- **F02 `eeg-preprocessing-absent` (missing, medium)** — no code for the App. A
  EEG preprocessing (re-ref M1/M2, 0.1–50 Hz band-pass, ICA, epoching); the encoder
  consumes pre-baked tensors.
- **F03 `weights-and-deps-absent` → narrowed (missing, medium)** — dependencies are
  now present (`requirements.txt`), so this was narrowed to: no checkpoints
  (every `ckpts/*` path dangles, e.g. `EAD.py:105`) and a 14-byte README with no run
  instructions.

**New — only discoverable now that an implementation exists:**
- **F05 `closed-loop-carla-harness-absent` (missing, high)** — Table 2's closed-loop
  DS/SR over 220 CARLA routes has no harness; a repo-wide grep for
  `carla|bench2drive|leaderboard|driving_score|success_rate|infraction` finds only a
  stray dep line (`requirements.txt:21`) and `vision15/` torchvision noise.
- **F06 `multi-baseline-claim-unsupported` (difference, high)** — Table 1 claims five
  E2E baselines; the code ships exactly one planner, `EAD` (a VAD-Base fork,
  `EAD.py:54-56`), with a single config; no UniAD/VAD-Tiny/GenAD/LAW code exists.
- **F07 `injection-frameworks-1-2-absent` (missing, high)** — Table 4 compares three
  injection frameworks; only Framework 3 (the `eeg_decoder`, `EAD_head.py:779-797`)
  is implemented; Frameworks 1 & 2 (AttnGate/TokenLearner; ego-query interaction)
  have no code and there is no selector.
- **F08 `stage1-training-not-runnable` (bug, high)** — the Driving-Thinking model
  (the paper's central novelty) cannot be trained as shipped: missing `RealCarDataset`
  module, a broken `main.py:4` entry import (`training.train`), and
  `contrastive_model.py:22` calling `timm.create_model(..., pretrained=True)` without
  the `config=` kwarg that `labram.py:539` asserts on.
- **F09 `stage1-hyperparams-mismatch` (difference, medium)** — config is 30 epochs /
  lr 1e-4 (`train_config.yaml:12,14`) vs the paper's 120 epochs / lr 2e-5
  (`paper_text.txt:439`); only batch size 16 agrees.
- **F10 `learnable-temperature-not-implemented` (difference, medium)** — §3.2
  (`paper_text.txt:261`) specifies a *learnable* log-temperature β; the code uses a
  fixed constant 0.1 (`contrastive_model.py:21`) with no learnable parameter.

**Removed — original "no code" findings were false (code exists on `E-VAD`):**
`repo-only-readme-placeholder`, `training-code-absent`,
`eval-code-absent-openloop-closedloop` (open-loop eval *is* present), and
`ablation-code-absent` (Framework 3 *is* present) each asserted the code was absent;
it is not, so all four are removed from the findings set. Their valid residues
(closed-loop gap; Frameworks 1 & 2 gap) are re-filed precisely as F05 and F07.

See `findings_verified.json` for the full per-finding claim / concern / evidence /
verification reason, and `_build_reaudit.py` for the script that emits it.
