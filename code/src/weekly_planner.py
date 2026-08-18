"""Weekly plan generation.

Implements Section 3.6 of the dissertation, following Algorithm 3.1 line by
line: slots are filled greedily in day order, a look-ahead term corrects the
defect that a purely greedy rule has here, and any slot left unfilled is retried
under adaptive relaxation of the soft constraints only.

The procedure is deterministic given a profile, which matters for Chapter 5.
"""

import os
import sys
from collections import Counter

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import constraints as C  # noqa: E402
from user_model import SLOT_SHARE, daily_targets  # noqa: E402

DAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
        "Saturday", "Sunday")
SLOTS = ("breakfast", "lunch", "dinner")

# Line 10 of Algorithm 3.1: the look-ahead is evaluated only on the k
# highest-scoring candidates, which keeps the cost of a slot linear in the size
# of the filtered candidate set rather than quadratic.
LOOKAHEAD_K = 50

# How many ranked candidates are retained per slot to serve replacements
# (§3.6.3).  The design says the whole ranked list is kept; in practice it is
# truncated here, because a user will not press replace two hundred times and
# holding 103,389 dinner candidates for each of seven days is not worth the
# memory.  Chapter 4 records the truncation.
CANDIDATE_LIST_SIZE = 200

# Weight on the look-ahead term.  Comparable to the energy weight of Section
# 3.5.2, since it expresses the same quantity -- energy feasibility -- one slot
# further ahead.
LOOKAHEAD_WEIGHT = 0.4

# Weight on preference when choosing an accompaniment.  Below the weight a main
# dish carries, because the accompaniment's job is to complete the plate
# nutritionally and a user chooses a meal by its main dish; but not zero,
# because a side the user dislikes is still a side they will not cook.
SIDE_RELEVANCE_WEIGHT = 0.4

# Allowance on the daily energy target used by the look-ahead feasibility test.
DAILY_TOLERANCE = 0.10


class Dish:
    """One recipe at one serving size, as it appears on a plate."""

    def __init__(self, row, corpus, df, servings=1.0, is_side=False):
        record = df.iloc[row]
        self.row = int(row)
        self.recipe_id = int(record["id"])
        self.name = str(record["name"])
        self.minutes = int(record["minutes"])
        self.servings = float(servings)
        self.per_serving_calories = float(record["calories"])
        self.calories = self.servings * float(record["calories"])
        self.protein_g = self.servings * float(record["protein_g"])
        self.fat_g = self.servings * float(record["fat_g"])
        self.carbs_g = self.servings * float(record["carbs_g"])
        self.sodium_mg = self.servings * float(record["sodium_mg"])
        self.sugar_g = self.servings * float(record["sugar_g"])
        self.satfat_g = self.servings * float(record["satfat_g"])
        self.ingredients = list(record["ingredients"])
        self.allergens = sorted(
            cls for cls, col in corpus.allergen.items() if col[row])
        self.has_unmappable = bool(corpus.has_unmappable[row])
        self.is_side = is_side

    def __repr__(self):
        return f"<{self.name} x{self.servings:g} ({self.calories:.0f} kcal)>"


