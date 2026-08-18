"""Streamlit interface: the weekly plan as cards the user shapes.

Implements Section 3.7.2 of the dissertation.

FIVE THINGS HERE ARE NOT COSMETIC
---------------------------------
1.  The standing notice that allergen screening is automated and is not a
    safety guarantee.
2.  The full ingredient list on every card, expanded by default, so a user with
    an allergy can check without an extra interaction.
3.  The absence of any photograph.  The corpus carries no image of any dish,
    and its text is used under a research exemption rather than a licence, so
    there is no dish photograph this project may lawfully show.  What the cards
    carry instead comes from the data: a category mark and the macronutrient
    split.
4.  **The stale-plan lock.**  Editing a restriction in the sidebar does not
    rebuild the plan -- the user must press the button.  A user who adds an
    allergy and does not press it would otherwise be looking at a plan that
    predates the allergy, with no indication that it does.  For a system whose
    whole position on allergens is fail-closed, showing a stale plan as though
    it were current is the worst failure available.  So a restriction change
    locks the week until it is rebuilt.
5.  The four controls that make a plan something to shape rather than accept
    whole: rate, choose among alternatives, keep, rebuild.

RENDERING RULE, and the reason for it.  No text taken from the corpus may be
placed inside raw HTML.  An earlier build interpolated ingredient names into an
HTML string; 5,982 ingredient names in the corpus contain a bare "&", which is
not a valid entity, so the browser's error recovery produced a DOM React could
not reconcile and every card raised "Failed to execute 'insertBefore' on
'Node'".  Corpus text goes through native components only; the raw markup that
survives (backdrop, meters, macronutrient bars) contains numbers this module
computes and no corpus text at all.

Run:  streamlit run code/app.py
"""

import os
import pickle
import re
import sys

import numpy as np
import streamlit as st

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "outputs")
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "src"))

import advisor                     # noqa: E402
import constraints as C            # noqa: E402
import uistyle                     # noqa: E402
import weekly_planner as W         # noqa: E402
from allergen_lexicon import ALLERGENS               # noqa: E402
from figstyle import BLUE, GREY, NAVY, TEAL          # noqa: E402
from make_background import data_uri                 # noqa: E402
from recommenders import (CollaborativeRecommender,  # noqa: E402
                          ContentRecommender, SwitchingController,
                          load_content_index)
from user_model import (PAL, Profile, basal_metabolic_rate,  # noqa: E402
                        daily_targets)

ALLERGEN_LABELS = {
    "gluten": "Gluten", "crustaceans": "Crustaceans", "eggs": "Eggs",
    "fish": "Fish", "peanuts": "Peanuts", "soybeans": "Soy", "milk": "Milk",
    "tree_nuts": "Tree nuts", "celery": "Celery", "mustard": "Mustard",
    "sesame": "Sesame", "sulphites": "Sulphites", "lupin": "Lupin",
    "molluscs": "Molluscs",
}

# Category marks, in priority order.  Drawn from the corpus tags, so the mark is
# a property of the data.  It is a category symbol, not a depiction: no claim is
# made that the dish looks like this.
CATEGORY_MARKS = [
    ("seafood", "🦐"), ("fish", "🐟"), ("poultry", "🍗"), ("chicken", "🍗"),
    ("beef", "🥩"), ("pork", "🥓"), ("lamb-sheep", "🍖"), ("meat", "🍖"),
    ("pasta", "🍝"), ("pizza", "🍕"), ("sandwiches", "🥪"),
    ("soups-stews", "🍲"), ("salads", "🥗"), ("curries", "🍛"),
    ("rice", "🍚"), ("grains", "🌾"), ("potatoes", "🥔"), ("beans", "🫘"),
    ("eggs", "🥚"), ("cheese", "🧀"), ("breads", "🍞"), ("fruit", "🍎"),
    ("vegetables", "🥦"), ("greens", "🥬"), ("side-dishes", "🥄"),
]
DEFAULT_MARK = "🍽️"

SLOT_LABEL = {"breakfast": "Breakfast", "lunch": "Lunch", "dinner": "Dinner"}

# Ingredients a kitchen keeps rather than buys per recipe.
PANTRY = ("oil", "salt", "pepper", "water", "sugar", "flour", "butter",
          "vinegar", "stock", "broth", "sauce", "spray", "yeast", "baking",
          "vanilla", "cornstarch", "honey", "syrup", "wine", "seasoning")

# Changing any of these invalidates the plan in a way that matters for safety.
SAFETY_FIELDS = ("allergens", "diet_regime", "max_sodium_mg", "max_sugar_g",
                 "banned_ingredients")

st.set_page_config(page_title="Weekly Recipe Planner", layout="wide",
                   page_icon="🍽️")


@st.cache_resource(show_spinner=False)
def backdrop():
    return data_uri()


st.markdown(uistyle.page_css(backdrop()), unsafe_allow_html=True)


@st.cache_resource(show_spinner="Loading the recipe corpus ...")
def load():
    with open(os.path.join(OUT, "corpus.pkl"), "rb") as f:
        df = pickle.load(f)
    index = load_content_index()
    corpus = C.Corpus(df, index)
    collaborative = CollaborativeRecommender.load(index["recipe_ids"])
    controller = SwitchingController(ContentRecommender(index), collaborative)
    return df, index, corpus, controller


