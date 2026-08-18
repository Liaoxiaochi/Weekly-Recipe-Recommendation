"""Data pipeline: raw Food.com export -> the corpus the planner ranks.

Implements Section 3.2 of the dissertation.  The six stages are

    1  load and parse the stringified list columns
    2  convert the nutrition tuple from percentages of a daily value to mass
    3  assign each recipe to one or more meal slots from its course tags
    4  apply the nine cleaning rules
    5  normalise ingredients through the ingredient map, recording the residue
    6  tag allergens with the three-layer lexicon, and derive the diet flags

THE COUNTS ARE A CONTRACT.  Chapter 3 states that the pipeline retains 128,403
recipes carrying 655,954 interactions, of which 19,919 are breakfasts, 40,779
lunches and 103,389 dinners.  Those figures were produced by profile_dataset.py
and are stored in outputs/dataset_profile.json.  This script reproduces them and
exits non-zero if it does not, so that a change to a cleaning rule cannot
silently put the code and the dissertation into disagreement.

profile_dataset.py is deliberately left untouched: it is the archival provenance
of the Chapter 3 numbers.  It cannot be imported, because it executes its whole
870 MB profiling run at module level, so the rules below are restated here and
the reconciliation at the end is what keeps the two in step.

Run:  python code/src/preprocessing.py
Out:  code/outputs/corpus.pkl         cleaned recipes, one row per recipe
      code/outputs/interactions.pkl   ratings falling on that corpus
"""

import ast
import json
import os
import pickle
import sys
import time

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
CODE = os.path.dirname(HERE)
DATA = os.path.join(CODE, "..", "data")
OUT = os.path.join(CODE, "outputs")

sys.path.insert(0, CODE)
from allergen_lexicon import ALLERGENS, EXEMPT, build_matcher  # noqa: E402

# ---------------------------------------------------------------------------
# Constants.  Sections 3.2.2, 3.2.3 and 3.6.1 of the dissertation.
# ---------------------------------------------------------------------------

# The seven-element nutrition tuple, in the order the corpus stores it.  The
# order was confirmed field by field against the nutrition panel Food.com
# publishes for recipe 61040, which is a member of this corpus (Figure 3.2).
NUTRI_COLS = ["calories", "total_fat_pdv", "sugar_pdv", "sodium_pdv",
              "protein_pdv", "sat_fat_pdv", "carbs_pdv"]

# Reference quantities used to turn a percentage of a daily value into a mass
# (Table 3.1).  These are the pre-2016 United States label values, consistent
# with the period over which the corpus was collected; the sugar figure of 25 g
# has no pre-2016 label equivalent and was recovered from the published panel
# and then corroborated across the corpus against total carbohydrate.
DAILY_VALUE = {
    "total_fat_pdv": ("fat_g", 65.0),
    "sugar_pdv": ("sugar_g", 25.0),
    "sodium_pdv": ("sodium_mg", 2400.0),
    "protein_pdv": ("protein_g", 50.0),
    "sat_fat_pdv": ("satfat_g", 20.0),
    "carbs_pdv": ("carbs_g", 300.0),
}

# Course tags mapped to meal slots (Section 3.6.1).  A recipe may satisfy more
# than one slot, so these are three independent flags rather than one label.
MEAL_SLOT_TAGS = {
    "breakfast": ["breakfast", "brunch", "breakfast-eggs", "oatmeal",
                  "cereals-and-grains"],
    "lunch": ["lunch", "sandwiches", "salads", "soups-stews", "brown-bag",
              "lunch-snacks", "wraps"],
    "dinner": ["main-dish", "dinner-party", "meat", "poultry", "seafood",
               "pasta-rice-and-grains", "casseroles", "one-dish-meal",
               "roast-beef"],
}

# Accompaniments rather than meals.  Excluded even when a slot tag also fires.
EXCLUDE_TAGS = ["desserts", "beverages", "cocktails", "condiments-etc",
                "sauces", "dips", "salad-dressings", "spreads",
                "jams-and-preserves"]

SLOTS = ("breakfast", "lunch", "dinner")

# Tags identifying an accompaniment: a dish served alongside a main rather than
# as one.  These recipes are drawn from those the meal-slot rule discards, and
# the pool is defined to be disjoint from the main corpus, so admitting them
# leaves the corpus figures of Section 3.2.2 untouched.
SIDE_TAGS = ["side-dishes", "vegetables", "greens", "potatoes", "rice", "beans"]