class Meal:
    """One filled slot: a main dish and the accompaniments served beside it.

    The nutritional attributes are the totals across every dish on the plate,
    since that is what the user eats and what the targets of Section 3.3.2 are
    compared against.
    """

    def __init__(self, day_index, slot, main, sides=(), terms=None,
                 relaxation=0):
        self.day_index = day_index
        self.day = DAYS[day_index]
        self.slot = slot
        self.main = main
        self.sides = list(sides)
        self.terms = terms or {}
        self.relaxation = relaxation

    @property
    def dishes(self):
        return [self.main] + self.sides

    # -- the plate, not the main dish ------------------------------------
    @property
    def calories(self):
        return sum(d.calories for d in self.dishes)

    @property
    def protein_g(self):
        return sum(d.protein_g for d in self.dishes)

    @property
    def fat_g(self):
        return sum(d.fat_g for d in self.dishes)

    @property
    def carbs_g(self):
        return sum(d.carbs_g for d in self.dishes)

    @property
    def sodium_mg(self):
        return sum(d.sodium_mg for d in self.dishes)

    @property
    def sugar_g(self):
        return sum(d.sugar_g for d in self.dishes)

    @property
    def satfat_g(self):
        return sum(d.satfat_g for d in self.dishes)

    @property
    def minutes(self):
        return sum(d.minutes for d in self.dishes)

    @property
    def allergens(self):
        """Every allergen class flagged anywhere on the plate.

        Unioned across the dishes rather than taken from the main, because an
        accompaniment can carry an allergen the main does not and the card must
        say so.
        """
        return sorted({a for d in self.dishes for a in d.allergens})

    @property
    def has_unmappable(self):
        return any(d.has_unmappable for d in self.dishes)

    @property
    def ingredients(self):
        return [i for d in self.dishes for i in d.ingredients]

    @property
    def name(self):
        return self.main.name

    @property
    def row(self):
        return self.main.row

    @property
    def recipe_id(self):
        return self.main.recipe_id

    def recipe_ids(self):
        return [d.recipe_id for d in self.dishes]

    def __repr__(self):
        extra = f" + {len(self.sides)} side(s)" if self.sides else ""
        return (f"<{self.day} {self.slot}: {self.main.name}{extra} "
                f"({self.calories:.0f} kcal)>")


class WeeklyPlan:
    """Twenty-one slots, the candidate lists behind them, and any gaps."""

    def __init__(self, profile, daily):
        self.profile = profile
        self.daily = daily
        self.meals = {}         # (day_index, slot) -> Meal
        self.candidates = {}    # (day_index, slot) -> list of row indices
        self.unfilled = {}      # (day_index, slot) -> reason
        self.locked = set()     # slots the user pinned, carried across rebuilds
        self.mode = ""          # which recommender served this plan

    def meal(self, day_index, slot):
        return self.meals.get((day_index, slot))

    def used_counts(self, exclude=None):
        """How many times each recipe already appears, mains and sides alike."""
        counts = Counter()
        for key, meal in self.meals.items():
            if key == exclude:
                continue
            counts.update(meal.recipe_ids())
        return counts

    def placed_ids(self, exclude=None):
        return [rid for key, m in self.meals.items() if key != exclude
                for rid in m.recipe_ids()]

    def day_meals(self, day_index):
        return [self.meals[(day_index, s)] for s in SLOTS
                if (day_index, s) in self.meals]

    def day_totals(self, day_index):
        meals = self.day_meals(day_index)
        return {
            "energy_kcal": sum(m.calories for m in meals),
            "protein_g": sum(m.protein_g for m in meals),
            "fat_g": sum(m.fat_g for m in meals),
            "carbs_g": sum(m.carbs_g for m in meals),
            "sodium_mg": sum(m.sodium_mg for m in meals),
            "sugar_g": sum(m.sugar_g for m in meals),
        }

    def is_complete(self):
        return len(self.meals) == len(DAYS) * len(SLOTS)


# ---------------------------------------------------------------------------
# Look-ahead (§3.6.2)
# ---------------------------------------------------------------------------

