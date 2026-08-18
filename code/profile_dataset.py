"""Read-only profiling of the Food.com corpus.

Every number reported in Chapter 3 of the dissertation comes from this script.
Nothing here modifies the files in data/; the script only reads and summarises.

Run:  python code/profile_dataset.py
Out:  code/outputs/dataset_profile.json   machine-readable, for re-checking
      code/outputs/dataset_profile.md     human-readable summary
"""

import ast
import json
import os
import re
import warnings
from collections import Counter

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")
OUT = os.path.join(HERE, "outputs")
os.makedirs(OUT, exist_ok=True)

from allergen_lexicon import ALLERGENS, NEGATIVE_TAGS, build_matcher, classify, fires, masked_text

R = {}   # results dict written out as JSON


def section(msg):
    print("\n" + "=" * 70)
    print(msg)
    print("=" * 70)


# ----------------------------------------------------------------------------
# 1. Recipe corpus
# ----------------------------------------------------------------------------
section("1. Loading RAW_recipes.csv")
recipes = pd.read_csv(os.path.join(DATA, "RAW_recipes.csv"))
print(f"loaded {len(recipes):,} rows, {len(recipes.columns)} columns")

R["n_recipes_raw"] = int(len(recipes))
R["recipe_columns"] = list(recipes.columns)
R["n_recipes_missing_name"] = int(recipes["name"].isna().sum())
R["n_recipes_missing_description"] = int(recipes["description"].isna().sum())

# ----------------------------------------------------------------------------
# 2. Parse the stringified list columns
# ----------------------------------------------------------------------------
section("2. Parsing list-valued columns (nutrition / ingredients / tags)")


def safe_eval(s):
    try:
        return ast.literal_eval(s)
    except Exception:
        return []


nutrition = recipes["nutrition"].map(safe_eval)
bad_nutrition = int(sum(len(x) != 7 for x in nutrition))
print(f"rows whose nutrition tuple is not length 7: {bad_nutrition}")
R["n_bad_nutrition_tuple"] = bad_nutrition

NUTRI_COLS = ["calories", "total_fat_pdv", "sugar_pdv", "sodium_pdv",
              "protein_pdv", "sat_fat_pdv", "carbs_pdv"]
nut = pd.DataFrame(
    [x if len(x) == 7 else [np.nan] * 7 for x in nutrition],
    columns=NUTRI_COLS, index=recipes.index,
)
recipes = pd.concat([recipes, nut], axis=1)

recipes["ingredients_list"] = recipes["ingredients"].map(safe_eval)
recipes["tags_list"] = recipes["tags"].map(safe_eval)
print("parsed ingredients and tags")

# ----------------------------------------------------------------------------
# 3. Nutrition distributions  (feeds section 3.2.2 / 3.2.3)
# ----------------------------------------------------------------------------
section("3. Nutrition field distributions")
qs = [0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99]
R["nutrition_quantiles"] = {}
for c in NUTRI_COLS:
    q = recipes[c].quantile(qs)
    R["nutrition_quantiles"][c] = {f"p{int(k*100)}": round(float(v), 2)
                                   for k, v in q.items()}
    print(f"{c:>16}  " + "  ".join(f"p{int(k*100)}={v:9.1f}" for k, v in q.items()))

cal = recipes["calories"]
R["n_calories_zero"] = int((cal == 0).sum())
R["n_calories_over_5000"] = int((cal > 5000).sum())
R["n_calories_over_2000"] = int((cal > 2000).sum())
R["calories_max"] = round(float(cal.max()), 1)
R["calories_mean"] = round(float(cal.mean()), 1)
R["calories_median"] = round(float(cal.median()), 1)
print(f"\ncalories == 0        : {R['n_calories_zero']:,}")
print(f"calories >  2000     : {R['n_calories_over_2000']:,}")
print(f"calories >  5000     : {R['n_calories_over_5000']:,}")
print(f"calories max         : {R['calories_max']:,}")

