"""Constraint engine: a hard filter, soft penalties, and adaptive relaxation.

Implements Section 3.5 of the dissertation.  The three stages are strictly
ordered and the ordering carries the safety argument:

    HARD        removes candidates outright, before any preference score is
                computed.  Four categories, per Section 3.5.1.
    SOFT        reduces a candidate's score without removing it, per the
                weighted sum of Section 3.5.2.
    RELAXATION  loosens the soft stage only, in a fixed order, when a slot
                cannot otherwise be filled.

Allergen filtering is never relaxed, under any circumstance, including the case
where relaxing it is the only way to return a complete plan.  An incomplete week
that says which slots could not be filled is the correct output; a meal the
system has reason to believe the user cannot safely eat is not.
"""

import re

import numpy as np

# Weights a to e of the scoring function in Section 3.5.2.  Preference has the
# largest single influence, while the nutritional terms dominate in combination
# when a candidate is badly matched.  These are the starting values; Chapter 5
# tunes them on a validation split.
WEIGHTS = {
    "relevance": 1.0,   # a
    "energy": 0.4,      # b
    "macros": 0.3,      # c
    "repetition": 0.2,  # d
    "time": 0.1,        # e
}

# Order in which soft constraints are given up when a slot cannot be filled
# (§3.5.3).  Preparation time is surrendered first because it is the least
# consequential to the objective, and energy last because it is the most.
RELAXATION_ORDER = ["time", "repetition", "macros", "energy"]

# Tolerance on each soft term beyond which a candidate is not acceptable for a
# slot at all.
#
# Section 3.5.3 says relaxation "widens the admissible set without touching the
# filter", which requires the soft stage to have an admissible set of its own:
# without one, every non-empty filtered set yields a winner by argmax and the
# relaxation step of Algorithm 3.1 could never fire.  These gates supply it.
#
# The energy gate is set by measurement rather than by taste, and was re-swept
# after accompaniments were introduced.  Under the earlier single-dish design it
# had to be tight -- relevance carries weight 1.0 against energy's 0.4, so a
# loose gate let the ranker trade energy accuracy for preference, and worst-day
# error ran from 8 per cent at a gate of 0.15 to 20 per cent at 0.50.  With
# accompaniments closing the gap the pressure disappears: over the same four
# profiles the worst day now lies between 0.2 and 3.5 per cent at every gate
# tried, with all twenty-one slots filled throughout.  The measured best, 0.25,
# is adopted.
#
# Tuning the scoring weights instead would have been the wrong lever: Section
# 3.5.2 fixes them as starting values that Chapter 5 tunes on a validation
# split, so moving them here to make a test pass would prejudge that experiment.
# A gate is not a weight -- it says which candidates are eligible for a slot at
# all, and leaves the ranking among them to the weights.
SOFT_GATES = {
    "time": 1.0,        # preparation time may exceed the day's budget twofold
    "repetition": 0.6,  # at most 60 per cent of ingredients already used
    "macros": 1.5,      # mean relative macronutrient deviation
    "energy": 0.25,     # main dish within 25 per cent of its share of the slot
}

# Nutrients entering the M term of Section 3.5.2, split by what the guidance
# actually says about each.
#
# This distinction was missing from the first implementation and the omission
# was serious.  The United Kingdom recommendations set protein and carbohydrate
# as quantities to reach, and fat, saturated fat, free sugars and salt as
# ceilings not to exceed; the scoring function treated fat as a target to hit
# and ignored saturated fat, sugar and sodium entirely.  Measured over three
# profiles, the resulting plans landed within 1.3 per cent of the energy target
# every day while running to 390 per cent of the sodium ceiling, 473 per cent of
# the sugar ceiling and 171 per cent of the fat ceiling.  The planner was
# optimising the one quantity the interface displayed and violating the rest.
#
# TARGETS are penalised for deviation in either direction; CEILINGS are
# penalised only for exceedance, so there is no pressure to eat up to a limit.
TARGET_NUTRIENTS = ("protein_g", "carbs_g")
CEILING_NUTRIENTS = ("fat_g", "satfat_g", "sugar_g", "sodium_mg")
MACROS = TARGET_NUTRIENTS + CEILING_NUTRIENTS

