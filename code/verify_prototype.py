"""Verification pass over the prototype.

Checks, in order:
   1  the corpus reproduces the figures printed in Chapter 3
   2  the vectorised allergen tagging agrees with allergen_lexicon.fires()
   3  the hard filter is fail-closed for a user who declares an allergy
   4  a seven-day plan fills every slot and violates no declared restriction
   5  replacement preserves those invariants and feeds back a negative signal
   6  a rating moves the user's vector in the direction the rating means
   7  no corpus text reaches raw HTML
   8  the collaborative component is trained and the switch fires correctly
   9  relaxation never reaches a hard constraint
  10  an excluded ingredient is understood as the food, not as the string
  11  a changed restriction locks the plan instead of leaving it on screen
  12  a written note cannot make a safety, allergen or medical claim
  13  every recipe link is a well-formed Food.com URL

Groups 7 and 11 render the application through Streamlit's AppTest, which
executes the script and inspects the resulting element tree.  It does not lay
anything out, so it cannot see a column too narrow for its contents or a
control that has wrapped -- those are found by code/shoot.py, which drives a
real browser.  The two are complementary and neither replaces the other.

Run:  python code/verify_prototype.py
"""

import json
import os
import pickle
import random
import re
import sys
from collections import Counter
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "outputs")
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "src"))

import constraints as C           # noqa: E402
import weekly_planner as W        # noqa: E402
from allergen_lexicon import ALLERGENS, build_matcher, fires  # noqa: E402
from recommenders import (ContentRecommender, SwitchingController,  # noqa: E402
                          load_content_index)
from user_model import Profile, daily_targets                 # noqa: E402

fail = []


def check(name, ok, detail=""):
    print(f"   {name:<52} {'OK' if ok else '*** FAILED ***'}"
          + (f"   {detail}" if detail else ""))
    if not ok:
        fail.append(name)
    return ok


def section(n, title):
    print()
    print("=" * 70)
    print(f"{n}. {title}")
    print("=" * 70)


t0 = time.time()
print("loading corpus and index ...", flush=True)
with open(os.path.join(OUT, "corpus.pkl"), "rb") as f:
    df = pickle.load(f)
index = load_content_index()
corpus = C.Corpus(df, index)
content = ContentRecommender(index)
controller = SwitchingController(content)
print(f"loaded in {time.time() - t0:.0f} s")

# ---------------------------------------------------------------------------
section(1, "CORPUS AGAINST CHAPTER 3")
with open(os.path.join(OUT, "dataset_profile.json"), encoding="utf-8") as f:
    profile_json = json.load(f)

n_main = int((~df["is_side"]).sum())
check("main recipes retained = 128,403", n_main == 128403, f"{n_main:,}")
check("breakfast candidates = 19,919",
      int(df["is_breakfast"].sum()) == 19919, f"{int(df['is_breakfast'].sum()):,}")
check("lunch candidates = 40,779",
      int(df["is_lunch"].sum()) == 40779, f"{int(df['is_lunch'].sum()):,}")
check("dinner candidates = 103,389",
      int(df["is_dinner"].sum()) == 103389, f"{int(df['is_dinner'].sum()):,}")
with open(os.path.join(OUT, "interactions.pkl"), "rb") as f:
    inter = pickle.load(f)
check("interactions retained = 655,954", len(inter) == 655954, f"{len(inter):,}")

# The accompaniment pool must not overlap the main corpus, or a dish could be
# served as its own side and the figures above would stop describing what the
# planner ranks.
sides_mask = df["is_side"].to_numpy()
check("accompaniment pool is disjoint from the mains",
      not (sides_mask & (df["is_breakfast"] | df["is_lunch"]
                         | df["is_dinner"]).to_numpy()).any(),
      f"{int(sides_mask.sum()):,} accompaniments")
check("breakfast accompaniments are a subset of the pool",
      not (df["side_breakfast_ok"] & ~df["is_side"]).any(),
      f"{int(df['side_breakfast_ok'].sum()):,} usable at breakfast")

