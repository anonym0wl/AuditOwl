"""Checks that determine_FMAD_hyperparameters() returns defined values for every
dataset in AggregateResults.DATASETS, and that no dataset name falls through the
if/elif chain leaving epoch_size/batch_size undefined. Supports finding
'epoch-selection-code-missing' and 'tccm-hyperparam-unbound-fallthrough'.
Read-only; writes a CSV to out/."""
import re, os, csv

REPO = os.path.join(os.path.dirname(__file__), "..", "code", "ZhongLIFR__TCCM-NIPS")
REPO = os.path.abspath(REPO)

# The 47 datasets used (from AggregateResults.DATASETS)
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

# Extract the keywords used in the if/elif chain of determine_FMAD_hyperparameters
funcs_path = os.path.join(REPO, "FMAD", "functions.py")
src = open(funcs_path).read()
# isolate the function body
start = src.index("def determine_FMAD_hyperparameters")
body = src[start:]
keywords = re.findall(r'"([^"]+)"\s+in\s+dataset_name', body)

rows = []
unmatched = []
for ds in all_ds:
    name = ds.lower()
    matched = [kw for kw in keywords if kw in name]
    status = "MATCHED" if matched else "FALLTHROUGH->UnboundLocalError"
    if not matched:
        unmatched.append(ds)
    rows.append((ds, ";".join(matched) if matched else "(none)", status))

out_csv = os.path.join(os.path.dirname(__file__), "out", "hyperparam_coverage.csv")
with open(out_csv, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["dataset", "matched_keywords", "status"])
    w.writerows(rows)

print(f"Total datasets: {len(all_ds)}")
print(f"Keywords in if/elif chain: {len(keywords)}")
print(f"Datasets that fall through (=> UnboundLocalError): {len(unmatched)}")
for u in unmatched:
    print("  FALLTHROUGH:", u)
print(f"Wrote {out_csv}")