# Weight on ceiling exceedance relative to deviation from a target, within the
# M term.  Set by measurement: see the sweep recorded in Chapter 5.  It exists
# because the two are not equally consequential -- missing a protein target by
# a fifth is a worse plan, whereas exceeding the salt ceiling by a fifth is a
# worse diet -- and because full compliance is not attainable on this corpus at
# any weight, so the parameter selects a point on a trade-off rather than a
# right answer.  Only 4.1 per cent of main dishes and 4.4 per cent of
# accompaniments satisfy all four ceilings at once, and only 414 of the 19,919
# breakfast candidates do, so a planner forced into full compliance would be
# choosing from a twenty-fifth of the corpus.
# Swept over three profiles.  Worst-day figures, as a percentage of each limit:
#
#   weight   energy err   sodium   fat    sugar   sat fat
#     0          2.9%      2610%   132%    585%    195%
#     1          8.8%       106%   143%    294%    109%
#     2         14.7%        98%   129%    141%    115%
#     4         16.2%        99%   102%    104%    102%
#     8         15.4%        90%   103%    105%     96%
#
# Four is adopted: it is the first weight at which every ceiling is met to
# within a few per cent.  The cost is energy, and the direction of that cost
# matters -- the residual is an undershoot averaging 5.5 per cent, never a
# systematic overshoot, so the failure mode is a plan that feeds slightly less
# than the target rather than one that quietly exceeds the salt limit
# twenty-six times over.
CEILING_EMPHASIS = 4.0

# A Food.com serving is much smaller than a meal.  Measured on the cleaned
# corpus, the median dinner candidate supplies 381 kcal while the dinner slot of
# a 2,440 kcal day asks for 976, and only 5.5 per cent of dinner candidates
# reach that figure in one serving.  A slot filled by a single dish therefore
# undershoots its energy target badly whichever dish is chosen.
#
# The gap is closed the way a cook closes it, by serving accompaniments beside
# the main dish rather than by serving the main dish several times over.  This
# replaced an earlier design in which a slot held one recipe at up to three
# servings; the change was prompted by user feedback and is supported by
# measurement.  Against a 976 kcal dinner target, one serving of a main plus up
# to two accompaniments brings 95.9 per cent of dinner candidates within ten per
# cent of the target, where servings alone reached only 49.8 per cent.  The same
# measurement showed that allowing more than one serving of the main added
# nothing once accompaniments were available, so the ceiling is now 1.5 -- a
# larger helping, not a second dinner.
MAX_SERVINGS = 1.5
MIN_SERVINGS = 0.5
SERVING_STEP = 0.5

# Accompaniments served beside one main dish.
MAX_SIDES = 2

# An accompaniment is only worth listing if it does real work.  Without these
# floors the planner closes a residual gap of four kilocalories with a fourth
# dish, which is arithmetically correct and useless to cook.
MIN_GAP_FOR_SIDE = 80.0    # kcal still missing before another dish is added
MIN_SIDE_KCAL = 40.0       # smallest accompaniment worth putting on the plate

# Share of a slot's energy the main dish is expected to carry, the remainder
# being left for accompaniments to supply.
#
# The main is ranked against this share rather than against the whole slot
# target, because with accompaniments available a modest main is no longer a
# defect: penalising it as though it had to reach the target alone would rule
# out most of the corpus for no reason.
#
# Swept jointly with the energy gate over four profiles at 0.55, 0.65 and 0.75.
# Every combination filled all twenty-one slots; worst-day energy error ranged
# from 0.2 to 3.5 per cent, and 0.55 with a gate of 0.25 was the best at 1.4 per
# cent.  The spread is narrow because the structure, not the parameter, is what
# fixes the energy error.
MAIN_SHARE = 0.55