# ----------------------------------------------------------------------------
# 4. minutes / n_ingredients / n_steps  (feeds section 3.2.2)
# ----------------------------------------------------------------------------
section("4. Preparation time and recipe complexity")
mins = recipes["minutes"]
R["minutes_quantiles"] = {f"p{int(k*100)}": round(float(v), 1)
                          for k, v in mins.quantile(qs).items()}
R["n_minutes_zero"] = int((mins == 0).sum())
R["n_minutes_over_1440"] = int((mins > 1440).sum())
R["minutes_max"] = int(mins.max())
print("minutes  " + "  ".join(f"p{int(k*100)}={v:.0f}"
                              for k, v in mins.quantile(qs).items()))
print(f"minutes == 0     : {R['n_minutes_zero']:,}")
print(f"minutes > 1440   : {R['n_minutes_over_1440']:,}")
print(f"minutes max      : {R['minutes_max']:,}")

ning = recipes["n_ingredients"]
R["n_ingredients_quantiles"] = {f"p{int(k*100)}": round(float(v), 1)
                                for k, v in ning.quantile(qs).items()}
R["n_ingredients_lt_2"] = int((ning < 2).sum())
R["n_ingredients_mean"] = round(float(ning.mean()), 2)
R["n_steps_mean"] = round(float(recipes["n_steps"].mean()), 2)
print(f"n_ingredients mean {R['n_ingredients_mean']}, <2 ingredients: "
      f"{R['n_ingredients_lt_2']:,}")

# ----------------------------------------------------------------------------
# 5. Tag coverage: dietary tags and meal-slot tags  (feeds 3.2.4 and 3.6)
# ----------------------------------------------------------------------------
section("5. Tag coverage")
tag_counter = Counter()
for tl in recipes["tags_list"]:
    tag_counter.update(tl)
R["n_distinct_tags"] = len(tag_counter)
R["top_30_tags"] = [[t, int(c)] for t, c in tag_counter.most_common(30)]
print(f"distinct tags: {len(tag_counter):,}")
print("top 15:", ", ".join(f"{t}({c:,})" for t, c in tag_counter.most_common(15)))

DIET_TAGS = ["vegetarian", "vegan", "dairy-free", "gluten-free", "egg-free",
             "nut-free", "low-sodium", "low-cholesterol", "low-carb",
             "low-calorie", "low-fat", "diabetic", "kosher", "healthy"]
R["dietary_tag_counts"] = {t: int(tag_counter.get(t, 0)) for t in DIET_TAGS}
print("\ndietary tags:")
for t in DIET_TAGS:
    n = tag_counter.get(t, 0)
    print(f"  {t:<18} {n:>8,}  ({100*n/len(recipes):5.2f}%)")

# Meal-slot assignment: THE key feasibility question for the weekly planner.
MEAL_SLOT_TAGS = {
    "breakfast": ["breakfast", "brunch", "breakfast-eggs", "oatmeal", "cereals-and-grains"],
    "lunch": ["lunch", "sandwiches", "salads", "soups-stews", "brown-bag",
              "lunch-snacks", "wraps"],
    "dinner": ["main-dish", "dinner-party", "meat", "poultry", "seafood",
               "pasta-rice-and-grains", "casseroles", "one-dish-meal", "roast-beef"],
}
EXCLUDE_TAGS = ["desserts", "beverages", "cocktails", "condiments-etc",
                "sauces", "dips", "salad-dressings", "spreads", "jams-and-preserves"]

slot_flags = {}
tagsets = recipes["tags_list"].map(set)
for slot, tl in MEAL_SLOT_TAGS.items():
    s = set(tl)
    slot_flags[slot] = tagsets.map(lambda x, s=s: len(x & s) > 0)
excl = tagsets.map(lambda x, s=set(EXCLUDE_TAGS): len(x & s) > 0)