@st.cache_resource(show_spinner="Loading recipe methods ...")
def load_detail():
    with open(os.path.join(OUT, "recipe_detail.pkl"), "rb") as f:
        return pickle.load(f)


df, index, corpus, controller = load()
detail = load_detail()
content = controller.content


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------
def plain(text):
    """Neutralise markdown metacharacters in corpus text."""
    out = str(text)
    for ch in ("\\", "*", "_", "`", "[", "]", "$"):
        out = out.replace(ch, "\\" + ch)
    return out


def category_mark(tokens):
    have = set(tokens)
    for tag, mark in CATEGORY_MARKS:
        if tag in have:
            return mark
    return DEFAULT_MARK


def source_url(name, recipe_id):
    """The recipe's page on Food.com.

    The corpus records which ingredients a recipe uses but not how much of
    each, so it cannot be cooked from alone.  Linking to the page the recipe
    came from supplies the quantities, and is also the proper attribution: the
    dataset is published as "Data files (c) Original Authors", so the people
    who wrote these recipes should be the ones a user is sent to.  A link is
    not a copy -- nothing is fetched, stored or redistributed here.
    """
    slug = re.sub(r"[^a-z0-9]+", "-", str(name).lower()).strip("-")
    return f"https://www.food.com/recipe/{slug}-{int(recipe_id)}"


def macro_bar(protein_g, fat_g, carbs_g):
    """Share of energy from each macronutrient.  Figure palette, not chrome."""
    p, f, c = protein_g * 4.0, fat_g * 9.0, carbs_g * 4.0
    total = p + f + c
    if total <= 0:
        return ""
    parts = [(p / total * 100, TEAL), (f / total * 100, NAVY),
             (c / total * 100, BLUE)]
    spans = "".join(f"<span style='width:{w:.1f}%;background:{col}'></span>"
                    for w, col in parts)
    return f"<div class='macrobar'>{spans}</div>"


def meter(fraction, over):
    """A single attainment bar.  Numbers only -- no corpus text."""
    width = max(0.0, min(fraction, 1.4)) / 1.4 * 100
    colour = uistyle.TERRACOTTA if over else TEAL
    return (f"<div class='meter'><span style='width:{width:.1f}%;"
            f"background:{colour}'></span></div>")


def split(text):
    return [t.strip() for t in text.split(",") if t.strip()]


@st.cache_data(show_spinner=False)
def matched_terms(term):
    """Which ingredient names an excluded term catches. Cached: it scans the
    whole corpus, and the sidebar re-runs on every interaction."""
    return C.matched_ingredients(corpus, term)


# ---------------------------------------------------------------------------
# Sidebar: the profile
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Your profile")

    st.subheader("About you")
    col_a, col_b = st.columns(2)
    age = col_a.number_input("Age", 16, 100, 30)
    sex = col_b.selectbox("Sex", ["female", "male"])
    height = col_a.number_input("Height (cm)", 120.0, 220.0, 165.0, step=1.0)
    weight = col_b.number_input("Weight (kg)", 35.0, 200.0, 65.0, step=1.0)
    activity = st.selectbox("Activity level", list(PAL), index=1)

    st.subheader("Time to cook")
    weekday_minutes = st.slider("Weekdays (minutes)", 10, 120, 30, step=5)
    weekend_minutes = st.slider("Weekends (minutes)", 10, 180, 75, step=5)
    max_repeats = st.slider(
        "How often may one main dish come round?", 1, 3, 2,
        help="Accompaniments never repeat, so a dish you see twice arrives "
             "with something different beside it.")

    st.subheader("Restrictions")
    st.caption("These remove recipes outright. They are never traded off "
               "against how well a recipe matches your taste.")
    allergens = st.multiselect(
        "Allergies", list(ALLERGENS),
        format_func=lambda k: ALLERGEN_LABELS.get(k, k))
    diet_regime = st.selectbox(
        "Dietary regime", ["none", "vegetarian", "vegan", "halal"])
    if diet_regime == "halal":
        st.caption("The corpus carries no halal labelling, so this screens for "
                   "pork, its derivatives and alcohol by ingredient name. It "
                   "is an approximation, not a certification.")
    low_sodium = st.checkbox("Low sodium (clinical)")
    low_sugar = st.checkbox("Low sugar (clinical)")
    banned = st.text_input("Other ingredients to avoid",
                           placeholder="olives, coriander")
    # What each term actually caught.  A term is matched by its stem against
    # the start of a word, so "oats" removes oatmeal and oat bran as well --
    # correct, and not something the user can guess.  The same rule
    # over-excludes: "pea" also removes peanut and peach.  That is the
    # acceptable direction of error for an exclusion list, but only because it
    # is shown here rather than applied silently.
    for term in split(banned):
        names, n_recipes = matched_terms(term)
        if not names:
            st.caption(f"'{term}' matches no ingredient in the corpus.")
            continue
        st.caption(f"**'{term}'** removes {n_recipes:,} recipes, including "
                   f"those using: " + ", ".join(plain(x) for x in names)
                   + ("…" if len(names) >= 8 else ""))

    st.subheader("What you like")
    st.caption("Used to rank recipes, not to exclude them. Rating meals in the "
               "plan adds to this.")
    liked = st.text_input("Ingredients you enjoy",
                          placeholder="tomato, basil, chicken")
    cuisines = st.text_input("Cuisines you enjoy", placeholder="italian, thai")

    build = st.button("Build my week", type="primary", width="stretch")