def look_ahead(corpus, rows, day_index, slot, plan, daily, servings,
               slot_kcal):
    """Penalty for candidates that would leave the rest of the day infeasible.

    Choosing the highest-scoring breakfast may consume so much of the day's
    energy allowance that no acceptable lunch or dinner remains.  For each
    candidate this estimates the energy still available after placing it, and
    compares that with what the day's remaining slots need.  The shortfall,
    expressed as a proportion of what is needed, is the penalty.

    For the last slot of a day nothing remains to be fed, so the term is zero
    and the energy penalty of Section 3.5.2 governs alone.
    """
    # Only slots that are still empty need feeding.  A slot the user has locked
    # already holds a real meal whose energy is counted in `used` below, so
    # asking for its target as well would charge the day's allowance twice and
    # reject candidates that are in fact affordable.
    remaining = [s for s in SLOTS[SLOTS.index(slot) + 1:]
                 if plan.meal(day_index, s) is None]
    if not remaining:
        return np.zeros(len(rows), dtype=np.float64)

    needed = sum(SLOT_SHARE[s] for s in remaining) * daily["energy_kcal"]
    used = sum(m.calories for m in plan.day_meals(day_index))
    budget = daily["energy_kcal"] * (1.0 + DAILY_TOLERANCE)
    # What the plate will supply, not what the main dish supplies: a main below
    # the slot target is topped up by accompaniments to roughly that target,
    # while one above it is served alone.
    plate = np.maximum(servings[rows] * corpus.calories[rows], slot_kcal)
    residual = budget - used - plate
    shortfall = np.maximum(needed - residual, 0.0) / max(needed, 1.0)
    return -LOOKAHEAD_WEIGHT * shortfall


# ---------------------------------------------------------------------------
# Filling one slot (Algorithm 3.1, lines 4-12)
# ---------------------------------------------------------------------------

def choose_sides(corpus, df, profile, plan, day_index, slot, relevance,
                 profile_mask, profile_report, main, extra_used=()):
    """Accompaniments that carry the plate towards the whole of its allowance.

    Chosen one at a time against everything the slot still has room for, not
    against its energy alone.  An earlier version scored accompaniments purely
    on how nearly they closed the energy gap, which is why plans hit the energy
    target to within a per cent while running to nearly four times the sodium
    ceiling, and why a single day could carry three tomato-and-bread dishes: the
    selection saw neither the guideline ceilings nor the repetition penalty.

    The hard filter applies to accompaniments exactly as it does to mains: an
    allergen on a side dish is as dangerous as one on a main, so nothing here is
    exempt from it.
    """
    used = plan.used_counts()
    used.update(extra_used)
    used.update([main.recipe_id])
    share = remaining_share(plan, day_index, slot)
    consumed = day_consumed(plan, day_index)

    sides = []
    for _ in range(C.MAX_SIDES):
        placed = [main] + sides
        # What the plate may still take: the slot's allowance less the dishes
        # already on it.
        allowance = C.slot_allowance(plan.daily, consumed, share)
        for dish in placed:
            allowance["energy_kcal"] -= dish.calories
            allowance["protein_g"] -= dish.protein_g
            allowance["fat_g"] -= dish.fat_g
            allowance["carbs_g"] -= dish.carbs_g
            allowance["satfat_g"] -= dish.satfat_g
            allowance["sugar_g"] -= dish.sugar_g
            allowance["sodium_mg"] -= dish.sodium_mg
        gap = allowance["energy_kcal"]
        if gap < C.MIN_GAP_FOR_SIDE:
            break
        allowance = {k: max(v, 1e-6) for k, v in allowance.items()}

        mask, _ = C.hard_filter(
            corpus, profile, slot, slot_target=None, used_counts=used,
            profile_mask=profile_mask, profile_report=profile_report,
            side=True)

        # A clinical ceiling binds on the plate, not on the main dish alone: a
        # sodium limit already met by the main leaves no room for a salted side.
        # The ceiling is a hard constraint and the energy target a soft one, so
        # where they conflict the plate goes short of energy rather than over
        # the limit.
        servings = C.servings_for(corpus.calories, gap)
        if profile.max_sodium_mg is not None:
            spare = profile.max_sodium_mg - sum(d.sodium_mg for d in placed)
            mask &= (servings * corpus.sodium_mg) <= spare
        if profile.max_sugar_g is not None:
            spare = profile.max_sugar_g - sum(d.sugar_g for d in placed)
            mask &= (servings * corpus.sugar_g) <= spare
        if not mask.any():
            break

        # Scored with the same terms as a main dish, against what the plate has
        # room for, so an accompaniment that fits the energy gap but blows the
        # sodium ceiling loses to one that fits both.
        penalties = C.soft_penalties(corpus, profile, allowance, day_index,
                                     plan.placed_ids() + [d.recipe_id
                                                          for d in placed])
        score = C.combine(SIDE_RELEVANCE_WEIGHT * relevance, penalties)
        score = np.where(mask, score, -np.inf)

        row = int(np.argmax(score))
        if not np.isfinite(score[row]):
            break
        side = Dish(row, corpus, df, servings=float(penalties["servings"][row]),
                    is_side=True)

        # Only if it helps, and only if it is worth cooking: a dish that
        # overshoots by more than the gap it fills makes the plate worse, and a
        # token portion is not worth a fourth pan.
        if side.calories < C.MIN_SIDE_KCAL or abs(gap - side.calories) >= gap:
            break
        sides.append(side)
        used.update([side.recipe_id])

    return sides