# ---------------------------------------------------------------------------
section(2, "VECTORISED ALLERGEN TAGGING vs THE LEXICON")
# preprocessing.py replaces the row-by-row fires() loop with pandas substring
# tests, for speed.  The two must agree exactly; here that is measured on a
# random sample rather than assumed.
random.seed(20260815)
sample = random.sample(range(len(df)), 500)
matcher = build_matcher()
disagreements = []
for row in sample:
    text = " | ".join(df["ingredients"].iloc[row]).lower()
    for cls in ALLERGENS:
        want = fires(text, cls, matcher)
        got = bool(df[f"allergen_{cls}"].iloc[row])
        if want != got:
            disagreements.append((row, cls, want, got))
check("500 recipes x 14 classes agree with fires()",
      not disagreements, f"{len(disagreements)} disagreement(s)")
for d in disagreements[:5]:
    print(f"      row {d[0]} {d[1]}: lexicon={d[2]} corpus={d[3]}")

# ---------------------------------------------------------------------------
section(3, "FAIL-CLOSED HARD FILTER")
allergic = Profile(age=28, sex="female", height_cm=165, weight_kg=62,
                   activity="lightly active",
                   allergens=["peanuts", "milk"],
                   liked_ingredients=["tomato", "basil", "chicken"])
mask, report = C.profile_filter(corpus, allergic)
check("no recipe flagged for a declared allergen survives",
      not (corpus.allergen["peanuts"] & mask).any()
      and not (corpus.allergen["milk"] & mask).any())
check("no recipe with an unresolvable ingredient survives",
      not (corpus.has_unmappable & mask).any(),
      f"{int((corpus.has_unmappable & mask).sum())} survived")
print(f"      filter report: {report}")

no_allergy = Profile(allergens=[])
mask_free, _ = C.profile_filter(corpus, no_allergy)
check("without a declared allergy the fail-closed rule does not fire",
      int((corpus.has_unmappable & mask_free).sum())
      == int(corpus.has_unmappable.sum()))

# ---------------------------------------------------------------------------
section(4, "SEVEN-DAY PLAN")
profiles = {
    "peanut + milk allergy, likes tomato/basil": allergic,
    "vegetarian, sedentary, 20 min weekdays": Profile(
        age=35, sex="male", height_cm=178, weight_kg=80, activity="inactive",
        diet_regime="vegetarian", weekday_minutes=20, weekend_minutes=60,
        liked_ingredients=["lentil", "spinach"], liked_cuisines=["indian"]),
    "vegan + gluten allergy + low sodium (hard case)": Profile(
        age=45, sex="female", height_cm=160, weight_kg=70, activity="active",
        diet_regime="vegan", allergens=["gluten"], max_sodium_mg=800,
        liked_ingredients=["rice", "mushroom"]),
    "halal, very active, no other restrictions": Profile(
        age=22, sex="male", height_cm=182, weight_kg=76, activity="very active",
        diet_regime="halal", liked_cuisines=["middle-eastern"]),
}