any_slot = slot_flags["breakfast"] | slot_flags["lunch"] | slot_flags["dinner"]
R["meal_slot_coverage"] = {
    slot: int(f.sum()) for slot, f in slot_flags.items()
}
R["n_any_meal_slot"] = int(any_slot.sum())
R["pct_any_meal_slot"] = round(100 * float(any_slot.mean()), 2)
R["n_excluded_by_course_tag"] = int(excl.sum())
R["n_slot_assignable_after_exclusion"] = int((any_slot & ~excl).sum())
R["pct_slot_assignable_after_exclusion"] = round(
    100 * float((any_slot & ~excl).mean()), 2)

print("\nmeal-slot assignability (the weekly planner needs this):")
for slot, n in R["meal_slot_coverage"].items():
    print(f"  {slot:<12} {n:>8,}  ({100*n/len(recipes):5.2f}%)")
print(f"  {'ANY slot':<12} {R['n_any_meal_slot']:>8,}  "
      f"({R['pct_any_meal_slot']}%)")
print(f"  excluded as dessert/drink/condiment: "
      f"{R['n_excluded_by_course_tag']:,}")
print(f"  ==> assignable after exclusion: "
      f"{R['n_slot_assignable_after_exclusion']:,} "
      f"({R['pct_slot_assignable_after_exclusion']}%)")

# ----------------------------------------------------------------------------
# 6. Ingredient normalisation coverage  (decides the fail-closed threshold)
# ----------------------------------------------------------------------------
section("6. Ingredient normalisation via ingr_map.pkl")
ingr_map = pd.read_pickle(os.path.join(DATA, "ingr_map.pkl"))
raw_set = set(ingr_map["raw_ingr"].str.lower())
canon_set = set(ingr_map["replaced"].str.lower())
known = raw_set | canon_set
R["ingr_map_rows"] = int(len(ingr_map))
R["ingr_map_n_raw"] = int(len(raw_set))
R["ingr_map_n_canonical"] = int(len(canon_set))
print(f"ingr_map: {len(ingr_map):,} rows, {len(raw_set):,} raw forms, "
      f"{len(canon_set):,} canonical ingredients")

all_ingr = Counter()
for il in recipes["ingredients_list"]:
    all_ingr.update(i.lower().strip() for i in il)
R["n_distinct_ingredient_strings"] = len(all_ingr)
matched = {i: c for i, c in all_ingr.items() if i in known}
R["n_distinct_ingredients_matched"] = len(matched)
R["pct_distinct_ingredients_matched"] = round(
    100 * len(matched) / len(all_ingr), 2)

total_occ = sum(all_ingr.values())
matched_occ = sum(matched.values())
R["pct_ingredient_occurrences_matched"] = round(100 * matched_occ / total_occ, 2)
print(f"distinct ingredient strings in corpus : {len(all_ingr):,}")
print(f"  matched to ingr_map                 : {len(matched):,} "
      f"({R['pct_distinct_ingredients_matched']}%)")
print(f"  by occurrence (token-weighted)      : "
      f"{R['pct_ingredient_occurrences_matched']}%")

# how many RECIPES contain at least one unmappable ingredient
has_unknown = recipes["ingredients_list"].map(
    lambda il: any(i.lower().strip() not in known for i in il))
R["n_recipes_with_unmappable_ingredient"] = int(has_unknown.sum())
R["pct_recipes_with_unmappable_ingredient"] = round(
    100 * float(has_unknown.mean()), 2)
print(f"\nrecipes containing >=1 unmappable ingredient: "
      f"{R['n_recipes_with_unmappable_ingredient']:,} "
      f"({R['pct_recipes_with_unmappable_ingredient']}%)")
print("  ^^ this decides how strict fail-closed can afford to be")
R["top_20_unmatched_ingredients"] = [
    [i, int(c)] for i, c in
    sorted(((i, c) for i, c in all_ingr.items() if i not in known),
           key=lambda x: -x[1])[:20]]
print("  most common unmatched:",
      ", ".join(f"{i}({c:,})" for i, c in R["top_20_unmatched_ingredients"][:8]))