# How many times one main dish may appear across the seven days.
#
# The earlier design barred a recipe outright once it had been placed, on the
# stated grounds that no user would regard the same dish twice in a week as a
# recommendation.  A user contradicted that directly: a dish they like, which is
# quick and fits their targets, is welcome more than once provided what is
# served beside it changes.  Repetition is therefore bounded rather than
# forbidden, the bound is exposed to the user, and accompaniments never repeat
# so that a repeated main arrives in different company.
DEFAULT_MAX_REPEATS = 2

SLOT_COLUMNS = {"breakfast": "is_breakfast",
                "lunch": "is_lunch",
                "dinner": "is_dinner"}


class Corpus:
    """Numpy views of the columns the filter and the penalties read.

    The constraint engine is evaluated twenty-one times per plan and again on
    every replacement, over a candidate set of up to 103,389 recipes, so the
    columns are extracted from the DataFrame once here rather than on each call.
    Everything below this line is vectorised: a filter is a boolean array and a
    penalty is a float array, both over the whole corpus.
    """

    def __init__(self, df, index):
        self.df = df
        self.ids = df["id"].to_numpy()
        self.n = len(df)
        self.row_of = {rid: i for i, rid in enumerate(self.ids)}

        self.calories = df["calories"].to_numpy(dtype=np.float64)
        self.minutes = df["minutes"].to_numpy(dtype=np.float64)
        self.sodium_mg = df["sodium_mg"].to_numpy(dtype=np.float64)
        self.sugar_g = df["sugar_g"].to_numpy(dtype=np.float64)
        self.macros = {m: df[m].to_numpy(dtype=np.float64) for m in MACROS}

        self.slot = {s: df[c].to_numpy(dtype=bool)
                     for s, c in SLOT_COLUMNS.items()}
        self.is_side = df["is_side"].to_numpy(dtype=bool)
        # Accompaniments admissible in each slot.  Breakfast draws on a subset,
        # because the pool is dominated by vegetable dishes and a bowl of
        # roasted vegetables beside porridge is not a suggestion a user acts on.
        breakfast_side = df["side_breakfast_ok"].to_numpy(dtype=bool)
        self.side_slot = {"breakfast": breakfast_side,
                          "lunch": self.is_side,
                          "dinner": self.is_side}
        self.allergen = {c[len("allergen_"):]: df[c].to_numpy(dtype=bool)
                         for c in df.columns if c.startswith("allergen_")}
        self.has_unmappable = df["has_unmappable"].to_numpy(dtype=bool)
        self.is_vegetarian = df["is_vegetarian"].to_numpy(dtype=bool)
        self.is_vegan = df["is_vegan"].to_numpy(dtype=bool)
        self.halal_ok = df["halal_ok"].to_numpy(dtype=bool)

        # Lower-cased ingredient text, for the user's own exclusion list.
        self.ingredient_text = df["ingredients"].map(
            lambda il: " | ".join(il).lower())

        # Binary recipe-by-ingredient matrix, for the repetition penalty.
        self.ingr_matrix = index["ingr_matrix"]
        self.ingr_vocabulary = index["ingr_vocabulary"]
        counts = np.asarray(self.ingr_matrix.sum(axis=1)).ravel()
        self.ingr_count = np.maximum(counts, 1.0)


# ---------------------------------------------------------------------------
# Hard constraints (§3.5.1)
# ---------------------------------------------------------------------------