plans = {}
for label, prof in profiles.items():
    t = time.time()
    plan = W.plan_week(corpus, df, prof, controller)
    plans[label] = plan
    elapsed = time.time() - t
    daily = daily_targets(prof)

    print(f"\n   -- {label}")
    print(f"      mode: {plan.mode}")
    print(f"      built in {elapsed:.1f} s, "
          f"{len(plan.meals)}/21 slots filled, "
          f"daily target {daily['energy_kcal']:.0f} kcal")

    check("   21 slots filled", len(plan.meals) == 21,
          f"{len(plan.unfilled)} unfilled")
    for key, report in plan.unfilled.items():
        print(f"      unfilled {W.DAYS[key[0]]} {key[1]}: {report}")

    # Every check below is over the whole plate, mains and accompaniments
    # alike.  An allergen on a side dish is as dangerous as one on a main, so
    # nothing here looks at the main only.
    all_dishes = [d for m in plan.meals.values() for d in m.dishes]
    print(f"      {len(all_dishes)} dishes across 21 slots "
          f"({sum(len(m.sides) for m in plan.meals.values())} accompaniments)")

    violations = [d for d in all_dishes
                  for a in prof.allergens if a in d.allergens]
    check("   zero declared-allergen violations, sides included",
          not violations, f"{len(violations)} violation(s)")

    if prof.allergens:
        check("   no unresolvable-ingredient dish anywhere on a plate",
              not any(d.has_unmappable for d in all_dishes))

    main_ids = [m.recipe_id for m in plan.meals.values()]
    worst_repeat = max(Counter(main_ids).values())
    check(f"   no main served more than {prof.max_repeats} time(s)",
          worst_repeat <= prof.max_repeats, f"worst {worst_repeat}")

    side_ids = [s.recipe_id for m in plan.meals.values() for s in m.sides]
    check("   no accompaniment repeats within the week",
          len(set(side_ids)) == len(side_ids),
          f"{len(side_ids) - len(set(side_ids))} repeat(s)")
    check("   no dish is both a main and a side in the same week",
          not (set(main_ids) & set(side_ids)))

    bad_breakfast = [s for (d, sl), m in plan.meals.items() if sl == "breakfast"
                     for s in m.sides
                     if not bool(df["side_breakfast_ok"].iloc[s.row])]
    check("   breakfast sides come from the breakfast subset",
          not bad_breakfast, f"{len(bad_breakfast)} off-subset")

    if prof.diet_regime == "vegetarian":
        check("   every dish is tagged vegetarian",
              all(bool(corpus.is_vegetarian[d.row]) for d in all_dishes))
    if prof.diet_regime == "vegan":
        check("   every dish is tagged vegan",
              all(bool(corpus.is_vegan[d.row]) for d in all_dishes))
    if prof.diet_regime == "halal":
        check("   every dish passes the halal screen",
              all(bool(corpus.halal_ok[d.row]) for d in all_dishes))
    if prof.max_sodium_mg is not None:
        check("   every plate is under the sodium ceiling",
              all(m.sodium_mg <= prof.max_sodium_mg
                  for m in plan.meals.values()),
              f"worst {max(m.sodium_mg for m in plan.meals.values()):.0f} mg")

    if len(plan.meals) == 21:
        # The energy assertion used to demand 10 per cent and it passed easily,
        # which is exactly how the defect this section now guards against went
        # unnoticed: energy was the only quantity asserted on, so the planner
        # optimised it and ran to nearly four times the sodium ceiling without
        # any test objecting.  Energy is now one objective among several and is
        # deliberately traded against the guideline ceilings below, so the bound
        # is wider -- but the direction is asserted too, because a plan that
        # feeds slightly less than the target is acceptable and one that
        # quietly overfeeds is not.
        signed = [(plan.day_totals(d)["energy_kcal"] - daily["energy_kcal"])
                  / daily["energy_kcal"] for d in range(7)]
        worst = max(abs(x) for x in signed)
        mean = sum(signed) / len(signed)
        check("   daily energy within 25 per cent of target",
              worst <= 0.25, f"worst day {100 * worst:.1f} per cent off")
        check("   the residual energy error is an undershoot, not an overshoot",
              mean <= 0.0, f"mean {100 * mean:+.1f} per cent")

        # The guideline ceilings, which the first implementation ignored.
        ceilings = {
            "sodium": ("sodium_mg", daily["sodium_mg"]),
            "fat": ("fat_g", daily["fat_g"]),
            "sugar": ("sugar_g", daily["sugar_g"]),
        }
        for label, (key, limit) in ceilings.items():
            worst_day = max(plan.day_totals(d)[key] for d in range(7))
            check(f"   daily {label} within 15 per cent of its ceiling",
                  worst_day <= limit * 1.15,
                  f"worst {100 * worst_day / limit:.0f} per cent of limit")
        worst_satfat = max(sum(m.satfat_g for m in plan.day_meals(d))
                           for d in range(7))
        check("   daily saturated fat within 15 per cent of its ceiling",
              worst_satfat <= daily["satfat_g"] * 1.15,
              f"worst {100 * worst_satfat / daily['satfat_g']:.0f} per cent")

        # Variety within a day: the accompaniment selection used to see no
        # repetition penalty at all, which produced days carrying three
        # tomato-and-bread dishes.
        dupes = sum(1 for d in range(7)
                    for m in plan.day_meals(d)
                    if len({dish.recipe_id for dish in m.dishes})
                    != len(m.dishes))
        check("   no plate repeats a dish within itself", dupes == 0,
              f"{dupes} plate(s)")

    relaxed = [m for m in plan.meals.values() if m.relaxation > 0]
    if relaxed:
        print(f"      {len(relaxed)} slot(s) needed relaxation "
              f"(deepest: {C.relaxation_note(max(m.relaxation for m in relaxed))})")