# ----------------------------------------------------------------------------
# 7. Allergen rule coverage  (feeds 3.2.4 and Table 3.4)
# ----------------------------------------------------------------------------
section("7. Allergen lexicon hit rates (14 EU classes)")
matcher = build_matcher()
ingr_text = recipes["ingredients_list"].map(lambda il: " | ".join(il).lower())

allergen_hits = {}
layer_breakdown = {}
for cls in ALLERGENS:
    terms = matcher[cls]
    fired_layer = ingr_text.map(
        lambda t, terms=terms, c=cls: next(
            (lay for term, lay in terms if term in masked_text(t, c)), None))
    n = int(fired_layer.notna().sum())
    allergen_hits[cls] = n
    layer_breakdown[cls] = {
        lay: int((fired_layer == lay).sum()) for lay in ("direct", "derived", "composite")}
    print(f"  {cls:<14} {n:>8,} ({100*n/len(recipes):5.2f}%)   "
          f"direct={layer_breakdown[cls]['direct']:>7,} "
          f"derived={layer_breakdown[cls]['derived']:>6,} "
          f"composite={layer_breakdown[cls]['composite']:>7,}")

R["allergen_hits"] = allergen_hits
R["allergen_layer_breakdown"] = layer_breakdown

n_free = int((~pd.DataFrame(
    {c: ingr_text.map(lambda t, c=c: fires(t, c, matcher))
     for c in ALLERGENS}).any(axis=1)).sum())
R["n_recipes_no_allergen_flag"] = n_free
R["pct_recipes_no_allergen_flag"] = round(100 * n_free / len(recipes), 2)
print(f"\nrecipes flagged for NO allergen class: {n_free:,} "
      f"({R['pct_recipes_no_allergen_flag']}%)")

# Contradiction check: rule says "contains", user tag says "free of"
section("7b. Rule-vs-tag contradictions (corroboration signal)")
contradictions = {}
for cls, negtags in NEGATIVE_TAGS.items():
    terms = matcher[cls]
    rule_says_contains = ingr_text.map(lambda t, c=cls: fires(t, c, matcher))
    tag_says_free = tagsets.map(lambda x, s=set(negtags): len(x & s) > 0)
    n = int((rule_says_contains & tag_says_free).sum())
    contradictions[cls] = {"n_conflict": n,
                           "n_tag_says_free": int(tag_says_free.sum())}
    print(f"  {cls:<12} tag says free: {int(tag_says_free.sum()):>7,}   "
          f"but rule fires: {n:>7,}")
R["rule_tag_contradictions"] = contradictions

# ----------------------------------------------------------------------------
# 8. Cleaning rules applied  (feeds 3.2.2 -- the final corpus size)
# ----------------------------------------------------------------------------
section("8. Applying the cleaning rules")
rules = {
    "missing name": recipes["name"].isna(),
    "nutrition tuple malformed": recipes["calories"].isna(),
    "calories == 0": recipes["calories"] == 0,
    "calories > 2000": recipes["calories"] > 2000,
    "minutes == 0": recipes["minutes"] == 0,
    "minutes > 1440 (24h)": recipes["minutes"] > 1440,
    "fewer than 2 ingredients": recipes["n_ingredients"] < 2,
    "no steps": recipes["n_steps"] < 1,
    "not assignable to a meal slot": ~(any_slot & ~excl),
}
drop = pd.Series(False, index=recipes.index)
R["cleaning_rules"] = {}
for name, mask in rules.items():
    mask = mask.fillna(True)
    new = int((mask & ~drop).sum())
    R["cleaning_rules"][name] = {"n_matched": int(mask.sum()),
                                 "n_newly_dropped": new}
    print(f"  {name:<32} matches {int(mask.sum()):>8,}   "
          f"newly drops {new:>8,}")
    drop = drop | mask

