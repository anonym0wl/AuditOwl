"""For each dataset, report which keyword the if/elif chain matches FIRST (Python
takes the first true branch). Detects mis-routing where a substring keyword
captures a dataset intended for a later branch (e.g. 'cardio' vs
'cardiotocography', 'musk' vs 'musk' in high_dim/contamination). Read-only."""
import re, os, csv

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "code", "ZhongLIFR__TCCM-NIPS"))
src = open(os.path.join(REPO, "FMAD", "functions.py")).read()
start = src.index("def determine_FMAD_hyperparameters")
body = src[start:]
# keywords in order of appearance (= elif order)
keywords_in_order = re.findall(r'"([^"]+)"\s+in\s+dataset_name', body)
# epochs paired with each branch (in order)
epochs_in_order = [int(x) for x in re.findall(r'epoch_size\s*=\s*(\d+)', body)]

DATASETS = {
    "small": ["4_breastw", "14_glass", "15_Hepatitis", "18_Ionosphere", "21_Lymphography",
              "29_Pima", "37_Stamps", "39_vertebral", "42_WBC", "43_WDBC", "45_wine", "46_WPBC"],
    "medium": ["2_annthyroid","6_cardio","7_Cardiotocography","12_fault","19_landsat","20_letter",
               "27_PageBlocks","28_pendigits","30_satellite","31_satimage-2","38_thyroid","40_vowels",
               "41_Waveform","44_Wilt","47_yeast"],
    "high_dim": ['3_backdoor', '5_campaign', '9_census', '17_InternetAds',
                 '24_mnist', '25_musk', '26_optdigits', '35_SpamBase', '36_speech'],
    "large": ['1_ALOI', '8_celeba', '10_cover', '11_donors', '13_fraud', '16_http', '22_magic.gamma',
              '23_mammography', '32_shuttle', '33_skin', '34_smtp']
}
all_ds = [d for v in DATASETS.values() for d in v]

rows = []
for ds in all_ds:
    name = ds.lower()
    first_kw, first_ep = None, None
    for kw, ep in zip(keywords_in_order, epochs_in_order):
        if kw in name:
            first_kw, first_ep = kw, ep
            break
    rows.append((ds, first_kw, first_ep))

out_csv = os.path.join(os.path.dirname(__file__), "out", "first_match.csv")
with open(out_csv, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["dataset", "first_matched_keyword", "epochs_assigned"])
    w.writerows(rows)

# Report any dataset whose first-matched keyword differs from the dataset's own name token
print(f"{'dataset':22s} {'first_kw':18s} epochs")
for ds, kw, ep in rows:
    flag = ""
    token = ds.split("_", 1)[1].lower() if "_" in ds else ds.lower()
    if kw is not None and kw != token and token not in kw and kw not in token:
        flag = "  <-- keyword != dataset token"
    print(f"{ds:22s} {str(kw):18s} {str(ep):6s}{flag}")
print(f"Wrote {out_csv}")