# Accompaniments a person would recognise at breakfast.  The side pool is
# dominated by vegetable dishes, and pairing a bowl of roasted vegetables with
# porridge is not a suggestion a user would act on, so the breakfast slot draws
# from this subset instead of the whole pool.
SIDE_BREAKFAST_TAGS = ["fruit", "eggs-dairy", "cheese", "potatoes"]

# Ingredients excluded under a halal regime.  The corpus carries no halal tag of
# any kind, so unlike the vegetarian and vegan regimes this one cannot be served
# by a tag whitelist and is approximated by an ingredient blacklist.  The
# approximation is stated as such in the interface and in Chapter 4: it screens
# for the ingredients most commonly at issue and is not a certification.
HALAL_EXCLUDED = [
    "pork", "bacon", "ham ", "gammon", "prosciutto", "pancetta", "chorizo",
    "salami", "pepperoni", "lard", "gelatin", "gelatine", "suet",
    "wine", "beer", "ale ", "lager", "rum", "vodka", "brandy", "sherry",
    "whisky", "whiskey", "bourbon", "liqueur", "kirsch", "marsala", "vermouth",
    "sake", "mirin", "champagne", "cognac", "amaretto", "creme de",
]


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def safe_eval(s):
    """Parse a stringified Python list, yielding [] on anything malformed."""
    try:
        return ast.literal_eval(s)
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Allergen flags
# ---------------------------------------------------------------------------

def allergen_flags(text, matcher):
    """Boolean flag per allergen class, over a Series of ingredient text.

    This is a vectorised restatement of allergen_lexicon.fires(): for each
    class the exempt phrases are blanked out of the text, and the class fires
    if any of its terms occurs in what remains.  The lexicon itself is imported
    rather than restated -- only the loop is different, because calling fires()
    row by row costs minutes over a corpus this size while pandas performs the
    same substring tests in seconds.

    verify_prototype.py checks the two agree on a random sample, so the
    equivalence is measured rather than assumed.
    """
    flags = {}
    for cls in ALLERGENS:
        masked = text
        for phrase in EXEMPT.get(cls, []):
            masked = masked.str.replace(phrase, " " * len(phrase), regex=False)
        hit = pd.Series(False, index=text.index)
        for term, _layer in matcher[cls]:
            hit |= masked.str.contains(term, regex=False, na=False)
        flags[f"allergen_{cls}"] = hit
    return pd.DataFrame(flags, index=text.index)


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