kept = int((~drop).sum())
R["n_recipes_after_cleaning"] = kept
R["pct_recipes_retained"] = round(100 * kept / len(recipes), 2)
print(f"\n  RETAINED: {kept:,} of {len(recipes):,} "
      f"({R['pct_recipes_retained']}%)")

clean = recipes.loc[~drop]
R["clean_calories_mean"] = round(float(clean["calories"].mean()), 1)
R["clean_calories_median"] = round(float(clean["calories"].median()), 1)
R["clean_minutes_median"] = round(float(clean["minutes"].median()), 1)
R["clean_meal_slot_counts"] = {
    slot: int((slot_flags[slot] & ~drop).sum()) for slot in MEAL_SLOT_TAGS}
print("  meal slots in the cleaned corpus:", R["clean_meal_slot_counts"])

# ----------------------------------------------------------------------------
# 9. Interactions  (feeds 3.4.2 sparsity and 3.4.3 switching threshold)
# ----------------------------------------------------------------------------
section("9. Loading RAW_interactions.csv (ratings only)")
inter = pd.read_csv(os.path.join(DATA, "RAW_interactions.csv"),
                    usecols=["user_id", "recipe_id", "rating"])
print(f"loaded {len(inter):,} interactions")
R["n_interactions_raw"] = int(len(inter))
R["n_users_raw"] = int(inter["user_id"].nunique())
R["n_recipes_rated_raw"] = int(inter["recipe_id"].nunique())

R["rating_distribution"] = {str(int(k)): int(v) for k, v in
                            inter["rating"].value_counts().sort_index().items()}
R["rating_mean"] = round(float(inter["rating"].mean()), 3)
R["pct_rating_5"] = round(100 * float((inter["rating"] == 5).mean()), 2)
R["pct_rating_0"] = round(100 * float((inter["rating"] == 0).mean()), 2)
print(f"users {R['n_users_raw']:,}, rated recipes {R['n_recipes_rated_raw']:,}")
print(f"rating distribution: {R['rating_distribution']}")
print(f"mean rating {R['rating_mean']}, 5-star share {R['pct_rating_5']}%, "
      f"zero-rating share {R['pct_rating_0']}%")

density = len(inter) / (R["n_users_raw"] * R["n_recipes_rated_raw"])
R["matrix_density_pct"] = round(100 * density, 6)
R["matrix_sparsity_pct"] = round(100 * (1 - density), 6)
print(f"matrix density {R['matrix_density_pct']}%  "
      f"(sparsity {R['matrix_sparsity_pct']}%)")

section("10. Interactions per user -- decides the switching threshold")
per_user = inter.groupby("user_id").size()
R["per_user_quantiles"] = {f"p{int(k*100)}": round(float(v), 1) for k, v in
                           per_user.quantile([0.1, 0.25, 0.5, 0.75, 0.9, 0.95, 0.99]).items()}
R["per_user_mean"] = round(float(per_user.mean()), 2)
R["per_user_median"] = int(per_user.median())
print("per-user interaction counts:")
for k, v in R["per_user_quantiles"].items():
    print(f"  {k:>4} = {v}")
print(f"  mean = {R['per_user_mean']}, median = {R['per_user_median']}")

R["users_with_at_least"] = {}
for n in [1, 2, 3, 5, 10, 15, 20, 25, 30, 50, 100]:
    c = int((per_user >= n).sum())
    R["users_with_at_least"][str(n)] = {
        "n_users": c, "pct": round(100 * c / len(per_user), 2)}
print("\nusers with >= N interactions:")
for n, d in R["users_with_at_least"].items():
    print(f"  >= {n:>3} : {d['n_users']:>9,}  ({d['pct']:>5.2f}%)")

per_item = inter.groupby("recipe_id").size()
R["per_item_median"] = int(per_item.median())
R["per_item_mean"] = round(float(per_item.mean()), 2)
R["pct_items_with_lt_5_ratings"] = round(
    100 * float((per_item < 5).mean()), 2)