def profile_filter(corpus, profile):
    """The part of the hard filter that depends only on the user (rules 1-5).

    Separated from the slot and plan-dependent part because it is the expensive
    part -- the user's own exclusion list is a substring scan over the whole
    corpus -- and because it does not change over the twenty-one slots of a
    plan.  The planner computes it once and passes it to hard_filter().

    Returns (mask, report).  `report` records how many candidates each rule
    removed from those still standing when it ran, which is what the interface
    shows the user when a slot cannot be filled.  Rules are applied in order of
    decreasing consequence so that the explanation names the most serious cause
    first.
    """
    mask = np.ones(corpus.n, dtype=bool)
    report = {"corpus": corpus.n}

    def apply(rule, condition):
        nonlocal mask
        before = int(mask.sum())
        mask &= condition
        removed = before - int(mask.sum())
        if removed:
            report[rule] = removed

    # 1  Declared allergens.  Never relaxed.
    for cls in profile.allergens:
        if cls in corpus.allergen:
            apply(f"allergen: {cls}", ~corpus.allergen[cls])

    # 2  Fail-closed.  Where the user declares an allergy and a candidate
    #    contains an ingredient that could not be resolved to a canonical form,
    #    the system cannot establish that the recipe is free of the allergen,
    #    so it excludes it rather than admitting it.  Wrongly excluding a recipe
    #    removes one option from a corpus of over a hundred thousand; wrongly
    #    admitting one may cause harm.
    if profile.allergens:
        apply("unresolvable ingredient (fail-closed)", ~corpus.has_unmappable)

    # 3  Religious and ethical regimes.  Vegetarian and vegan are served by the
    #    corpus tags, which is a whitelist and therefore errs towards exclusion.
    #    Halal has no tag of any kind in this corpus and is approximated by an
    #    ingredient blacklist; the interface says so.
    if profile.diet_regime == "vegetarian":
        apply("not tagged vegetarian", corpus.is_vegetarian)
    elif profile.diet_regime == "vegan":
        apply("not tagged vegan", corpus.is_vegan)
    elif profile.diet_regime == "halal":
        apply("contains a non-halal ingredient", corpus.halal_ok)

    # 4  Clinical exclusions are applied in hard_filter() instead, because they
    #    bind on the quantity actually eaten and so depend on the serving count,
    #    which in turn depends on the slot.  A ceiling of 800 mg of sodium is
    #    not respected by a recipe carrying 800 mg per serving of which the plan
    #    asks the user to eat three.

    # 5  The user's own exclusion list.
    for term in profile.banned_ingredients:
        pattern = exclusion_pattern(term)
        if pattern:
            apply(f"contains '{term.strip().lower()}'",
                  ~corpus.ingredient_text.str.contains(
                      pattern, regex=True, na=False).to_numpy())

    return mask, report


# The user's own exclusion list is matched with this rather than with a plain
# substring test, for a reason worth recording.  A substring test is
# simultaneously too loose and too tight: "oat" matches goat cheese, while
# "oats" fails to match oatmeal, because "oats" is not a substring of
# "oatmeal".  A user who excluded oats was therefore served oatmeal, which is
# the defect this replaces.
#
# Anchoring at a word boundary removes the first error; matching a prefix of a
# word removes the second.  The stem drops a trailing plural so that the
# singular and plural forms of a term behave identically.
#
# The remaining error is over-exclusion: "pea" also removes peach and peanut.
# For an exclusion list that direction is the acceptable one -- the cost is
# some lost variety, where the cost of under-exclusion is being served food the
# user has said they do not want -- but it must not be silent, so
# `matched_ingredients` below lets the interface show what a term caught.
_PLURAL = ("es", "s")


def exclusion_stem(term):
    """The stem a term is matched by, or "" if the term is unusable."""
    term = " ".join(str(term).strip().lower().split())
    if not term:
        return ""
    head, _, tail = term.rpartition(" ")
    for suffix in _PLURAL:
        if len(tail) > len(suffix) + 2 and tail.endswith(suffix):
            tail = tail[: -len(suffix)]
            break
    return (head + " " + tail).strip() if head else tail