def remaining_share(plan, day_index, slot):
    """This slot's share of what is left of the day, per Section 3.6.1.

    The 25/35/40 proportions are renormalised over the slots still to be filled,
    so a day with breakfast already placed splits the remainder between lunch
    and dinner in their original ratio rather than in the original absolute
    amounts.
    """
    open_slots = [s for s in SLOTS
                  if s == slot or plan.meal(day_index, s) is None]
    total = sum(SLOT_SHARE[s] for s in open_slots) or 1.0
    return SLOT_SHARE[slot] / total


def day_consumed(plan, day_index, exclude_slot=None):
    """Everything already on the day's plates, by nutrient."""
    keys = ("energy_kcal", "protein_g", "fat_g", "carbs_g", "satfat_g",
            "sugar_g", "sodium_mg")
    out = dict.fromkeys(keys, 0.0)
    for meal in plan.day_meals(day_index):
        if meal.slot == exclude_slot:
            continue
        out["energy_kcal"] += meal.calories
        out["protein_g"] += meal.protein_g
        out["fat_g"] += meal.fat_g
        out["carbs_g"] += meal.carbs_g
        out["sugar_g"] += meal.sugar_g
        out["sodium_mg"] += meal.sodium_mg
        out["satfat_g"] += meal.satfat_g
    return out


def _fill_slot(corpus, df, profile, plan, day_index, slot, relevance,
               profile_mask, profile_report, level=0):
    """Choose a main and its accompaniments for one slot, or explain why not."""
    daily = plan.daily
    target = C.slot_allowance(daily, day_consumed(plan, day_index),
                              remaining_share(plan, day_index, slot))

    # lines 4-5: candidates for the slot, then the hard filter
    mask, report = C.hard_filter(
        corpus, profile, slot, slot_target=target,
        used_counts=plan.used_counts(),
        profile_mask=profile_mask, profile_report=profile_report)

    # lines 6-7
    if not mask.any():
        return None, report

    # line 9: base score over the admissible set.  The main is scored against
    # its share of the slot, not the whole of it, because accompaniments supply
    # the remainder (Section 3.6.1).
    main_target = {k: v * C.MAIN_SHARE for k, v in target.items()}
    penalties = C.soft_penalties(corpus, profile, main_target, day_index,
                                 plan.placed_ids())
    gate = C.soft_admissible(penalties, level)
    admissible = mask & gate
    if not admissible.any():
        report["outside the soft tolerances"] = int(mask.sum())
        return None, report

    weights = C.relaxed_weights(level)
    rel = C.normalise_relevance(relevance, admissible)
    base = C.combine(rel, penalties, weights)
    base = np.where(admissible, base, -np.inf)

    # line 10: the k highest-scoring candidates
    k = min(LOOKAHEAD_K, int(admissible.sum()))
    top = np.argpartition(base, -k)[-k:]
    top = top[np.argsort(base[top])[::-1]]

    # line 11: the look-ahead decides among them
    final = base[top] + look_ahead(corpus, top, day_index, slot, plan, daily,
                                   penalties["servings"],
                                   target["energy_kcal"])
    chosen = top[int(np.argmax(final))]

    # The ranked list kept for replacements (§3.6.3).  Ranked by base score, so
    # that a replacement follows the user's preference order; the look-ahead is
    # re-applied at replacement time rather than baked in here, because it
    # depends on what the rest of the day looks like by then.
    pool = min(CANDIDATE_LIST_SIZE, int(admissible.sum()))
    ranked = np.argpartition(base, -pool)[-pool:]
    ranked = ranked[np.argsort(base[ranked])[::-1]]
    plan.candidates[(day_index, slot)] = [int(r) for r in ranked]

    terms = C.contributions(rel, penalties, chosen, weights)
    terms["look-ahead"] = float(final[int(np.argmax(final))] - base[chosen])

    main = Dish(int(chosen), corpus, df,
                servings=float(penalties["servings"][chosen]))
    sides = choose_sides(corpus, df, profile, plan, day_index, slot, relevance,
                         profile_mask, profile_report, main)
    return Meal(day_index, slot, main, sides, terms, level), report