print(f"\nper-recipe ratings: median {R['per_item_median']}, "
      f"mean {R['per_item_mean']}, "
      f"{R['pct_items_with_lt_5_ratings']}% of recipes have <5 ratings")

# interactions restricted to the cleaned corpus
clean_ids = set(clean["id"])
in_clean = inter[inter["recipe_id"].isin(clean_ids)]
R["n_interactions_on_clean_corpus"] = int(len(in_clean))
R["pct_interactions_retained"] = round(100 * len(in_clean) / len(inter), 2)
print(f"\ninteractions falling on the cleaned corpus: "
      f"{len(in_clean):,} ({R['pct_interactions_retained']}%)")

# ----------------------------------------------------------------------------
# 11. Write outputs
# ----------------------------------------------------------------------------
section("11. Writing outputs")
with open(os.path.join(OUT, "dataset_profile.json"), "w", encoding="utf-8") as f:
    json.dump(R, f, indent=2, ensure_ascii=False)
print("wrote outputs/dataset_profile.json")

lines = ["# Food.com dataset profile", "",
         "Generated by `code/profile_dataset.py`. Every figure quoted in "
         "Chapter 3 traces back to this file.", ""]
lines += ["## Corpus size", "",
          f"- raw recipes: **{R['n_recipes_raw']:,}**",
          f"- raw interactions: **{R['n_interactions_raw']:,}**",
          f"- distinct users: **{R['n_users_raw']:,}**",
          f"- distinct rated recipes: **{R['n_recipes_rated_raw']:,}**",
          f"- rating matrix density: **{R['matrix_density_pct']}%** "
          f"(sparsity {R['matrix_sparsity_pct']}%)", ""]
lines += ["## After cleaning", "",
          f"- retained recipes: **{R['n_recipes_after_cleaning']:,}** "
          f"({R['pct_recipes_retained']}% of raw)",
          f"- interactions on retained corpus: "
          f"**{R['n_interactions_on_clean_corpus']:,}** "
          f"({R['pct_interactions_retained']}%)", "",
          "| rule | matches | newly drops |", "|---|---:|---:|"]
for name, d in R["cleaning_rules"].items():
    lines.append(f"| {name} | {d['n_matched']:,} | {d['n_newly_dropped']:,} |")
lines += ["", "## Meal-slot assignability", "",
          f"- assignable to >=1 slot after removing desserts/drinks/condiments: "
          f"**{R['n_slot_assignable_after_exclusion']:,}** "
          f"({R['pct_slot_assignable_after_exclusion']}%)",
          f"- in cleaned corpus: {R['clean_meal_slot_counts']}", ""]
lines += ["## Ingredient normalisation", "",
          f"- distinct ingredient strings: {R['n_distinct_ingredient_strings']:,}",
          f"- matched to ingr_map: {R['pct_distinct_ingredients_matched']}% "
          f"of distinct forms, {R['pct_ingredient_occurrences_matched']}% of occurrences",
          f"- recipes with >=1 unmappable ingredient: "
          f"**{R['pct_recipes_with_unmappable_ingredient']}%**", ""]
lines += ["## Allergen rule hit rates", "",
          "| class | recipes flagged | % | direct | derived | composite |",
          "|---|---:|---:|---:|---:|---:|"]
for cls, n in R["allergen_hits"].items():
    b = R["allergen_layer_breakdown"][cls]
    lines.append(f"| {cls} | {n:,} | {100*n/R['n_recipes_raw']:.2f}% | "
                 f"{b['direct']:,} | {b['derived']:,} | {b['composite']:,} |")
lines += ["", "## Interactions per user", "",
          f"- median {R['per_user_median']}, mean {R['per_user_mean']}", "",
          "| >= N interactions | users | % |", "|---:|---:|---:|"]
for n, d in R["users_with_at_least"].items():
    lines.append(f"| {n} | {d['n_users']:,} | {d['pct']}% |")
lines.append("")

with open(os.path.join(OUT, "dataset_profile.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("wrote outputs/dataset_profile.md")
print("\nDONE")
