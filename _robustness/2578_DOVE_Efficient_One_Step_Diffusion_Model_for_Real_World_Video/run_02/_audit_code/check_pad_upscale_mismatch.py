#!/usr/bin/env python3
"""Shows that inference_script.py removes pad_h*4 / pad_w*4 from the SR output
regardless of args.upscale, while the SR padding region is actually pad_h*upscale.

Supports finding: pad-removal-hardcoded-x4. For --upscale 1 (used by RealVSR and
MVSR4x in inference.sh) with a non-multiple-of-16 input dim, this over-crops by
3*pad pixels. Pure arithmetic; no repo execution.
"""
import json, os

def sr_pad_region(H, W, upscale):
    pad_h = (16 - H % 16) % 16   # LR pixels padded (line 228)
    pad_w = (16 - W % 16) % 16   # LR pixels padded (line 229)
    # SR output padding region after interpolate by `upscale` (line 672)
    sr_pad_h = pad_h * upscale
    sr_pad_w = pad_w * upscale
    # what the code removes (line 731): pad_h*4, pad_w*4
    removed_h = pad_h * 4
    removed_w = pad_w * 4
    return {
        "H": H, "W": W, "upscale": upscale,
        "lr_pad_h": pad_h, "lr_pad_w": pad_w,
        "sr_pad_region_h": sr_pad_h, "sr_pad_region_w": sr_pad_w,
        "code_removes_h": removed_h, "code_removes_w": removed_w,
        "over_crop_h": removed_h - sr_pad_h, "over_crop_w": removed_w - sr_pad_w,
        "correct": (removed_h == sr_pad_h and removed_w == sr_pad_w),
    }

cases = [
    sr_pad_region(1080, 1920, 4),  # multiple of 16 in W only; default upscale, fine
    sr_pad_region(540, 960, 4),    # default upscale path
    sr_pad_region(1024, 436, 1),   # RealVSR-like, upscale=1, W not multiple of 16
    sr_pad_region(720, 1276, 1),   # MVSR4x-like, upscale=1, W not multiple of 16
    sr_pad_region(1024, 512, 1),   # both multiples of 16 -> no pad -> harmless
]
result = {
    "cases": cases,
    "n_overcrop_when_upscale1": sum(
        1 for c in cases if c["upscale"] == 1 and (c["over_crop_h"] > 0 or c["over_crop_w"] > 0)
    ),
    "note": "Bug only manifests when upscale != 4 AND an input dim is not a multiple of 16.",
}
outp = os.path.join(os.path.dirname(__file__), "out", "pad_upscale_mismatch.json")
with open(outp, "w") as fh:
    json.dump(result, fh, indent=2)
print(json.dumps(result, indent=2))