# ---------------------------------------------------------------------------
# Algorithm 3.1
# ---------------------------------------------------------------------------

def plan_week(corpus, df, profile, controller, keep=None):
    """Build a seven-day plan.  Algorithm 3.1 of the dissertation.

    `keep` maps a slot to a Meal the user has locked.  Locked slots are placed
    before the loop runs, so their recipes count towards the repetition bound
    and their energy towards the day, and the loop skips them.  A user who
    likes three of the week's meals can therefore regenerate the rest without
    losing them, which is what makes the plan something to refine rather than
    something to accept or discard whole.
    """
    daily = daily_targets(profile)
    plan = WeeklyPlan(profile, daily)                       # line 1
    if keep:
        plan.meals.update(keep)
        plan.locked = set(keep)

    recommender, mode = controller.select(profile)
    plan.mode = mode
    relevance = recommender.scores(profile)

    profile_mask, profile_report = C.profile_filter(corpus, profile)

    for day_index in range(len(DAYS)):                      # line 2
        for slot in SLOTS:                                  # line 3
            if (day_index, slot) in plan.meals:
                continue
            meal, report = _fill_slot(
                corpus, df, profile, plan, day_index, slot, relevance,
                profile_mask, profile_report)
            if meal is None:                                # lines 6-7
                plan.unfilled[(day_index, slot)] = report
            else:
                plan.meals[(day_index, slot)] = meal        # line 12

    if plan.unfilled:                                       # lines 13-14
        adaptive_relax(corpus, df, profile, plan, relevance,
                       profile_mask, profile_report)

    return plan                                             # line 15


def adaptive_relax(corpus, df, profile, plan, relevance,
                   profile_mask, profile_report):
    """Retry unfilled slots, surrendering soft constraints one at a time.

    Hard constraints are never relaxed, and allergen filters in particular are
    never relaxed under any circumstance, including the case where relaxing them
    is the only way to return a complete plan.  Structurally this is guaranteed
    rather than promised: relaxation only changes the weights and gates passed
    to the soft stage, and the hard filter does not read either.

    A slot that remains unfilled after every relaxation stays unfilled.
    Returning a week with a gap in it, and saying which slot and why, is a worse
    user experience than returning a full one and the correct behaviour: the
    alternative is to present a meal the system has reason to believe the user
    cannot safely eat.
    """
    for (day_index, slot) in list(plan.unfilled):
        for level in range(1, C.MAX_RELAXATION + 1):
            meal, report = _fill_slot(
                corpus, df, profile, plan, day_index, slot, relevance,
                profile_mask, profile_report, level=level)
            if meal is not None:
                plan.meals[(day_index, slot)] = meal
                del plan.unfilled[(day_index, slot)]
                break
            plan.unfilled[(day_index, slot)] = report


# ---------------------------------------------------------------------------
# Replacing a meal (§3.6.3)
# ---------------------------------------------------------------------------