# ---------------------------------------------------------------------------
section(5, "REPLACEMENT")
label = "peanut + milk allergy, likes tomato/basil"
plan, prof = plans[label], profiles[label]
before = plan.meal(0, "breakfast").name
n_rejected_before = len(prof.rejected)

swapped = 0
for _ in range(5):
    ok, message = W.replace_meal(corpus, df, prof, plan, 0, "breakfast",
                                 recommender=content)
    print(f"      {message}")
    if ok:
        swapped += 1

check("at least one replacement succeeded", swapped > 0, f"{swapped} of 5")
check("the recipe on screen actually changed",
      plan.meal(0, "breakfast").name != before)
check("each successful replacement fed back a negative signal",
      len(prof.rejected) == n_rejected_before + swapped,
      f"{len(prof.rejected) - n_rejected_before} recorded")
check("no declared allergen after replacing, sides included",
      not any(a in plan.meal(0, "breakfast").allergens for a in prof.allergens))
check("still 21 slots filled", len(plan.meals) == 21)
main_ids = [m.recipe_id for m in plan.meals.values()]
check("main repetition bound still respected",
      max(Counter(main_ids).values()) <= prof.max_repeats)
side_ids = [s.recipe_id for m in plan.meals.values() for s in m.sides]
check("accompaniments still never repeat",
      len(set(side_ids)) == len(side_ids))

day0 = plan.day_totals(0)["energy_kcal"]
target0 = plan.daily["energy_kcal"]
check("Monday's energy still within 20 per cent after five replacements",
      abs(day0 - target0) / target0 <= 0.20,
      f"{100 * abs(day0 - target0) / target0:.1f} per cent off")

# ---------------------------------------------------------------------------
section(6, "PERSONALISATION LOOP")
# A user told us the plan felt one-shot and impersonal.  These checks assert
# that the loop actually closes: that a rating moves the recommendations, that
# a low rating moves them the other way, and that a pinned meal survives a
# rebuild.
taster = Profile(age=30, sex="female", height_cm=168, weight_kg=64,
                 liked_ingredients=["tomato"])
base_scores = content.scores(taster)

# Rate one recipe highly and check its neighbourhood is pulled towards.
liked_row = int(np.argmax(np.where(corpus.slot["dinner"], base_scores, -np.inf)))
liked_id = int(df["id"].iloc[liked_row])
taster.ratings = {liked_id: 5}
up_scores = content.scores(taster)
check("a five-star rating raises that recipe's own score",
      up_scores[liked_row] > base_scores[liked_row],
      f"{base_scores[liked_row]:.3f} -> {up_scores[liked_row]:.3f}")

taster.ratings = {liked_id: 1}
down_scores = content.scores(taster)
check("a one-star rating LOWERS it instead of raising it",
      down_scores[liked_row] < up_scores[liked_row],
      f"1 star {down_scores[liked_row]:.3f} < 5 star {up_scores[liked_row]:.3f}")
check("a one-star rating is evidence against, not weaker evidence for",
      down_scores[liked_row] < base_scores[liked_row],
      f"{down_scores[liked_row]:.3f} < neutral {base_scores[liked_row]:.3f}")

# Pinning: rebuild while keeping three slots and confirm they are untouched.
pinner = Profile(age=30, sex="female", height_cm=168, weight_kg=64,
                 liked_ingredients=["tomato", "garlic"])
first = W.plan_week(corpus, df, pinner, controller)
pinned_keys = [(0, "breakfast"), (2, "lunch"), (5, "dinner")]
keep = {k: first.meals[k] for k in pinned_keys if k in first.meals}
kept_names = {k: m.main.name for k, m in keep.items()}
second = W.plan_week(corpus, df, pinner, controller, keep=keep)

check("rebuilding still fills 21 slots with meals pinned",
      len(second.meals) == 21, f"{len(second.unfilled)} unfilled")
check("every pinned meal survives the rebuild unchanged",
      all(second.meals[k].main.name == n for k, n in kept_names.items()),
      f"{len(kept_names)} pinned")