def profile_from_form():
    return Profile(
        age=int(age), sex=sex, height_cm=float(height),
        weight_kg=float(weight), activity=activity,
        allergens=allergens, diet_regime=diet_regime,
        max_sodium_mg=800.0 if low_sodium else None,
        max_sugar_g=15.0 if low_sugar else None,
        banned_ingredients=split(banned),
        liked_ingredients=split(liked), liked_cuisines=split(cuisines),
        weekday_minutes=int(weekday_minutes),
        weekend_minutes=int(weekend_minutes),
        max_repeats=int(max_repeats),
    )


def build_plan(profile, keep=None):
    with st.spinner("Planning seven days ..."):
        return W.plan_week(corpus, df, profile, controller, keep=keep)


# ---------------------------------------------------------------------------
# Session state, and the stale-plan lock
# ---------------------------------------------------------------------------
form_profile = profile_from_form()

if build or "plan" not in st.session_state:
    fresh = form_profile
    if not build and "profile" in st.session_state:
        fresh.ratings = st.session_state["profile"].ratings
        fresh.rejected = st.session_state["profile"].rejected
    st.session_state["profile"] = fresh
    st.session_state["plan"] = build_plan(fresh)

plan = st.session_state["plan"]
prof = st.session_state["profile"]
daily = plan.daily


def drift():
    """Which sidebar fields no longer match the plan on screen.

    Returns (safety_changed, changed_field_labels).  A safety change is one
    that could make a displayed meal one the user has since told us to exclude.
    """
    labels = {"allergens": "allergies", "diet_regime": "dietary regime",
              "max_sodium_mg": "low-sodium limit",
              "max_sugar_g": "low-sugar limit",
              "banned_ingredients": "ingredients to avoid",
              "age": "age", "sex": "sex", "height_cm": "height",
              "weight_kg": "weight", "activity": "activity level",
              "weekday_minutes": "weekday cooking time",
              "weekend_minutes": "weekend cooking time",
              "max_repeats": "variety", "liked_ingredients": "liked ingredients",
              "liked_cuisines": "liked cuisines"}
    changed = [labels[f] for f in labels
               if getattr(form_profile, f) != getattr(prof, f)]
    unsafe = any(getattr(form_profile, f) != getattr(prof, f)
                 for f in SAFETY_FIELDS)
    return unsafe, changed


unsafe_drift, changed_fields = drift()

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.title("Your week")
st.caption("Seven days, twenty-one meals, planned around what you like and "
           "what you can eat.")

st.warning(
    "**Allergen screening here is automated and is not a safety guarantee.** "
    "Ingredients are matched against a rule set whose false-negative rate is "
    "measured, not assumed to be zero. Always read the full ingredient list, "
    "shown on every card, before cooking or eating anything suggested here.")

if changed_fields:
    if unsafe_drift:
        # Deliberately not st.error.  A red error box is the same thing
        # Streamlit shows when the script crashes, and a user who saw this
        # after pressing Enter read it as the application breaking rather than
        # as the application protecting them.  A notice that is mistaken for a
        # fault teaches the user to dismiss it, which is the opposite of what a
        # safety notice is for.  So it is styled as part of this page, opens by
        # saying what the system did, and says plainly that nothing is broken.
        with st.container(border=True):
            st.markdown(
                f"🔒 **Locked while your changes are pending — nothing has "
                f"gone wrong.** You changed {', '.join(changed_fields)}, so "
                f"the plan below is out of date and may contain meals you "
                f"have just excluded. Rather than show it as though it were "
                f"current, the cards are held until you press **Build my "
                f"week**. Your ratings and pinned meals are kept.")
    else:
        st.info(f"You changed {', '.join(changed_fields)}. Press **Build my "
                f"week** to see a plan that uses it.")

head_l, head_r = st.columns([3, 1])
with head_l:
    n_sides = sum(len(m.sides) for m in plan.meals.values())
    st.caption(
        f"Ranked by {plan.mode}. Each slot is a main dish plus whatever "
        f"accompaniments it needs to reach its target ({n_sides} this week), "
        f"because one recipe serving is usually smaller than a meal. A main "
        f"may come round up to {prof.max_repeats} time(s), always with "
        f"something different beside it.")
with head_r:
    if st.button("Rebuild from my feedback", width="stretch",
                 disabled=unsafe_drift or not (prof.ratings or prof.rejected
                                               or plan.locked),
                 help="Keeps anything you pinned and re-plans the rest using "
                      "every rating and rejection so far."):
        keep = {k: plan.meals[k] for k in plan.locked if k in plan.meals}
        st.session_state["plan"] = build_plan(prof, keep=keep)
        st.rerun()
    st.caption(f"{len(prof.ratings)} rated · {len(prof.rejected)} rejected · "
               f"{len(plan.locked)} pinned")

