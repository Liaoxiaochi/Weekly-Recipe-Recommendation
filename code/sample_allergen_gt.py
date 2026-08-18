"""Draw a stratified sample for manual allergen labelling.

Recall is the quantity that matters for safety, so the sample must contain
recipes the rules called NEGATIVE -- those are where false negatives hide.
Sampling only flagged recipes would measure precision and say nothing about
what the lexicon misses.

Strata are formed on the rule outcome for the four highest-traffic classes
(gluten, milk, eggs, fish), so that each has both flagged and unflagged
recipes in the sample.

Run:  python code/sample_allergen_gt.py
Out:  code/outputs/allergen_sample.csv        recipes to label
      code/outputs/allergen_sample_rules.csv  what the rules predicted
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
os.makedirs(OUT, exist_ok=True)

from allergen_lexicon import ALLERGENS, build_matcher, fires

SEED = 20260814
N_PER_STRATUM = 20
FOCUS = ["gluten", "milk", "eggs", "fish"]

rng = np.random.default_rng(SEED)

print("loading corpus ...")
r = pd.read_csv(os.path.join(DATA, "RAW_recipes.csv"),
                usecols=["id", "name", "ingredients", "tags"])
r["ing"] = r["ingredients"].map(ast.literal_eval)
r["ing_text"] = r["ing"].map(lambda x: " | ".join(x).lower())
r = r[r["ing"].map(len) >= 2].reset_index(drop=True)
print(f"  {len(r):,} recipes")

matcher = build_matcher()
pred = {}
for cls, terms in matcher.items():
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
out.to_csv(os.path.join(OUT, "allergen_sample.csv"), index=False)

rules = pred.loc[sample["idx"]].copy()
rules.insert(0, "recipe_id", r.loc[sample["idx"], "id"].values)
rules.to_csv(os.path.join(OUT, "allergen_sample_rules.csv"), index=False)
print("wrote outputs/allergen_sample.csv and allergen_sample_rules.csv")

print("\n" + "=" * 78)
print("RECIPES TO LABEL")
print("=" * 78)
for n, (_, row) in enumerate(out.iterrows(), 1):
    ings = ", ".join(ast.literal_eval(row["ingredients"]))
    print(f"\n[{n:>3}] id={row['id']}  ({row['stratum']})")
    print(f"      {row['name'].strip()}")
    print(f"      {ings}")