def _slot_context(corpus, profile, plan, day_index, slot):
    """Everything needed to judge a candidate for a slot already in the plan.

    Shared by every route that changes a filled slot -- the replace control, the
    alternatives list and the direct pick -- so that all three apply the same
    hard filter and the same feasibility test.  A candidate offered in the
    alternatives list must be one the replace control would also accept, or the
    interface would be showing options that cannot be taken.
    """
    key = (day_index, slot)
    if key not in plan.meals:
        return None
    profile_mask, profile_report = C.profile_filter(corpus, profile)
    daily = plan.daily
    # The slot being edited is excluded from what the day has consumed, so the
    # candidate is judged against the room its predecessor was occupying.
    target = C.slot_allowance(daily, day_consumed(plan, day_index, slot),
                              remaining_share(plan, day_index, slot))
    mask, _ = C.hard_filter(corpus, profile, slot, slot_target=target,
                            used_counts=plan.used_counts(exclude=key),
                            profile_mask=profile_mask,
                            profile_report=profile_report)
    others = [m for m in plan.day_meals(day_index) if m.slot != slot]

    # The look-ahead test of Section 3.6.2, restated for the case where the rest
    # of the day is already filled.  During planning it asks whether the slots
    # still to come can be fed from what is left; here those slots hold real
    # meals whose energy is already in `used`, so the question is whether the
    # day still closes within budget once the candidate is served.  Only slots
    # that are still empty reserve anything.
    unfilled_share = sum(SLOT_SHARE[s] for s in SLOTS
                         if s != slot and not any(m.slot == s for m in others))
    return {
        "mask": mask,
        "servings": C.servings_for(corpus.calories, target["energy_kcal"]),
        "used": sum(m.calories for m in others),
        "reserved": unfilled_share * daily["energy_kcal"],
        "budget": daily["energy_kcal"] * (1.0 + DAILY_TOLERANCE),
        "target": target,
        "others": others,
        "profile_mask": profile_mask,
        "profile_report": profile_report,
    }


def _affordable(corpus, ctx, row):
    """Whether serving this candidate still lets the day close within budget."""
    plate = max(ctx["servings"][row] * corpus.calories[row],
                ctx["target"]["energy_kcal"])
    return ctx["used"] + plate + ctx["reserved"] <= ctx["budget"]


def _place(corpus, df, profile, plan, day_index, slot, row, recommender, ctx):
    """Put a chosen main into a filled slot and re-choose its accompaniments."""
    key = (day_index, slot)
    current = plan.meals[key]
    target, others = ctx["target"], ctx["others"]

    # Record the rejection before the swap, so the signal survives it.
    profile.rejected.append(current.recipe_id)
    scores = (recommender.scores(profile) if recommender
              else np.zeros(corpus.n))
    main_target = {k: v * C.MAIN_SHARE for k, v in target.items()}
    penalties = C.soft_penalties(corpus, profile, main_target, day_index,
                                 [r for m in others for r in m.recipe_ids()])
    rel = C.normalise_relevance(scores, ctx["mask"])
    terms = C.contributions(rel, penalties, row)

    main = Dish(row, corpus, df, servings=float(penalties["servings"][row]))
    # The slot is dropped from the plan first, so its old accompaniments are
    # free to be reused elsewhere and cannot block the new ones through the
    # no-repeat rule.
    del plan.meals[key]
    sides = choose_sides(corpus, df, profile, plan, day_index, slot, scores,
                         ctx["profile_mask"], ctx["profile_report"], main)
    plan.meals[key] = Meal(day_index, slot, main, sides, terms,
                           current.relaxation)
    extra = f" plus {len(sides)} side(s)" if sides else ""
    return True, f"Now serving {main.name}{extra}."