def run():
    os.makedirs(OUT, exist_ok=True)

    # -- stage 1: load and parse -------------------------------------------
    log("stage 1  loading RAW_recipes.csv")
    recipes = pd.read_csv(
        os.path.join(DATA, "RAW_recipes.csv"),
        usecols=["name", "id", "minutes", "tags", "nutrition", "n_steps",
                 "steps", "description", "ingredients", "n_ingredients"])
    n_raw = len(recipes)
    log(f"         {n_raw:,} rows")

    nutrition = recipes["nutrition"].map(safe_eval)
    nut = pd.DataFrame(
        [x if len(x) == 7 else [np.nan] * 7 for x in nutrition],
        columns=NUTRI_COLS, index=recipes.index)
    recipes = pd.concat([recipes.drop(columns=["nutrition"]), nut], axis=1)

    recipes["ingredients"] = recipes["ingredients"].map(safe_eval)
    recipes["tags"] = recipes["tags"].map(safe_eval)
    recipes["steps"] = recipes["steps"].map(safe_eval)
    recipes["description"] = recipes["description"].fillna("")
    log("stage 1  parsed nutrition, ingredients, tags, method and description")

    # -- stage 2: percentages of a daily value -> mass ----------------------
    for pdv_col, (mass_col, reference) in DAILY_VALUE.items():
        recipes[mass_col] = recipes[pdv_col] / 100.0 * reference
    recipes = recipes.drop(columns=list(DAILY_VALUE))
    log("stage 2  converted the nutrition tuple to mass per serving")

    # -- stage 3: meal slots ------------------------------------------------
    tagsets = recipes["tags"].map(set)
    slot_flags = {}
    for slot, tags in MEAL_SLOT_TAGS.items():
        want = set(tags)
        slot_flags[slot] = tagsets.map(lambda x, w=want: len(x & w) > 0)
    excluded = tagsets.map(lambda x, w=set(EXCLUDE_TAGS): len(x & w) > 0)
    any_slot = slot_flags["breakfast"] | slot_flags["lunch"] | slot_flags["dinner"]
    log(f"stage 3  slot-assignable after exclusions: "
        f"{int((any_slot & ~excluded).sum()):,}")

    # -- stage 4: the nine cleaning rules ----------------------------------
    # Order matters only for attributing removals to rules, not for the set
    # retained, which is the complement of the union of the masks.
    rules = {
        "missing name": recipes["name"].isna(),
        "nutrition tuple malformed": recipes["calories"].isna(),
        "calories == 0": recipes["calories"] == 0,
        "calories > 2000": recipes["calories"] > 2000,
        "minutes == 0": recipes["minutes"] == 0,
        "minutes > 1440 (24h)": recipes["minutes"] > 1440,
        "fewer than 2 ingredients": recipes["n_ingredients"] < 2,
        "no steps": recipes["n_steps"] < 1,
        "not assignable to a meal slot": ~(any_slot & ~excluded),
    }
    drop = pd.Series(False, index=recipes.index)
    other_drop = pd.Series(False, index=recipes.index)   # every rule but the last
    rule_report = {}
    for name, mask in rules.items():
        mask = mask.fillna(True)
        newly = int((mask & ~drop).sum())
        rule_report[name] = newly
        drop = drop | mask
        if name != "not assignable to a meal slot":
            other_drop = other_drop | mask
        log(f"stage 4  {name:<32} drops {newly:>7,}")

    keep = ~drop

    # -- stage 4b: the accompaniment pool ----------------------------------
    # A slot is filled by a main dish together with the accompaniments needed to
    # reach its energy target, so the planner needs a pool of dishes served
    # alongside a meal rather than as one.  Those recipes are exactly what the
    # meal-slot rule discards, and the pool is defined as disjoint from the main
    # corpus (`& ~keep`), so every figure reported for the corpus in Section
    # 3.2.2 is unaffected by admitting it.
    side_tagged = tagsets.map(lambda x, w=set(SIDE_TAGS): len(x & w) > 0)
    side_keep = ~other_drop & side_tagged & ~excluded & ~keep
    breakfast_side = tagsets.map(
        lambda x, w=set(SIDE_BREAKFAST_TAGS): len(x & w) > 0)
    log(f"stage 4b accompaniment pool: {int(side_keep.sum()):,} recipes, "
        f"{int((side_keep & breakfast_side).sum()):,} of them usable at "
        f"breakfast")

    # -- stage 5: ingredient normalisation ---------------------------------
    # Run before the filter is applied, so that the residue can be reported on
    # both denominators: on the raw corpus, where it reconciles against the
    # profiling run, and on the cleaned corpus, which is what the fail-closed
    # rule of Section 3.5.1 actually costs.
    log("stage 5  normalising ingredients through ingr_map.pkl")
    ingr_map = pd.read_pickle(os.path.join(DATA, "ingr_map.pkl"))
    raw2canon = dict(zip(ingr_map["raw_ingr"].str.lower(),
                         ingr_map["replaced"].str.lower()))
    canonical = set(ingr_map["replaced"].str.lower())

    def normalise(ingredients):
        """Canonical forms, and whether any ingredient resisted resolution.

        An ingredient that is neither a known raw form nor already canonical is
        left as it stands and the recipe is marked.  Section 3.5.1 excludes
        marked recipes outright whenever the user declares an allergy, because
        the system cannot establish what such an ingredient contains.
        """
        out, unresolved = [], False
        for item in ingredients:
            key = item.lower().strip()
            if key in raw2canon:
                out.append(raw2canon[key])
            elif key in canonical:
                out.append(key)
            else:
                out.append(key)
                unresolved = True
        return out, unresolved

    normalised = recipes["ingredients"].map(normalise)
    recipes["ingredients_norm"] = [x[0] for x in normalised]
    recipes["has_unmappable"] = [x[1] for x in normalised]
    pct_unmappable_raw = round(100 * float(recipes["has_unmappable"].mean()), 2)

    # Mains first, accompaniments after, so that the row order is stable and the
    # main corpus occupies a contiguous block.
    selected = keep | side_keep
    corpus = recipes.loc[selected].copy()
    corpus["is_side"] = side_keep.loc[selected].to_numpy()
    for slot in SLOTS:
        corpus[f"is_{slot}"] = slot_flags[slot].loc[selected].to_numpy()
        # An accompaniment is never a main, whatever its tags say.
        corpus.loc[corpus["is_side"], f"is_{slot}"] = False
    corpus["side_breakfast_ok"] = (
        corpus["is_side"] & breakfast_side.loc[selected].to_numpy())
    corpus = corpus.sort_values("is_side", kind="stable").reset_index(drop=True)

    n_main = int((~corpus["is_side"]).sum())
    log(f"stage 4  retained {n_main:,} mains of {n_raw:,} "
        f"({100 * n_main / n_raw:.2f} per cent), plus "
        f"{int(corpus['is_side'].sum()):,} accompaniments")
    mains = ~corpus["is_side"]
    log(f"stage 5  recipes with an unresolvable ingredient: "
        f"{pct_unmappable_raw} per cent of the raw corpus, "
        f"{100 * corpus.loc[mains, 'has_unmappable'].mean():.2f} per cent of "
        f"the cleaned main corpus (the latter is what the fail-closed rule "
        f"costs, and is the figure quoted in Section 3.5.1), "
        f"{100 * corpus.loc[~mains, 'has_unmappable'].mean():.2f} per cent of "
        f"the accompaniment pool")

    # -- stage 6: allergen tagging and diet flags --------------------------
    # Matching runs on the ingredient strings as the corpus records them, not
    # on the normalised forms: the composite layer needs complete multi-word
    # phrases, and normalisation collapses them to a head word (Section 3.2.4).
    log("stage 6  applying the three-layer allergen lexicon")
    ingr_text = corpus["ingredients"].map(lambda il: " | ".join(il).lower())
    corpus = pd.concat([corpus, allergen_flags(ingr_text, build_matcher())],
                       axis=1)

    tagsets_clean = corpus["tags"].map(set)
    corpus["is_vegetarian"] = tagsets_clean.map(lambda x: "vegetarian" in x)
    corpus["is_vegan"] = tagsets_clean.map(lambda x: "vegan" in x)
    halal_hit = pd.Series(False, index=corpus.index)
    for term in HALAL_EXCLUDED:
        halal_hit |= ingr_text.str.contains(term, regex=False, na=False)
    corpus["halal_ok"] = ~halal_hit

    for cls in ALLERGENS:
        n = int(corpus.loc[mains, f"allergen_{cls}"].sum())
        s = int(corpus.loc[~mains, f"allergen_{cls}"].sum())
        log(f"stage 6  allergen {cls:<14} mains {n:>7,} "
            f"({100 * n / int(mains.sum()):5.2f} per cent), "
            f"accompaniments {s:>6,}")
    log(f"stage 6  vegetarian {int(corpus['is_vegetarian'].sum()):,}, "
        f"vegan {int(corpus['is_vegan'].sum()):,}, "
        f"halal-admissible {int(corpus['halal_ok'].sum()):,} "
        f"(mains and accompaniments together)")

    # Document tokens for the content-based representation (Section 3.4.1):
    # normalised ingredients, spaces closed up so a multi-word ingredient stays
    # one term, plus the corpus tags.
    corpus["doc_tokens"] = [
        [i.replace(" ", "_") for i in ings] + list(tags)
        for ings, tags in zip(corpus["ingredients_norm"], corpus["tags"])
    ]
    corpus = corpus.drop(columns=["tags"])

    # -- interactions -------------------------------------------------------
    log("loading RAW_interactions.csv")
    inter = pd.read_csv(os.path.join(DATA, "RAW_interactions.csv"),
                        usecols=["user_id", "recipe_id", "rating"])
    # Restricted to the main corpus.  Accompaniments carry ratings of their own,
    # but the collaborative component ranks meals, not garnishes, and admitting
    # them would move the interaction count away from the figure Chapter 3
    # reports for the corpus the recommender is trained on.
    main_ids = set(corpus.loc[mains, "id"])
    inter = inter[inter["recipe_id"].isin(main_ids)].reset_index(drop=True)
    log(f"         {len(inter):,} interactions fall on the main corpus")

    # -- write --------------------------------------------------------------
    # Method and description are kept in a file of their own rather than in the
    # corpus.  The planner never reads them -- it ranks on nutrition, tags and
    # ingredients -- so carrying roughly 85 MB of prose through every scoring
    # pass would cost load time for nothing.  The interface loads this file
    # separately and only to render a recipe the user has opened.
    detail = {
        int(rid): {"steps": steps, "description": desc}
        for rid, steps, desc in zip(corpus["id"], corpus["steps"],
                                    corpus["description"])
    }
    with open(os.path.join(OUT, "recipe_detail.pkl"), "wb") as f:
        pickle.dump(detail, f, protocol=pickle.HIGHEST_PROTOCOL)
    log(f"wrote outputs/recipe_detail.pkl "
        f"({os.path.getsize(os.path.join(OUT, 'recipe_detail.pkl')) / 1e6:.0f} MB), "
        f"{sum(1 for v in detail.values() if v['steps']):,} with a method")
    corpus = corpus.drop(columns=["steps", "description"])

    with open(os.path.join(OUT, "corpus.pkl"), "wb") as f:
        pickle.dump(corpus, f, protocol=pickle.HIGHEST_PROTOCOL)
    with open(os.path.join(OUT, "interactions.pkl"), "wb") as f:
        pickle.dump(inter, f, protocol=pickle.HIGHEST_PROTOCOL)
    log(f"wrote outputs/corpus.pkl "
        f"({os.path.getsize(os.path.join(OUT, 'corpus.pkl')) / 1e6:.0f} MB) "
        f"and outputs/interactions.pkl")

    return corpus, inter, pct_unmappable_raw