if plan.unfilled:
    st.error(
        f"{len(plan.unfilled)} of 21 slots could not be filled. The week is "
        f"returned with the gaps in it rather than filled with something your "
        f"restrictions exclude.")
    for (day_index, slot), report in plan.unfilled.items():
        with st.expander(f"Why {W.DAYS[day_index]} {slot} is empty"):
            for rule, n in report.items():
                st.write(f"- {rule}: {n:,}")


# ---------------------------------------------------------------------------
# Recipe detail
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner=False, ttl=3600)
def cached_note(recipe_id, _dish, _meal, _allowance, _daily, _profile, count):
    """One note per recipe per session.  `recipe_id` and `count` are the key."""
    return advisor.note_for(_dish, _meal, _allowance, _daily, _profile, count)


@st.dialog("Recipe", width="large")
def recipe_dialog(dish, meal, allowance, week_count, once_only):
    """Everything about one dish.  All corpus text via native components."""
    st.markdown(f"### {category_mark(df['doc_tokens'].iloc[dish.row])} "
                f"{plain(dish.name)}")
    st.caption(f"{dish.minutes} min · {dish.per_serving_calories:.0f} kcal per "
               f"serving · this plan serves {dish.servings:g}")

    info = detail.get(dish.recipe_id, {})
    if info.get("description"):
        # A markdown blockquote, not raw HTML: this is the recipe author's own
        # text out of the corpus, and corpus text never enters raw markup.
        st.markdown("> " + plain(" ".join(info["description"].split())))

    with st.spinner("Writing a note ..."):
        note, note_source = cached_note(dish.recipe_id, dish, meal, allowance,
                                        daily, prof, week_count)
    if note:
        st.markdown(f"**{plain(note)}**")
        st.caption("Written by a language model from this recipe's own figures."
                   if note_source == "model" else
                   "Derived from this plan's own figures.")
        st.caption("It describes what the plan contains. It is not safety or "
                   "medical advice.")

    if dish.allergens:
        st.warning("Flagged for: "
                   + ", ".join(ALLERGEN_LABELS.get(a, a)
                               for a in dish.allergens)
                   + ". The screening is automated and is not a safety "
                     "guarantee — read the ingredients below.")

    left, right = st.columns([1, 1])
    with left:
        st.markdown("**Ingredients**")
        for item in dish.ingredients:
            st.markdown(f"- {plain(item)}")
        st.caption("The dataset records which ingredients a recipe uses, not "
                   "how much of each. For quantities, open the original "
                   "recipe.")

        # Only the ingredients this dish alone is responsible for buying, and
        # only a few.  An earlier version marked every once-used ingredient
        # inline, which flagged nine of eleven lines and so told the user
        # nothing: a marker that fires on almost everything is not a marker.
        mine = [i for i in dish.ingredients
                if any(o.lower() in i.lower() for o in once_only)][:3]
        if mine:
            st.caption("Bought for this dish alone: "
                       + ", ".join(plain(i) for i in mine)
                       + ". The leftovers section below suggests what else "
                         "they would go into.")
        st.link_button("Open the original recipe on Food.com",
                       source_url(dish.name, dish.recipe_id), width="stretch")

    with right:
        st.markdown("**What it supplies**")
        rows = [
            {"": "Energy", "This dish": f"{dish.calories:.0f} kcal",
             "Slot allows": f"{allowance['energy_kcal']:.0f} kcal"},
            {"": "Protein", "This dish": f"{dish.protein_g:.0f} g",
             "Slot allows": f"{allowance['protein_g']:.0f} g"},
            {"": "Carbohydrate", "This dish": f"{dish.carbs_g:.0f} g",
             "Slot allows": f"{allowance['carbs_g']:.0f} g"},
            {"": "Fat", "This dish": f"{dish.fat_g:.0f} g",
             "Slot allows": f"{allowance['fat_g']:.0f} g"},
            {"": "Saturated fat", "This dish": f"{dish.satfat_g:.0f} g",
             "Slot allows": f"{allowance['satfat_g']:.0f} g"},
            {"": "Sugars", "This dish": f"{dish.sugar_g:.0f} g",
             "Slot allows": f"{allowance['sugar_g']:.0f} g"},
            {"": "Salt (sodium)", "This dish": f"{dish.sodium_mg:.0f} mg",
             "Slot allows": f"{allowance['sodium_mg']:.0f} mg"},
        ]
        st.dataframe(rows, hide_index=True, width="stretch")
        st.markdown("**Where it sits in your week**")
        st.write(f"- {100 * dish.calories / max(daily['energy_kcal'], 1):.0f} "
                 f"per cent of your daily energy")
        st.write(f"- {100 * dish.protein_g / max(daily['protein_g'], 1e-6):.0f} "
                 f"per cent of your daily protein")
        if week_count > 1:
            st.write(f"- appears {week_count} times this week")

    st.markdown("**Method**")
    steps = info.get("steps") or []
    if steps:
        for n, step in enumerate(steps, 1):
            st.markdown(f"{n}. {plain(step)}")
    else:
        st.caption("The corpus records no method for this recipe.")

    # The rest of the plate.  A meal is a main dish plus its accompaniments,
    # and a user who opens "the recipe" is asking about the meal, so the sides
    # are described here rather than behind another control.
    if meal is not None and meal.sides:
        st.markdown("**Also on this plate**")
        for side in meal.sides:
            with st.expander(f"{plain(side.name)} · {side.calories:.0f} kcal "
                             f"· {side.minutes} min"):
                if side.allergens:
                    st.warning("Flagged for: " + ", ".join(
                        ALLERGEN_LABELS.get(a, a) for a in side.allergens)
                        + ". Screening is automated and is not a safety "
                          "guarantee — read the ingredients.")
                cols = st.columns([1, 1])
                with cols[0]:
                    for item in side.ingredients:
                        st.markdown(f"- {plain(item)}")
                with cols[1]:
                    st.write(f"{side.protein_g:.0f} g protein · "
                             f"{side.carbs_g:.0f} g carbohydrate · "
                             f"{side.fat_g:.0f} g fat")
                    st.write(f"{side.sodium_mg:.0f} mg sodium · "
                             f"{side.sugar_g:.0f} g sugars")
                    st.link_button("Open the original recipe",
                                   source_url(side.name, side.recipe_id),
                                   width="stretch")
                side_steps = (detail.get(side.recipe_id) or {}).get("steps")
                if side_steps:
                    st.markdown("**Method**")
                    for n, step in enumerate(side_steps, 1):
                        st.markdown(f"{n}. {plain(step)}")
        st.caption(f"The plate comes to {meal.calories:.0f} kcal against a "
                   f"slot allowance of {allowance['energy_kcal']:.0f} kcal.")

    if meal is not None and dish is meal.main and meal.terms:
        st.markdown("**Why this was chosen**")
        st.caption(", ".join(f"{k} {v:+.2f}" for k, v in meal.terms.items())
                   + " — a weighted sum of named terms, so each contribution "
                     "can be read rather than inferred.")