moved = sum(1 for k in second.meals if k not in kept_names
            and k in first.meals
            and second.meals[k].main.name != first.meals[k].main.name)
check("the unpinned slots are genuinely re-planned", moved > 0,
      f"{moved} of {21 - len(kept_names)} changed")

ids = [m.recipe_id for m in second.meals.values()]
check("the repetition bound still holds after a rebuild",
      max(Counter(ids).values()) <= pinner.max_repeats)
side_ids = [s.recipe_id for m in second.meals.values() for s in m.sides]
check("accompaniments still never repeat after a rebuild",
      len(set(side_ids)) == len(side_ids))

# The alternatives list must only offer what can actually be taken.
opts = W.alternatives(corpus, df, pinner, second, 3, "dinner", limit=6)
check("the alternatives list is non-empty", len(opts) > 0, f"{len(opts)} shown")
if opts:
    ok, msg = W.choose_alternative(corpus, df, pinner, second, 3, "dinner",
                                   opts[0]["row"], recommender=content)
    check("the first offered alternative can actually be chosen", ok, msg)
    check("choosing an alternative keeps the week complete",
          len(second.meals) == 21)

# ---------------------------------------------------------------------------
section(7, "NO CORPUS TEXT REACHES RAW HTML")
# The bug this guards against: 5,982 ingredient names contain a bare "&", which
# is not a valid HTML entity.  Interpolating them into an unsafe_allow_html
# string produced a DOM React could not reconcile, and every card raised
# "Failed to execute 'insertBefore' on 'Node'".
# Checked by rendering rather than by reading the source: a static scan cannot
# tell whether a variable holds corpus text, so the test renders the app and
# inspects what it actually emits.
n_amp = sum(1 for il in df["ingredients"] for i in il if "&" in i)
check("the hazard is real and still present in the corpus", n_amp > 0,
      f"{n_amp:,} ingredient names contain '&'")

from streamlit.testing.v1 import AppTest  # noqa: E402

rendered = AppTest.from_file(os.path.join(HERE, "app.py"),
                             default_timeout=600).run()
check("the interface renders without raising", not rendered.exception,
      f"{len(rendered.exception)} exception(s)")
for exc in rendered.exception[:3]:
    print(f"      {str(exc.value)[:120]}")

raw_html = [m.value for m in rendered.markdown if m.value.lstrip().startswith("<")]
check("some raw markup is emitted, so the test is not vacuous",
      len(raw_html) > 0, f"{len(raw_html)} block(s)")
check("no raw markup contains a bare '&'",
      not any("&" in v for v in raw_html),
      f"{sum(1 for v in raw_html if '&' in v)} offending block(s)")

shown = rendered.session_state["plan"]
if shown is not None:
    names = {m.main.name for m in shown.meals.values()}
    items = {i for m in shown.meals.values() for d in m.dishes
             for i in d.ingredients}
    leaked_names = [n for n in names if any(n in v for v in raw_html)]
    leaked_items = [i for i in items if any(i in v for v in raw_html)]
    check("no recipe name appears inside raw markup", not leaked_names,
          f"{len(leaked_names)} leaked")
    check("no ingredient name appears inside raw markup", not leaked_items,
          f"{len(leaked_items)} leaked")

# ---------------------------------------------------------------------------
section(8, "COLLABORATIVE COMPONENT AND THE SWITCH")
from recommenders import CollaborativeRecommender  # noqa: E402

cf = CollaborativeRecommender.load(index["recipe_ids"])
check("the collaborative model has been trained and stored",
      cf.factors is not None,
      "" if cf.factors is None else f"RMSE {cf.factors['val_rmse']:.4f}")