def alternatives(corpus, df, profile, plan, day_index, slot, limit=6):
    """The next few candidates for a slot, for the user to choose among.

    Section 3.6.3 gives the user one control that swaps in the next candidate.
    Offering the list instead lets them choose rather than cycle, which is what
    a user asked for: a plan is only adjustable in a useful sense if you can see
    what you are adjusting it to.  Only candidates that pass both tests are
    returned, so nothing shown here can be refused when clicked.
    """
    ctx = _slot_context(corpus, profile, plan, day_index, slot)
    if ctx is None:
        return []
    current = plan.meals[(day_index, slot)]
    out = []
    for row in plan.candidates.get((day_index, slot), []):
        if row == current.row or not ctx["mask"][row]:
            continue
        if not _affordable(corpus, ctx, row):
            continue
        record = df.iloc[row]
        out.append({
            "row": int(row),
            "name": str(record["name"]),
            "calories": float(ctx["servings"][row] * record["calories"]),
            "minutes": int(record["minutes"]),
            "tokens": list(record["doc_tokens"]),
        })
        if len(out) >= limit:
            break
    return out


def choose_alternative(corpus, df, profile, plan, day_index, slot, row,
                       recommender=None):
    """Swap in a specific candidate the user picked from the alternatives list.

    The checks are re-run rather than trusted: the list the user is looking at
    may have been built before an earlier edit changed what the day can afford.
    """
    ctx = _slot_context(corpus, profile, plan, day_index, slot)
    if ctx is None:
        return False, "This slot is empty."
    if not ctx["mask"][row]:
        return False, ("That recipe is no longer admissible under your "
                       "restrictions. The meal has been left unchanged.")
    if not _affordable(corpus, ctx, row):
        return False, (f"That recipe would leave too little energy for the "
                       f"rest of {DAYS[day_index]}. The meal has been left "
                       f"unchanged.")
    return _place(corpus, df, profile, plan, day_index, slot, row,
                  recommender, ctx)


def replace_meal(corpus, df, profile, plan, day_index, slot, recommender=None):
    """Swap the main dish for the next viable candidate, and re-choose its sides.

    A replacement is not simply the next-highest score.  The candidate must
    still pass the hard filter, which is re-applied rather than assumed, and it
    must still leave the remaining slots of that day feasible under the
    look-ahead test.  Without the second check a user could exhaust the day's
    energy budget by repeatedly replacing breakfast, leaving the planner unable
    to fill the evening.

    The accompaniments are chosen afresh for the new main rather than carried
    over, because they exist to close the gap between that main and the slot
    target, and a different main leaves a different gap.

    Each rejection is also information: the replaced recipe is recorded as a
    negative preference signal and fed back into the user model, so that a user
    who rejects three fish dishes stops being offered them.

    Returns (ok, message).
    """
    ctx = _slot_context(corpus, profile, plan, day_index, slot)
    if ctx is None:
        return False, "This slot is empty, so there is nothing to replace."
    key = (day_index, slot)
    current = plan.meals[key]
    ranked = plan.candidates.get(key, [])

    # Advance past the recipe on screen, so that pressing replace repeatedly
    # walks down the list rather than returning to the top.
    try:
        start = ranked.index(current.row) + 1
    except ValueError:
        start = 0

    blocked_by_filter = 0
    blocked_by_lookahead = 0
    for row in ranked[start:]:
        if not ctx["mask"][row]:
            blocked_by_filter += 1
            continue
        if not _affordable(corpus, ctx, row):
            blocked_by_lookahead += 1
            continue

        return _place(corpus, df, profile, plan, day_index, slot, row,
                      recommender, ctx)

    reasons = []
    if blocked_by_filter:
        reasons.append(f"{blocked_by_filter} failed your restrictions")
    if blocked_by_lookahead:
        reasons.append(f"{blocked_by_lookahead} would leave too little energy "
                       f"for the rest of {DAYS[day_index]}")
    detail = "; ".join(reasons) if reasons else "the candidate list is exhausted"
    return False, (f"No replacement available for this slot ({detail}). "
                   f"The meal has been left unchanged.")