# ---------------------------------------------------------------------------
# Leftovers, computed once per plan and reused by the cards
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def leftover_ingredients(used_ids):
    """Ingredients this week uses exactly once, excluding pantry staples."""
    rows = [corpus.row_of[r] for r in used_ids if r in corpus.row_of]
    counts = {}
    for row in rows:
        for item in df["ingredients_norm"].iloc[row]:
            counts[item] = counts.get(item, 0) + 1
    return [i for i, n in counts.items()
            if n == 1 and not any(s in i for s in PANTRY)]


@st.cache_data(show_spinner=False)
def leftover_suggestions(used_ids, restriction_key, budget, wanted=6):
    """Recipes that would use up what this week leaves behind.

    TWO THINGS THIS DELIBERATELY DOES.

    It runs the user's own hard filter over the candidates.  A suggestion is a
    suggestion to eat something, so the fail-closed rule of Section 3.5.1
    applies here exactly as it does inside the planner.  The first version
    queried the ingredient matrix directly and would happily have offered a
    peanut recipe to a user who had declared a peanut allergy -- the section
    sits below the plan, so it looked like a footnote rather than a
    recommendation, which is precisely why it was easy to miss.

    It prefers a recipe that clears *several* leftovers at once.  Picking the
    candidate nearest a 30-minute target, as the first version did, returned
    six recipes all of exactly 30 minutes, which reads as canned.  Ranking by
    how many of the week's orphaned ingredients a dish would use is both more
    varied and more useful: one dish that finishes the jalapenos, the coriander
    and the tortillas is worth more than three that each finish one.

    `restriction_key` is not read.  It is a hashable summary of the fields that
    change the filter, present so that the cache is keyed on them.
    """
    del restriction_key
    profile = st.session_state["profile"]
    rows = {corpus.row_of[r] for r in used_ids if r in corpus.row_of}
    vocab = corpus.ingr_vocabulary
    admissible, _ = C.profile_filter(corpus, profile)

    leftovers = leftover_ingredients(used_ids)
    columns = {i: vocab.get(i.replace(" ", "_")) for i in leftovers}
    columns = {i: c for i, c in columns.items() if c is not None}
    if not columns:
        return []

    # How many of the week's leftovers each recipe would use up.
    clears = np.zeros(corpus.n, dtype=np.int32)
    for col in columns.values():
        clears[corpus.ingr_matrix[:, col].nonzero()[0]] += 1

    out = []
    for item, col in columns.items():
        users = [int(u) for u in corpus.ingr_matrix[:, col].nonzero()[0]
                 if int(u) not in rows and admissible[u]]
        if len(users) < 3:
            continue
        pick = max(users, key=lambda u: (clears[u],
                                         -abs(corpus.minutes[u] - budget)))
        out.append({"ingredient": item, "n_recipes": len(users),
                    "row": pick, "name": str(df["name"].iloc[pick]),
                    "minutes": int(corpus.minutes[pick]),
                    "clears": int(clears[pick]),
                    "recipe_id": int(df["id"].iloc[pick])})
        if len(out) >= wanted:
            break
    return out


def restriction_key(profile):
    """A hashable summary of everything that changes the hard filter."""
    return (tuple(sorted(profile.allergens)), profile.diet_regime,
            profile.max_sodium_mg, profile.max_sugar_g,
            tuple(sorted(profile.banned_ingredients)))