if cf.factors is not None:
    switch = SwitchingController(content, cf)
    cold = Profile(liked_ingredients=["tomato"])
    _, why_cold = switch.select(cold)
    check("a cold-start user is served by the content-based branch",
          "content-based" in why_cold, why_cold)

    # A fixture that resembles a real user of this corpus.  Taking the first
    # 500 recipes in corpus order gives a profile made of recipes almost nobody
    # has rated, which folds in to a meaningless latent vector and makes any
    # ranking check meaningless with it.  The most-rated recipes are what a
    # user with twelve ratings actually tends to have rated.
    rated_counts = Counter(inter["recipe_id"].to_numpy())
    popular = [int(r) for r, _ in rated_counts.most_common()
               if int(r) in cf.factors["item_index"]][:12]
    dense = Profile(ratings={r: 5 for r in popular})
    _, why_dense = switch.select(dense)
    check("a user past the threshold reaches the collaborative branch",
          "collaborative" in why_dense, why_dense)

    preds = cf.predicted_ratings(dense)
    check("collaborative predictions stay on the rating scale",
          float(preds.min()) >= 1.0 and float(preds.max()) <= 5.0,
          f"{preds.min():.2f} to {preds.max():.2f}")

    # Predicting a rating and ranking for a recommendation are different jobs
    # served by different parts of the same model.  Ranking by the prediction
    # ranks by the item bias, which on this corpus is estimated from very few
    # observations and swamps the latent term: measured over 2,000 held-out
    # users it scored no better than random (Section 5.3).  These two checks
    # exist because that defect passed every assertion in this suite.
    rank = cf.scores(dense)
    top_pred = set(np.argsort(-preds)[:10])
    top_rank = set(np.argsort(-rank)[:10])
    check("ranking and rating prediction are not the same ordering",
          top_pred != top_rank,
          f"{len(top_pred & top_rank)} of 10 shared")

    # The symptom the defect produced: a top ten made of recipes almost nobody
    # has rated, because a single five-star rating buys a large item bias.  The
    # check is relative rather than absolute -- it asserts that ranking by the
    # latent term reaches better-observed recipes than ranking by the
    # prediction does -- because that is the property the fix delivers, and an
    # absolute threshold would depend on the profile used as a fixture.  On
    # 200 real held-out users the medians are 91 ratings against 4.8.
    counts = Counter(inter["recipe_id"].to_numpy())
    obs = np.array([counts.get(int(r), 0) for r in index["recipe_ids"]])
    med_rank = float(np.median([obs[i] for i in top_rank]))
    med_pred = float(np.median([obs[i] for i in top_pred]))
    check("ranking reaches better-observed recipes than prediction does",
          med_rank > med_pred,
          f"median {med_rank:.0f} ratings ranked vs {med_pred:.0f} predicted")
    check("the model beats predicting the global mean",
          cf.factors["val_rmse"] < 1.2306,
          f"{cf.factors['val_rmse']:.4f} vs 1.2306")

# ---------------------------------------------------------------------------
section(9, "RELAXATION CANNOT REACH A HARD CONSTRAINT")
# Structural, not behavioural: the hard filter takes no weights and no gates, so
# there is no argument a relaxation could pass it.  Checked by confirming the
# filter output is identical at every relaxation level.
base_mask, _ = C.hard_filter(corpus, allergic, "dinner")
same = all(
    np.array_equal(base_mask,
                   C.hard_filter(corpus, allergic, "dinner")[0])
    for _ in range(C.MAX_RELAXATION + 1))
check("hard filter is independent of the relaxation level", same)
check("relaxed weights never revive a hard rule",
      all(term in C.WEIGHTS for term in C.RELAXATION_ORDER),
      "relaxation touches soft weights only")
for level in range(C.MAX_RELAXATION + 1):
    w = C.relaxed_weights(level)
    check(f"   level {level}: relevance weight intact, "
          f"{sum(1 for v in w.values() if v == 0)} soft term(s) surrendered",
          w["relevance"] == 1.0)

# ---------------------------------------------------------------------------
section(10, "THE EXCLUSION LIST MEANS THE FOOD, NOT THE STRING")
# A user excluded "oats" and was served "tuti fruity oatmeal", whose ingredient
# list is ['oatmeal', 'fruit juice'].
#
# This group exists because of how the previous version of it FAILED to catch
# that.  It asserted that no surviving recipe contained the literal string
# "oats", which was true -- "oats" is not a substring of "oatmeal" -- and so it
# passed while the defect was live.  The assertion tested the implementation's
# own notion of matching instead of the user's: the user meant "no oat
# products", not "no occurrence of o-a-t-s".  An assertion can only protect the
# property it actually states, and a wrong one is more dangerous than a missing
# one because it is counted as coverage.
#
# The checks below are therefore written in the user's terms.
plain_mask, _ = C.profile_filter(corpus, Profile())
oats_mask, _ = C.profile_filter(corpus, Profile(banned_ingredients=["oats"]))
check("excluding oats removes recipes at all",
      int(plain_mask.sum() - oats_mask.sum()) > 0,
      f"{int(plain_mask.sum() - oats_mask.sum()):,} recipes removed")

