"""Draw a SECOND, independent stratified sample for allergen labelling.

WHY A SECOND SAMPLE EXISTS.

The lexicon was revised using the errors found on the first sample of 160
recipes.  Its recall measured on that same sample is therefore an optimistic
estimate of itself: the rules were changed until those particular misses went
away, so a perfect score there says only that the repair was applied, not that
it generalises.  outputs/allergen_eval_v1_v2.md says so explicitly and quotes
the v1 figure as the honest one.

This script draws a fresh sample with a different seed, **excluding every
recipe in the first sample**, so the revised lexicon can be scored on data it
was not built from.  Section 4.2 of the dissertation promises exactly this
measurement, and without it that promise is unmet.

The stratification is the same as the first sample's and for the same reason:
recall is the quantity that matters for safety, and false negatives can only be
found among recipes the rules called NEGATIVE, so each class contributes both
flagged and unflagged recipes.

Run:  python code/sample_allergen_gt2.py
Out:  code/outputs/allergen_sample2.csv        recipes to label
      code/outputs/allergen_sample2_rules.csv  what the rules predicted
"""

import ast
import os
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")
OUT = os.path.join(HERE, "outputs")

from allergen_lexicon import build_matcher, fires  # noqa: E402

SEED = 20260817          # deliberately not the first sample's 20260814
N_PER_STRATUM = 13       # 13 x 8 strata = 104 recipes
FOCUS = ["gluten", "milk", "eggs", "fish"]

rng = np.random.default_rng(SEED)

print("loading corpus ...")
r = pd.read_csv(os.path.join(DATA, "RAW_recipes.csv"),
                usecols=["id", "name", "ingredients", "tags"])
r["ing"] = r["ingredients"].map(ast.literal_eval)
r["ing_text"] = r["ing"].map(lambda x: " | ".join(x).lower())
r = r[r["ing"].map(len) >= 2].reset_index(drop=True)
print(f"  {len(r):,} recipes")

# Exclude everything in the first sample.  This is the whole point of the
# exercise, so it is asserted rather than assumed.
first = pd.read_csv(os.path.join(OUT, "allergen_sample.csv"))
already = set(first["id"].astype(int))
print(f"  excluding {len(already)} recipes used in the first sample")
r = r[~r["id"].astype(int).isin(already)].reset_index(drop=True)
print(f"  {len(r):,} remain")

matcher = build_matcher()
pred = {}
for cls in FOCUS:
    pred[cls] = r["ing_text"].map(lambda t, c=cls: fires(t, c, matcher))
pred = pd.DataFrame(pred)

rows = []
for cls in FOCUS:
    for outcome in (True, False):
        pool = r.index[pred[cls] == outcome]
        take = rng.choice(pool, size=N_PER_STRATUM, replace=False)
        for i in take:
            rows.append({"stratum": f"{cls}_{'pos' if outcome else 'neg'}",
                         "idx": int(i)})

sample = pd.DataFrame(rows).drop_duplicates("idx").reset_index(drop=True)
print(f"\nsampled {len(sample)} distinct recipes "
      f"across {sample['stratum'].nunique()} strata")

out = r.loc[sample["idx"], ["id", "name", "ingredients"]].copy()
out.insert(0, "stratum", sample["stratum"].values)
assert not set(out["id"].astype(int)) & already, "overlap with the first sample"
out.to_csv(os.path.join(OUT, "allergen_sample2.csv"), index=False)

rules = pred.loc[sample["idx"]].copy()
rules.insert(0, "recipe_id", r.loc[sample["idx"], "id"].values)
rules.to_csv(os.path.join(OUT, "allergen_sample2_rules.csv"), index=False)
print("wrote outputs/allergen_sample2.csv and allergen_sample2_rules.csv")
print("zero overlap with the first sample: verified")

print("\n" + "=" * 78)
print("RECIPES TO LABEL")
print("=" * 78)
for n, (_, row) in enumerate(out.iterrows(), 1):
    ings = ", ".join(ast.literal_eval(row["ingredients"]))
    print(f"\n[{n:>3}] id={row['id']}  ({row['stratum']})")
    print(f"      {str(row['name']).strip()}")
    print(f"      {ings}")