def exclusion_pattern(term):
    """A word-boundary-anchored prefix pattern for one excluded term."""
    stem = exclusion_stem(term)
    if not stem:
        return ""
    return r"\b" + r"\s+".join(re.escape(w) for w in stem.split()) + r"\w*"


def matched_ingredients(corpus, term, limit=8):
    """The distinct ingredient names an excluded term actually catches.

    Shown in the interface beneath the exclusion box.  A prefix rule that
    over-excludes is defensible only if the user can see what it removed, so
    this is what turns the heuristic above from a hidden approximation into a
    visible one the user can correct by rewording the term.
    """
    pattern = exclusion_pattern(term)
    if not pattern:
        return [], 0
    hit = corpus.ingredient_text.str.contains(pattern, regex=True, na=False)
    compiled = re.compile(pattern)
    names = {}
    for text in corpus.ingredient_text[hit.to_numpy()]:
        for part in text.split(" | "):
            if compiled.search(part):
                names[part] = names.get(part, 0) + 1
    ordered = sorted(names, key=lambda k: -names[k])
    return ordered[:limit], int(hit.sum())


def hard_filter(corpus, profile, slot, slot_target=None, used_counts=None,
                profile_mask=None, profile_report=None, side=False):
    """Admissible candidates for one slot, as mains or as accompaniments.

    Combines the user-dependent rules with the three that vary within a plan:
    the slot itself, the clinical ceilings, which bind on the quantity the plan
    asks the user to eat and so depend on the slot's serving count, and the
    repetition bound of Section 3.6.5.

    `used_counts` maps a recipe id to the number of times it already appears in
    the week.  A main is barred once it reaches the user's repetition limit; an
    accompaniment is barred after one appearance, so that a repeated main is
    always served in different company.
    """
    if profile_mask is None:
        profile_mask, profile_report = profile_filter(corpus, profile)
    report = dict(profile_report or {})

    mask = (corpus.side_slot[slot] if side else corpus.slot[slot]).copy()
    report["slot candidates"] = int(mask.sum())

    before = int(mask.sum())
    mask &= profile_mask
    if before - int(mask.sum()):
        report["removed by restrictions"] = before - int(mask.sum())

    # Clinical ceilings, on the served quantity rather than on one serving.
    if slot_target is not None and (profile.max_sodium_mg is not None
                                    or profile.max_sugar_g is not None):
        servings = servings_for(corpus.calories, slot_target["energy_kcal"])
        if profile.max_sodium_mg is not None:
            before = int(mask.sum())
            mask &= (servings * corpus.sodium_mg) <= profile.max_sodium_mg
            if before - int(mask.sum()):
                report[f"sodium above {profile.max_sodium_mg:.0f} mg as served"] = \
                    before - int(mask.sum())
        if profile.max_sugar_g is not None:
            before = int(mask.sum())
            mask &= (servings * corpus.sugar_g) <= profile.max_sugar_g
            if before - int(mask.sum()):
                report[f"sugar above {profile.max_sugar_g:.0f} g as served"] = \
                    before - int(mask.sum())

    limit = 1 if side else max(1, getattr(profile, "max_repeats",
                                          DEFAULT_MAX_REPEATS))
    rows = [corpus.row_of[r] for r, n in (used_counts or {}).items()
            if n >= limit and r in corpus.row_of]
    if rows:
        exhausted = np.zeros(corpus.n, dtype=bool)
        exhausted[rows] = True
        before = int(mask.sum())
        mask &= ~exhausted
        if before - int(mask.sum()):
            label = ("already served this week" if side
                     else f"already served {limit} time(s) this week")
            report[label] = before - int(mask.sum())

    report["admissible"] = int(mask.sum())
    return mask, report


# ---------------------------------------------------------------------------
# Soft constraints (§3.5.2)
# ---------------------------------------------------------------------------