once_only = leftover_ingredients(tuple(plan.placed_ids()))


# ---------------------------------------------------------------------------
# The week at a glance
#
# WHY THERE ARE TWO VIEWS OF THE SAME WEEK.  The first build laid the week out
# as seven columns of full cards.  On a 1680-pixel window each column is about
# 130 pixels, which is narrower than the words that have to go in it: recipe
# names wrapped to four lines, and the controls degraded to a vertical stack of
# single letters -- "Other options" rendered as O-t-h-e-r on six lines.  It was
# unusable, and it was invisible to every automated check in this project,
# because those run against Streamlit's AppTest, which builds the element tree
# and never renders it.  It became visible the moment the interface was
# photographed in a real browser (code/shoot.py).
#
# Seven columns is the right shape for *seeing the week*, and the wrong shape
# for *working on a meal*.  So the week is shown twice: a compact strip that
# fits seven days across, then a row per day wide enough for the ingredient
# list the safety rule requires to be open.
# ---------------------------------------------------------------------------
st.markdown("#### The week at a glance")
overview = st.columns(7)
for day_index, column in enumerate(overview):
    weekend = day_index >= 5
    with column:
        budget = prof.weekend_minutes if weekend else prof.weekday_minutes
        st.markdown(
            f"<div class='{'weekend' if weekend else ''}'>"
            f"<div class='daylabel'>{W.DAYS[day_index][:3]}</div>"
            f"<div class='daysub'>{'weekend' if weekend else 'weekday'} · "
            f"{budget} min</div></div>",
            unsafe_allow_html=True)
        for slot in W.SLOTS:
            meal = plan.meal(day_index, slot)
            if meal is None:
                st.markdown(f"<div class='slotname'>{SLOT_LABEL[slot]}</div>",
                            unsafe_allow_html=True)
                st.caption("— nothing fits —")
                continue
            st.markdown(
                f"<div class='glance'><span class='mark-sm'>"
                f"{category_mark(df['doc_tokens'].iloc[meal.main.row])}</span>"
                f"<span class='slotname'>{SLOT_LABEL[slot]}</span></div>",
                unsafe_allow_html=True)
            # No HTML wrapper around the name: st.markdown escapes it, which is
            # the protection this module depends on, so a <small> tag would
            # appear on screen as text.
            st.markdown(plain(meal.main.name))
            sides = (f" · plus {len(meal.sides)} side"
                     + ("s" if len(meal.sides) > 1 else "")) if meal.sides else ""
            st.caption(f"{meal.calories:.0f} kcal{sides}")
        st.markdown(f"<div class='daytotal'>"
                    f"{plan.day_totals(day_index)['energy_kcal']:.0f} kcal"
                    f"</div>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# One meal, at working width
# ---------------------------------------------------------------------------
@st.fragment
def render_card(day_index, slot, locked):
    key = (day_index, slot)
    plan = st.session_state["plan"]
    prof = st.session_state["profile"]
    meal = plan.meal(day_index, slot)

    with st.container(border=True):
        if meal is None:
            st.markdown(f"<div class='slotname'>{SLOT_LABEL[slot]}</div>",
                        unsafe_allow_html=True)
            st.markdown("**No acceptable recipe**")
            st.caption("Your restrictions leave nothing for this slot. The "
                       "slot is left empty rather than filled with something "
                       "you have excluded.")
            return

        pinned = key in plan.locked
        mark = category_mark(df["doc_tokens"].iloc[meal.main.row])
        st.markdown(
            f"<div class='cardhead'><span class='mark'>{mark}</span>"
            f"<span class='slotname'>{SLOT_LABEL[slot]}"
            f"{' · pinned' if pinned else ''}</span>"
            f"<span class='kcal'>{meal.calories:.0f} kcal</span></div>",
            unsafe_allow_html=True)
        st.markdown(f"##### {plain(meal.main.name)}")
        helping = (f" · {meal.main.servings:g} helpings"
                   if meal.main.servings != 1 else "")
        st.caption(f"{meal.main.calories:.0f} kcal{helping} · "
                   f"{meal.main.minutes} min")

        for side in meal.sides:
            st.markdown(f"↳ {plain(side.name)}")
            st.caption(f"{side.calories:.0f} kcal · {side.minutes} min")

        st.markdown(macro_bar(meal.protein_g, meal.fat_g, meal.carbs_g),
                    unsafe_allow_html=True)
        line = (f"{meal.minutes} min total · P {meal.protein_g:.0f} / "
                f"F {meal.fat_g:.0f} / C {meal.carbs_g:.0f} g")
        if meal.allergens:
            line += " · contains " + ", ".join(
                ALLERGEN_LABELS.get(a, a) for a in meal.allergens)
        st.caption(line)

        # Expanded by default: an allergic user must be able to check without
        # an extra interaction (§3.7.2).
        with st.expander(f"{len(meal.ingredients)} ingredients", expanded=True):
            for dish in meal.dishes:
                if meal.sides:
                    st.markdown(f"*{plain(dish.name)}*")
                halves = st.columns(2)
                items = list(dish.ingredients)
                cut = (len(items) + 1) // 2
                for half, chunk in zip(halves, (items[:cut], items[cut:])):
                    with half:
                        for item in chunk:
                            st.markdown(f"- {plain(item)}")
            if meal.has_unmappable:
                st.caption("One ingredient here could not be resolved to a "
                           "known form, so it could not be screened.")
            if meal.relaxation:
                st.caption(f"To fill this slot the planner "
                           f"{C.relaxation_note(meal.relaxation)}. Allergen "
                           f"rules were not relaxed.")

        if locked:
            st.caption("🔒 Locked until you rebuild — your restrictions "
                       "changed after this meal was chosen.")
            return

        counts = plan.used_counts()
        allowance = C.slot_allowance(
            plan.daily, W.day_consumed(plan, day_index, slot),
            W.remaining_share(plan, day_index, slot))

        act = st.columns(2)
        with act[0]:
            # One button, not a popover of one button per dish.  The popover
            # version left itself open on top of the dialog it had just
            # spawned, because opening a dialog does not dismiss it.  The whole
            # plate is described inside the dialog instead.
            if st.button("Open the recipe", width="stretch",
                         key=f"detail-{day_index}-{slot}"):
                recipe_dialog(meal.main, meal, allowance,
                              counts.get(meal.main.recipe_id, 1), once_only)
        with act[1]:
            with st.popover("Swap this meal", width="stretch"):
                options = W.alternatives(corpus, df, prof, plan, day_index,
                                         slot)
                if not options:
                    st.caption("No other recipe fits this slot right now.")
                for opt in options:
                    st.markdown(f"{category_mark(opt['tokens'])} "
                                f"**{plain(opt['name'])}**")
                    st.caption(f"{opt['calories']:.0f} kcal · "
                               f"{opt['minutes']} min")
                    if st.button("Choose this",
                                 key=f"alt-{day_index}-{slot}-{opt['row']}",
                                 width="stretch"):
                        ok, msg = W.choose_alternative(
                            corpus, df, prof, plan, day_index, slot,
                            opt["row"], recommender=content)
                        (st.toast if ok else st.warning)(msg)
                        st.rerun()
                    st.divider()
        # Pin and rating share a row of their own.  Squeezed into a third
        # column beside the two popovers, the toggle's label broke across two
        # lines as "P / in".
        foot = st.columns([3, 2])
        with foot[0]:
            if st.toggle("Keep this one", value=pinned,
                         key=f"pin-{day_index}-{slot}",
                         help="Pinned meals survive a rebuild unchanged."):
                plan.locked.add(key)
            else:
                plan.locked.discard(key)
        with foot[1]:
            current = prof.ratings.get(meal.recipe_id)
            stars = st.feedback("stars", key=f"rate-{day_index}-{slot}",
                                default=None if current is None
                                else current - 1)
            if stars is not None:
                prof.ratings[meal.recipe_id] = stars + 1


# ---------------------------------------------------------------------------
# The week, a day at a time
# ---------------------------------------------------------------------------
st.markdown("#### Day by day")
for day_index in range(len(W.DAYS)):
    weekend = day_index >= 5
    budget = prof.weekend_minutes if weekend else prof.weekday_minutes
    totals = plan.day_totals(day_index)
    st.markdown(
        f"<div class='{'weekend' if weekend else ''}'>"
        f"<div class='daylabel'>{W.DAYS[day_index]}</div>"
        f"<div class='daysub'>{'weekend' if weekend else 'weekday'} · "
        f"{budget} min to cook · {totals['energy_kcal']:.0f} of "
        f"{daily['energy_kcal']:.0f} kcal</div></div>",
        unsafe_allow_html=True)
    slot_columns = st.columns(3)
    for column, slot in zip(slot_columns, W.SLOTS):
        with column:
            render_card(day_index, slot, unsafe_drift)

# ---------------------------------------------------------------------------
# Nutrition, in plain language
# ---------------------------------------------------------------------------
st.header("How this week feeds you")

bmr = basal_metabolic_rate(prof)
st.markdown("**Where your numbers come from**")
st.caption(
    f"You are {prof.age}, {prof.sex}, {prof.height_cm:.0f} cm and "
    f"{prof.weight_kg:.0f} kg. That gives a resting energy need of "
    f"{bmr:.0f} kcal a day — what your body uses doing nothing at all. "
    f"Being **{prof.activity}** multiplies it by {PAL[prof.activity]}, so you "
    f"need about **{daily['energy_kcal']:.0f} kcal a day**. The rest of the "
    f"targets are shares of that, following the United Kingdom government's "
    f"dietary recommendations.")

reach_l, limit_r = st.columns(2)

TO_REACH = [("Energy", "energy_kcal", "kcal"), ("Protein", "protein_g", "g"),
            ("Carbohydrate", "carbs_g", "g")]
NOT_EXCEED = [("Fat", "fat_g", "g"), ("Saturated fat", "satfat_g", "g"),
              ("Sugars", "sugar_g", "g"), ("Salt (sodium)", "sodium_mg", "mg")]


def week_stat(key):
    """Worst day and average across the week for one nutrient."""
    per_day = []
    for d in range(len(W.DAYS)):
        if key == "satfat_g":
            per_day.append(sum(m.satfat_g for m in plan.day_meals(d)))
        else:
            per_day.append(plan.day_totals(d)[key])
    return max(per_day), sum(per_day) / len(per_day)


with reach_l:
    st.markdown("**Aim to reach these**")
    st.caption("Falling short means the week is not feeding you enough.")
    for label, key, unit in TO_REACH:
        worst, mean = week_stat(key)
        target = daily[key]
        frac = mean / max(target, 1e-6)
        st.markdown(f"{label} — {mean:.0f} of {target:.0f} {unit} a day "
                    f"({100 * frac:.0f}%)")
        st.markdown(meter(frac, over=False), unsafe_allow_html=True)

with limit_r:
    st.markdown("**Try to stay under these**")
    st.caption("Going over is what the guidance warns about.")
    for label, key, unit in NOT_EXCEED:
        worst, mean = week_stat(key)
        limit = daily[key]
        frac = worst / max(limit, 1e-6)
        verdict = ("within the guideline" if frac <= 1.0
                   else f"{100 * (frac - 1):.0f}% over on the worst day")
        st.markdown(f"{label} — worst day {worst:.0f} of {limit:.0f} {unit} "
                    f"({verdict})")
        st.markdown(meter(frac, over=frac > 1.0), unsafe_allow_html=True)

chart_rows = [{"Day": W.DAYS[d][:3],
               "Energy": round(plan.day_totals(d)["energy_kcal"]),
               "Target": round(daily["energy_kcal"])}
              for d in range(len(W.DAYS))]
# sort=False keeps Monday first: the default sorts the axis alphabetically,
# which rendered the week as Fri, Mon, Sat, Sun, Thu, Tue, Wed.
st.bar_chart(chart_rows, x="Day", y=["Energy", "Target"], stack=False,
             color=[BLUE, GREY], height=220, width="stretch",
             sort=False, x_label="", y_label="kcal")
st.caption("Blue is what the plan supplies; grey is your target. The palette "
           "is the one used for the figures in the dissertation.")

with st.expander("The day-by-day numbers"):
    rows = []
    for day_index in range(len(W.DAYS)):
        totals = plan.day_totals(day_index)
        rows.append({
            "Day": W.DAYS[day_index],
            "Energy (kcal)": round(totals["energy_kcal"]),
            "vs target": f"{100 * (totals['energy_kcal'] / daily['energy_kcal'] - 1):+.0f}%",
            "Protein (g)": round(totals["protein_g"]),
            "Fat (g)": round(totals["fat_g"]),
            "Carbs (g)": round(totals["carbs_g"]),
            "Sodium (mg)": round(totals["sodium_mg"]),
        })
    rows.append({"Day": "Target",
                 "Energy (kcal)": round(daily["energy_kcal"]), "vs target": "",
                 "Protein (g)": round(daily["protein_g"]),
                 "Fat (g)": round(daily["fat_g"]),
                 "Carbs (g)": round(daily["carbs_g"]),
                 "Sodium (mg)": round(daily["sodium_mg"])})
    st.dataframe(rows, width="stretch", hide_index=True)

# ---------------------------------------------------------------------------
# Leftovers
# ---------------------------------------------------------------------------
st.header("Shopping that carries over")
st.caption("An ingredient bought for one dish is rarely sold in one dish's "
           "worth. These are the ones this week uses only once, with a recipe "
           "that would use up the rest.")

ideas = leftover_suggestions(tuple(plan.placed_ids()), restriction_key(prof),
                             prof.weekday_minutes)
if not ideas:
    st.caption("Nothing obvious is left over this week.")
for idea in ideas:
    with st.container(border=True):
        cols = st.columns([3, 3, 1])
        cols[0].markdown(f"**{plain(idea['ingredient'])}**")
        cols[0].caption(f"used once this week · in {idea['n_recipes']:,} "
                        f"recipes you can eat")
        cols[1].markdown(plain(idea["name"]))
        extra = (f" · uses {idea['clears']} of this week's leftovers"
                 if idea["clears"] > 1 else "")
        cols[1].caption(f"{idea['minutes']} min{extra}")
        cols[2].link_button("Open recipe",
                            source_url(idea["name"], idea["recipe_id"]),
                            width="stretch")
st.caption("These are screened against your restrictions in the same way the "
           "plan is. The screening is automated and is not a safety guarantee.")

with st.expander("How a recipe was chosen, and what is kept about you"):
    st.write(
        "Every candidate is scored as a weighted sum of named terms, so each "
        "contribution can be read rather than inferred: **relevance** to your "
        "stated tastes, minus penalties for **energy** deviation from the "
        "slot's allowance, **nutritional** error, **repetition** of "
        "ingredients already used this week, and preparation **time** over "
        "your budget for that day.")
    st.write(
        "Restrictions never enter that sum. Allergens, dietary regime and any "
        "clinical limits remove recipes before scoring begins, and are never "
        "relaxed — if that leaves a slot empty, the slot stays empty.")
    st.write(
        "**Nothing about you is stored.** There is no account and no database. "
        "The collaborative model was trained offline on the public rating "
        "history in the dataset; your own ratings are fitted into it in memory "
        "for this session only and are gone when you close the page.")
