"""Checks that every dataset referenced by AggregateResults.DATASETS exists as an
.npz file under datasets/<category>/. Supports any 'missing dataset' finding.
Read-only; writes CSV to out/."""
import os, csv

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "code", "ZhongLIFR__TCCM-NIPS"))
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

rows = []
present = 0
missing = 0
for cat, names in DATASETS.items():
    for nm in names:
        path = os.path.join(REPO, "datasets", cat, nm + ".npz")
        ok = os.path.isfile(path)
        rows.append((cat, nm, "present" if ok else "MISSING"))
        if ok: present += 1
        else: missing += 1

out_csv = os.path.join(os.path.dirname(__file__), "out", "dataset_files.csv")
with open(out_csv, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["category", "dataset", "status"])
    w.writerows(rows)

print(f"Datasets present: {present}, missing: {missing}, total: {present+missing}")
for cat, nm, st in rows:
    if st == "MISSING":
        print(f"  MISSING: {cat}/{nm}")
print(f"Wrote {out_csv}")