def used_ingredient_vector(corpus, recipe_ids):
    """Indicator over the ingredient vocabulary for a set of placed recipes."""
    vec = np.zeros(corpus.ingr_matrix.shape[1], dtype=np.float64)
    rows = [corpus.row_of[r] for r in recipe_ids if r in corpus.row_of]
    if rows:
        used = np.asarray(corpus.ingr_matrix[rows].sum(axis=0)).ravel()
        vec[used > 0] = 1.0
    return vec


def servings_for(calories, target_kcal):
    """Servings of a recipe that come closest to a slot's energy target.

    Rounded to the nearest half serving and clipped to [MIN_SERVINGS,
    MAX_SERVINGS].  The residual error left by the rounding is carried by the
    energy penalty like any other deviation, so a recipe whose serving size
    happens to divide the target well is preferred over one that does not.
    """
    with np.errstate(divide="ignore", invalid="ignore"):
        raw = np.where(calories > 0, target_kcal / np.maximum(calories, 1e-6), 1.0)
    stepped = np.round(raw / SERVING_STEP) * SERVING_STEP
    return np.clip(stepped, MIN_SERVINGS, MAX_SERVINGS)


def slot_allowance(daily, consumed, share_of_remaining, scale=1.0):
    """What this slot may still contribute, given what the day has had already.

    The first implementation gave every slot a fixed share of the daily figures
    regardless of what the earlier slots had actually supplied, so an excess at
    breakfast was never recovered and the day's errors compounded.  Here the
    slot is scored against the daily figure minus what is already on the plate:
    a heavy breakfast tightens lunch and dinner automatically.

    `share_of_remaining` is this slot's share of what is left, computed from the
    proportions of Section 3.6.1 restricted to the slots still to be filled, so
    the 25/35/40 split is preserved in relative terms.  `scale` narrows the
    result to the part the main dish is expected to carry (MAIN_SHARE);
    accompaniments are scored against the whole of what remains.
    """
    return {key: max(total - consumed.get(key, 0.0), 0.0)
                 * share_of_remaining * scale
            for key, total in daily.items()}


def soft_penalties(corpus, profile, slot_target, day_index, plan_ids):
    """The four penalty terms of Section 3.5.2, each over the whole corpus.

    E   absolute relative deviation of energy from the slot allowance
    M   mean nutritional error over the nutrients of TARGET_NUTRIENTS and
        CEILING_NUTRIENTS: deviation in either direction for a quantity the
        guidance sets as a target, exceedance only for one it sets as a ceiling
    D   proportion of the recipe's ingredients already appearing in the plan
    T   exceedance of the day's preparation-time budget, as a proportion of it,
        floored at zero so that quick recipes are not rewarded without limit

    E and M are evaluated on the served quantity, that is on the recipe scaled
    by the serving count returned alongside the penalties, for the reason given
    at MAX_SERVINGS.  D and T are properties of the recipe itself and do not
    scale: cooking a second portion neither adds ingredients nor doubles the
    preparation time.

    `slot_target` is what this slot may still contribute, normally produced by
    slot_allowance() so that the term reflects the day as it stands rather than
    a fixed share of it.
    """
    target_kcal = max(slot_target["energy_kcal"], 1.0)
    servings = servings_for(corpus.calories, target_kcal)
    energy = np.abs(servings * corpus.calories - target_kcal) / target_kcal

    # The two kinds of error are averaged within their own group and then added,
    # not averaged together.  Pooling all six would let a satisfied ceiling
    # dilute a violated one: sodium at twice its limit contributes 1.0 to its
    # own group but only 0.17 to a six-way mean, which is how the first version
    # came to run at nearly four times the sodium ceiling while the term it was
    # minimising looked small.
    deviation = np.mean([
        np.abs(servings * corpus.macros[m] - max(slot_target.get(m, 0.0), 1e-6))
        / max(slot_target.get(m, 0.0), 1e-6)
        for m in TARGET_NUTRIENTS], axis=0)
    exceedance = np.mean([
        np.maximum(servings * corpus.macros[m]
                   - max(slot_target.get(m, 0.0), 1e-6), 0.0)
        / max(slot_target.get(m, 0.0), 1e-6)
        for m in CEILING_NUTRIENTS], axis=0)
    macros = deviation + CEILING_EMPHASIS * exceedance

    used = used_ingredient_vector(corpus, plan_ids)
    repetition = (corpus.ingr_matrix @ used) / corpus.ingr_count

    budget = max(profile.time_budget(day_index), 1.0)
    time_over = np.maximum(corpus.minutes - budget, 0.0) / budget

    return {"energy": energy, "macros": macros,
            "repetition": repetition, "time": time_over,
            "servings": servings}