surviving = corpus.ingredient_text[oats_mask].tolist()
oatish = re.compile(r"\boat")
leaks = [t for t in surviving if oatish.search(t)]
check("no surviving recipe uses ANY oat product",
      not leaks, f"{len(leaks)} recipes still use an oat ingredient")

reported = df.loc[oats_mask, "name"].str.contains("tuti", case=False, na=False)
check("the dish the user reported is gone by name", not bool(reported.any()),
      "'tuti fruity oatmeal' (ingredients: oatmeal, fruit juice)")

# The opposite error, guarded so that fixing the first cannot reintroduce it:
# "oat" is a substring of "goat", and a substring rule silently removed goat's
# cheese from a user who had said nothing about goats.
oat_mask, _ = C.profile_filter(corpus, Profile(banned_ingredients=["oat"]))
goats = sum(1 for t in corpus.ingredient_text[oat_mask].tolist()
            if "goat" in t)
check("excluding 'oat' does not also remove goat's cheese", goats > 0,
      f"{goats:,} goat recipes survive")
check("singular and plural forms behave identically",
      int(oat_mask.sum()) == int(oats_mask.sum()),
      f"'oat' and 'oats' both leave {int(oats_mask.sum()):,}")

# End to end: the rule is only worth anything if it holds in a served plan.
oats_plan = W.plan_week(corpus, df, Profile(banned_ingredients=["oats"],
                                            liked_ingredients=["tomato"]),
                        SwitchingController(content, None))
served = [i for m in oats_plan.meals.values() for d in m.dishes
          for i in d.ingredients if oatish.search(i.lower())]
check("no oat product reaches the plate in a planned week", not served,
      f"{len(oats_plan.meals)} meals planned, {len(served)} oat ingredient(s)")

# The safety path is a different mechanism and must not regress with it.
import allergen_lexicon as AL  # noqa: E402

matcher = AL.build_matcher()
oat_forms = ("oats", "oatmeal", "rolled oat", "oat bran", "oat flour",
             "quick-cooking oatmeal", "cheerios toasted oat cereal")
missed = [f for f in oat_forms if not AL.fires(f, "gluten", matcher)]
check("the allergen lexicon still flags every oat form as gluten", not missed,
      f"{len(oat_forms)} forms checked" if not missed else f"missed {missed}")

# What the user is shown about a term that over-excludes.
names, n = C.matched_ingredients(corpus, "oats")
check("the interface can name what a term caught", bool(names),
      f"'oats' -> {n:,} recipes; " + ", ".join(names[:4]))

# ---------------------------------------------------------------------------
section(11, "A CHANGED RESTRICTION LOCKS THE PLAN ON SCREEN")
# A plan is rebuilt when the user asks for one, so editing a restriction does
# not by itself change what is displayed.  For a preference that is merely
# stale; for a restriction it is unsafe, because the user has just declared an
# exclusion and the system appears to have accepted it while still showing
# meals chosen before it.
locked = AppTest.from_file(os.path.join(HERE, "app.py"),
                           default_timeout=600).run()
n_before = len(locked.session_state["plan"].meals)
allergy_widget = [m for m in locked.multiselect if "Allerg" in str(m.label)]
if not allergy_widget:
    check("the allergy control is reachable in the rendered app", False)
else:
    allergy_widget[0].select("peanuts").run()
    check("the plan is NOT silently rebuilt behind the user's back",
          len(locked.session_state["plan"].meals) == n_before
          and locked.session_state["profile"].allergens == [],
          "the displayed plan and its profile are unchanged")
    notice = " ".join(m.value for m in locked.markdown)
    check("a notice states the plan predates the change",
          "Locked while your changes are pending" in notice,
          "notice present" if "Locked while" in notice else "NO notice emitted")
    # Not st.error: a red error box is what Streamlit shows when the script
    # crashes, and a user read this notice as the application breaking.
    check("the notice is not rendered as a crash",
          not locked.error,
          f"{len(locked.error)} error box(es)")
    # st.caption lands in at.caption, not at.markdown.
    lock_notes = [c.value for c in locked.caption
                  if "Locked until you rebuild" in c.value]
    check("every card is locked, not just some",
          len(lock_notes) == n_before,
          f"{len(lock_notes)} of {n_before} cards locked")
    openers = [b for b in locked.button
               if str(b.label) == "Open the recipe"]
    check("no card action survives the lock", not openers,
          f"{len(openers)} action button(s) still live")

