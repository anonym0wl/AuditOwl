"""Checks determine_FMAD_hyperparameters for substring-matching collisions.
The function dispatches on `if <key> in dataset_name.lower()` in order; an earlier
key that is a substring of a later dataset's name would mis-assign hyperparameters.
Supports finding: hparam-substring-dispatch. Read-only; imports the real function.
"""
import os, sys

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "code", "ZhongLIFR__TCCM-NIPS"))
sys.path.insert(0, REPO)
from FMAD.functions import determine_FMAD_hyperparameters  # noqa

# All 47 ADBench dataset filenames used (from AggregateResults.DATASETS), lowercased base name
datasets = [
 "4_breastw","14_glass","15_Hepatitis","18_Ionosphere","21_Lymphography","29_Pima",
 "37_Stamps","39_vertebral","42_WBC","43_WDBC","45_wine","46_WPBC",
 "2_annthyroid","6_cardio","7_Cardiotocography","12_fault","19_landsat","20_letter",
 "27_PageBlocks","28_pendigits","30_satellite","31_satimage-2","38_thyroid","40_vowels",
 "41_Waveform","44_Wilt","47_yeast",
 "3_backdoor","5_campaign","9_census","17_InternetAds","24_mnist","25_musk",
 "26_optdigits","35_SpamBase","36_speech",
 "1_ALOI","8_celeba","10_cover","11_donors","13_fraud","16_http","22_magic.gamma",
 "23_mammography","32_shuttle","33_skin","34_smtp",
]

# Ordered keys as they appear in the if/elif chain
keys_in_order = ["census","backdoor","campaign","mnist","speech","optdigits","spambase","musk",
 "internetads","donors","http","cover","fraud","skin","celeba","smtp","aloi","shuttle",
 "magic.gamma","mammography","annthyroid","pendigits","satellite","landsat","satimage-2",
 "pageblocks","wilt","thyroid","waveform","cardiotocography","fault","cardio","letter",
 "yeast","vowels","pima","breastw","wdbc","ionosphere","stamps","vertebral","wbc","glass",
 "wpbc","lymphography","wine","hepatitis"]

print(f"Number of dataset files: {len(datasets)}; number of dispatch keys: {len(keys_in_order)}")

# For each dataset, find which key the if/elif chain matches FIRST
def first_match(name_low):
    for k in keys_in_order:
        if k in name_low:
            return k
    return None

issues = []
no_match = []
for ds in datasets:
    low = ds.lower()
    matched = first_match(low)
    if matched is None:
        no_match.append(ds)
        continue
    # The 'intended' key is the one whose token equals the dataset's semantic name.
    # Flag if the first-matched key is NOT a clean match (i.e., an earlier key collided).
    # Heuristic: report all (dataset -> first matched key) for manual inspection,
    # and explicitly flag where matched key != the dataset's own trailing token.
    # Determine all keys that are substrings:
    all_subs = [k for k in keys_in_order if k in low]
    if len(all_subs) > 1:
        issues.append((ds, matched, all_subs))

print("\nDatasets that match NO key (would get UnboundLocalError / fall through):")
for ds in no_match:
    print("  ", ds)

print("\nDatasets where MULTIPLE keys are substrings (potential collision; first wins):")
for ds, matched, subs in issues:
    print(f"   {ds}: first='{matched}', all_substring_keys={subs}")

# Also actually call the function and report what it returns for the no_match ones
print("\nActual return of determine_FMAD_hyperparameters for no-match datasets:")
for ds in no_match:
    try:
        print("  ", ds, "->", determine_FMAD_hyperparameters(ds))
    except Exception as e:
        print("  ", ds, "-> EXCEPTION:", type(e).__name__, e)

out = os.path.join(os.path.dirname(__file__), "out", "hparam_collisions.txt")
with open(out, "w") as f:
    f.write(f"no_match={no_match}\n")
    f.write(f"multi_substring_issues={issues}\n")
print("\nwrote", out)