def normalise_relevance(scores, mask):
    """Scale relevance to the unit interval over the admissible set only.

    Section 3.5.2 requires rel in [0, 1] so that the weights are comparable.
    Doing it over the admissible set rather than the whole corpus keeps the
    scale meaningful after a filter has removed most of the candidates.
    """
    out = np.zeros_like(scores)
    if not mask.any():
        return out
    vals = scores[mask]
    lo, hi = float(vals.min()), float(vals.max())
    out[mask] = 0.5 if hi <= lo else (vals - lo) / (hi - lo)
    return out


def combine(relevance, penalties, weights=None):
    """score(r) = a.rel - b.E - c.M - d.D - e.T

    An additive sum of named terms rather than a single opaque prediction, so
    that each contribution can be displayed alongside the recommendation.
    """
    w = weights or WEIGHTS
    return (w["relevance"] * relevance
            - w["energy"] * penalties["energy"]
            - w["macros"] * penalties["macros"]
            - w["repetition"] * penalties["repetition"]
            - w["time"] * penalties["time"])


def contributions(relevance, penalties, row, weights=None):
    """The scoring terms for one recipe, for display (requirement N2)."""
    w = weights or WEIGHTS
    return {
        "relevance": w["relevance"] * float(relevance[row]),
        "energy": -w["energy"] * float(penalties["energy"][row]),
        "macros": -w["macros"] * float(penalties["macros"][row]),
        "repetition": -w["repetition"] * float(penalties["repetition"][row]),
        "time": -w["time"] * float(penalties["time"][row]),
    }


# ---------------------------------------------------------------------------
# Adaptive relaxation (§3.5.3)
# ---------------------------------------------------------------------------

def soft_admissible(penalties, level, gates=None):
    """Candidates acceptable for a slot after `level` steps of relaxation.

    A gate that has been relaxed is dropped entirely rather than widened, which
    is what makes the relaxation monotone: the admissible set can only grow.
    """
    gates = gates or SOFT_GATES
    surrendered = set(RELAXATION_ORDER[:level])
    mask = None
    for term, limit in gates.items():
        if term in surrendered:
            continue
        ok = penalties[term] <= limit
        mask = ok if mask is None else (mask & ok)
    return mask if mask is not None else np.ones_like(
        penalties["energy"], dtype=bool)


def relaxed_weights(level, weights=None):
    """Weights after `level` steps of relaxation.

    Each step surrenders one soft term by setting its weight to zero, in the
    order of RELAXATION_ORDER.  Every step widens the admissible set without
    touching the filter, because the filter does not consult these weights at
    all -- which is the structural reason a relaxation cannot reach an allergen
    rule even by mistake.
    """
    w = dict(weights or WEIGHTS)
    for term in RELAXATION_ORDER[:level]:
        w[term] = 0.0
    return w


def relaxation_note(level):
    """A description of what has been given up, for the interface."""
    if level <= 0:
        return ""
    given_up = RELAXATION_ORDER[:level]
    names = {"time": "the preparation-time budget",
             "repetition": "the repetition penalty",
             "macros": "the macronutrient target",
             "energy": "the energy target"}
    return "relaxed " + ", then ".join(names[t] for t in given_up)


MAX_RELAXATION = len(RELAXATION_ORDER)