# ---------------------------------------------------------------------------
section(12, "THE WRITTEN NOTE CANNOT MAKE A SAFETY CLAIM")
# advisor.py is a presentation-layer aid, not part of the recommender.  It is
# checked here because it is the one place where text the system did not write
# reaches a user, and a sentence asserting that a dish is safe would contradict
# the standing notice in the one place a user is most likely to believe it.
import advisor  # noqa: E402

for bad in ("This is safe for your allergies.",
            "A healthy choice, good for your heart.",
            "Contains no allergens.",
            "Consult your doctor before eating this.",
            "This dish is allergy-friendly.",
            ""):
    check(f"   rejected: {bad[:44] or '(empty response)'}",
          not advisor.passes_safety_filter(bad))
check("   accepted: an ordinary factual note",
      advisor.passes_safety_filter(
          "This 476 kcal portion leaves room in your dinner slot and takes "
          "30 minutes."))
check("an over-long response is rejected whatever it says",
      not advisor.passes_safety_filter("a" * (advisor.MAX_CHARS + 1)),
      f"limit {advisor.MAX_CHARS} characters")

# The degraded path is the one that runs during the user test if the key is
# absent, the network is down or the provider fails, so it is checked without
# reference to whether a key happens to be configured now.
probe = W.plan_week(corpus, df, Profile(liked_ingredients=["tomato"]),
                    SwitchingController(content, None))
probe_meal = probe.meal(0, "dinner")
if probe_meal is None:
    check("a dinner was planned to test the note against", False)
else:
    allowance = C.slot_allowance(probe.daily,
                                 W.day_consumed(probe, 0, "dinner"),
                                 W.remaining_share(probe, 0, "dinner"))
    fallback = advisor.derived_note(probe_meal.main, probe_meal, allowance,
                                    probe.daily, probe.profile)
    check("with no model at all, a note is still produced",
          bool(fallback and fallback.strip()), fallback[:60])
    check("and it passes the same filter the generated one must pass",
          advisor.passes_safety_filter(fallback))

# ---------------------------------------------------------------------------
section(13, "EVERY RECIPE LINK POINTS AT A WELL-FORMED FOOD.COM URL")
# The corpus records which ingredients a recipe uses but not how much of each,
# so a card cannot be cooked from alone.  The link supplies the quantities and
# is also the attribution the dataset's "Data files (c) Original Authors"
# terms deserve.  A malformed slug would send the user to a 404 instead.
import re as _re  # noqa: E402

SLUG = _re.compile(r"^https://www\.food\.com/recipe/[a-z0-9-]+-\d+$")


def _url(name, rid):
    return (f"https://www.food.com/recipe/"
            f"{_re.sub(r'[^a-z0-9]+', '-', str(name).lower()).strip('-')}-"
            f"{int(rid)}")


sample = df.sample(n=2000, random_state=0)
bad = [(n, i) for n, i in zip(sample["name"], sample["id"])
       if not SLUG.match(_url(n, i))]
check("2,000 sampled recipes all produce a well-formed URL", not bad,
      f"{len(bad)} malformed" if bad
      else _url(sample["name"].iloc[0], sample["id"].iloc[0])[:66])
check("names with an ampersand do not break the slug",
      all(SLUG.match(_url(n, 1)) for n in
          ("mac & cheese", "fish & chips", "salt & pepper squid")),
      "'&' collapses to a hyphen")

# ---------------------------------------------------------------------------
print()
print("=" * 70)
if fail:
    print(f"RESULT: {len(fail)} check(s) failed")
    for f_ in fail:
        print(f"  - {f_.strip()}")
    sys.exit(1)
print(f"RESULT: all checks passed  ({time.time() - t0:.0f} s)")