# ---------------------------------------------------------------------------
# Reconciliation against the figures printed in Chapter 3
# ---------------------------------------------------------------------------

def reconcile(corpus, inter, pct_unmappable_raw):
    """Compare the pipeline output with the profiling run behind Chapter 3."""
    with open(os.path.join(OUT, "dataset_profile.json"), encoding="utf-8") as f:
        profile = json.load(f)

    mains = ~corpus["is_side"]
    expected = [
        ("main recipes retained", int(mains.sum()),
         profile["n_recipes_after_cleaning"]),
        ("interactions retained", len(inter),
         profile["n_interactions_on_clean_corpus"]),
        ("breakfast candidates", int(corpus["is_breakfast"].sum()),
         profile["clean_meal_slot_counts"]["breakfast"]),
        ("lunch candidates", int(corpus["is_lunch"].sum()),
         profile["clean_meal_slot_counts"]["lunch"]),
        ("dinner candidates", int(corpus["is_dinner"].sum()),
         profile["clean_meal_slot_counts"]["dinner"]),
        # Reconciled on the raw denominator, which is what profile_dataset.py
        # measured.  The figure Chapter 3 quotes in Section 3.5.1 is the cost
        # on the cleaned corpus, printed beneath.
        ("unresolvable share, raw corpus", pct_unmappable_raw,
         profile["pct_recipes_with_unmappable_ingredient"]),
        # The accompaniment pool must not overlap the main corpus, or a dish
        # could be served as its own side and the corpus figures above would no
        # longer describe what the planner ranks.
        ("mains that are also accompaniments",
         int((mains & corpus["is_side"]).sum()), 0),
    ]

    print()
    print("=" * 68)
    print("RECONCILIATION WITH CHAPTER 3")
    print("=" * 68)
    print(f"  {'quantity':<32}{'pipeline':>12}{'Chapter 3':>12}   ")
    bad = []
    for label, got, want in expected:
        ok = got == want
        print(f"  {label:<32}{got:>12,}{want:>12,}   {'OK' if ok else '*** MISMATCH ***'}"
              if isinstance(got, int) else
              f"  {label:<32}{got:>12}{want:>12}   {'OK' if ok else '*** MISMATCH ***'}")
        if not ok:
            bad.append(label)
    print(f"  {'unresolvable share, clean mains':<32}"
          f"{round(100 * float(corpus.loc[mains, 'has_unmappable'].mean()), 2):>12}"
          f"{'--':>12}   quoted in Section 3.5.1")
    print(f"  {'accompaniment pool':<32}"
          f"{int(corpus['is_side'].sum()):>12,}{'--':>12}   new in this build")
    print(f"  {'  usable at breakfast':<32}"
          f"{int(corpus['side_breakfast_ok'].sum()):>12,}{'--':>12}")
    print("=" * 68)
    if bad:
        print(f"RESULT: {len(bad)} figure(s) disagree with Chapter 3: {bad}")
        print("Either the pipeline is wrong, or Chapter 3 must be amended to")
        print("match it.  The two are not allowed to differ.")
        return False
    print("RESULT: every figure reproduces Chapter 3")
    return True


if __name__ == "__main__":
    t0 = time.time()
    corpus, inter, pct_unmappable_raw = run()
    ok = reconcile(corpus, inter, pct_unmappable_raw)
    log(f"finished in {time.time() - t0:.0f} s")
    sys.exit(0 if ok else 1)
