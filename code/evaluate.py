"""Evaluation experiments for Chapter 5.

Everything Chapter 5 reports is produced here, written to outputs/eval_*.json
so that a number in the chapter can be traced to the run that produced it, and
to outputs/eval_*.md as tables ready to read.

WHAT THE DATA FORCES, and why the experiments are shaped the way they are.

Two properties of this corpus decide the design of every ranking experiment
below, and both are reported in Chapter 5 rather than worked around:

  *  The median user has ONE interaction.  Only 5.6 per cent have ten or more.
     A top-N experiment therefore cannot be run over "users" in general; it is
     run over the minority with enough history to hold anything out, and the
     result describes that minority.

  *  88.9 per cent of ratings are four or five stars.  Precision@K is
     consequently high for almost any ranking, including a bad one, so an
     absolute figure means nothing on its own.  Every ranking result is
     reported beside a random and a popularity baseline, which is the only way
     to read it.

THE LEAKAGE TRAP.  outputs/mf.pkl is trained on every interaction, so scoring
held-out items with it would be scoring data the model has already seen.  The
top-N experiment therefore retrains the factorisation from scratch on the
training split alone (about four minutes).  This is the single easiest mistake
to make here and the hardest to notice afterwards, because the only symptom is
that the numbers are too good.

Run:  python code/evaluate.py                 (all experiments)
      python code/evaluate.py rank nutrition  (a subset, by name)
"""

import json
import os
import pickle
import sys
import time
from collections import Counter

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "outputs")
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "src"))

import constraints as C            # noqa: E402
import weekly_planner as W         # noqa: E402
from recommenders import (CollaborativeRecommender, ContentRecommender,  # noqa: E402
                          SwitchingController, load_content_index,
                          train_matrix_factorisation)
from user_model import PAL, Profile, daily_targets   # noqa: E402

SEED = 20260817
KS = (5, 10, 20)
N_EVAL_USERS = 2000
MIN_INTERACTIONS = 10
MIN_POSITIVES = 5
POSITIVE = 4.0          # a rating of four or five is a positive
HOLDOUT = 0.2
N_COVERAGE = 30         # plans generated for the coverage measurement

results = {}


def log(msg=""):
    print(msg, flush=True)


def section(n, title):
    log()
    log("=" * 70)
    log(f"{n}. {title}")
    log("=" * 70)


def save(name, payload):
    path = os.path.join(OUT, f"eval_{name}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, default=float)
    log(f"   -> outputs/eval_{name}.json")


# ---------------------------------------------------------------------------
# Shared data
# ---------------------------------------------------------------------------
log("loading corpus, index and interactions ...")
t0 = time.time()
with open(os.path.join(OUT, "corpus.pkl"), "rb") as f:
    df = pickle.load(f)
with open(os.path.join(OUT, "interactions.pkl"), "rb") as f:
    inter = pickle.load(f)
index = load_content_index()
corpus = C.Corpus(df, index)
content = ContentRecommender(index)
recipe_ids = index["recipe_ids"]
row_of = {int(r): i for i, r in enumerate(recipe_ids)}
log(f"loaded in {time.time() - t0:.0f} s: {len(df):,} recipes, "
    f"{len(inter):,} interactions")


# ===========================================================================
def experiment_rating():
    """Rating prediction against three trivial baselines."""
    section(1, "RATING PREDICTION")
    with open(os.path.join(OUT, "mf.pkl"), "rb") as f:
        factors = pickle.load(f)

    rng = np.random.default_rng(20260816)     # the seed the model was fit with
    users = inter["user_id"].to_numpy()
    items = inter["recipe_id"].to_numpy()
    ratings = inter["rating"].to_numpy(dtype=np.float64)
    order = rng.permutation(len(users))
    cut = int(len(users) * 0.9)
    tr, va = order[:cut], order[cut:]

    # Baselines are fitted on the training half only, exactly as the model was.
    global_mean = float(ratings[tr].mean())
    user_mean = {}
    item_mean = {}
    for u, r in zip(users[tr], ratings[tr]):
        user_mean.setdefault(u, []).append(r)
    for i, r in zip(items[tr], ratings[tr]):
        item_mean.setdefault(i, []).append(r)
    user_mean = {k: float(np.mean(v)) for k, v in user_mean.items()}
    item_mean = {k: float(np.mean(v)) for k, v in item_mean.items()}

    def rmse(pred):
        return float(np.sqrt(np.mean((ratings[va] - np.clip(pred, 1, 5)) ** 2)))

    rows = {
        "matrix factorisation": float(factors["val_rmse"]),
        "global mean": rmse(np.full(len(va), global_mean)),
        "user mean": rmse(np.array([user_mean.get(u, global_mean)
                                    for u in users[va]])),
        "item mean": rmse(np.array([item_mean.get(i, global_mean)
                                    for i in items[va]])),
    }
    for k, v in sorted(rows.items(), key=lambda kv: kv[1]):
        log(f"   {k:<24} RMSE {v:.4f}")

    payload = {"rmse": rows, "n_validation": int(len(va)),
               "n_train": int(len(tr)), "n_factors": factors["n_factors"]}
    save("rating", payload)
    results["rating"] = payload


# ===========================================================================
def _split_users(rng):
    """Users with enough history to hold anything out, and their split."""
    by_user = {}
    for u, i, r in zip(inter["user_id"].to_numpy(),
                       inter["recipe_id"].to_numpy(),
                       inter["rating"].to_numpy(dtype=np.float64)):
        by_user.setdefault(int(u), []).append((int(i), float(r)))

    eligible = [u for u, rs in by_user.items()
                if len(rs) >= MIN_INTERACTIONS
                and sum(1 for _, r in rs if r >= POSITIVE) >= MIN_POSITIVES]
    rng.shuffle(eligible)
    chosen = eligible[:N_EVAL_USERS]

    train, test = {}, {}
    for u in chosen:
        rs = by_user[u]
        pos = [i for i, r in rs if r >= POSITIVE]
        rng.shuffle(pos)
        n_hold = max(2, int(round(len(pos) * HOLDOUT)))
        held = set(pos[:n_hold])
        test[u] = held
        train[u] = [(i, r) for i, r in rs if i not in held]
    return by_user, chosen, train, test, len(eligible)


def _ndcg(hits, n_relevant, k):
    """Normalised discounted cumulative gain for a binary relevance list."""
    dcg = sum(1.0 / np.log2(rank + 2) for rank, hit in enumerate(hits[:k])
              if hit)
    ideal = sum(1.0 / np.log2(rank + 2)
                for rank in range(min(n_relevant, k)))
    return dcg / ideal if ideal > 0 else 0.0


def experiment_ranking(order_by="latent"):
    """Top-N ranking for five systems, over two user populations.

    `order_by` selects how the collaborative signal is turned into an ordering.
    "latent" is what the system deploys, and what Section 3.4.2 specifies:
    rank by the latent term alone.  "predicted" reproduces the behaviour the
    component had before the defect of Section 5.3 was found, ranking by the
    full predicted rating and so, in effect, by item bias.

    The second mode exists because Chapter 5 reports both columns of Table 5.2.
    Without it the "before" column would be the only set of numbers in the
    chapter with no stored result behind it -- and a chapter that claims every
    figure is reproducible cannot carry one that is not.  Both runs use the
    same seed and therefore the same split, so the columns are comparable.
    """
    if order_by not in ("latent", "predicted"):
        raise ValueError("order_by must be 'latent' or 'predicted'")
    section(2, "TOP-N RANKING" + ("" if order_by == "latent"
                                  else "  (pre-correction ordering)"))
    rng = np.random.default_rng(SEED)
    by_user, chosen, train, test, n_eligible = _split_users(rng)
    log(f"   {n_eligible:,} users have >= {MIN_INTERACTIONS} interactions and "
        f">= {MIN_POSITIVES} positives")
    log(f"   evaluating {len(chosen):,} of them, holding out "
        f"{int(HOLDOUT * 100)} per cent of each user's positives")

    # -- retrain the factorisation WITHOUT the held-out interactions ---------
    held_pairs = {(u, i) for u, items in test.items() for i in items}
    mask = np.array([(int(u), int(i)) not in held_pairs
                     for u, i in zip(inter["user_id"], inter["recipe_id"])])
    reduced = inter[mask]
    log(f"   retraining the factorisation on {len(reduced):,} interactions "
        f"({len(inter) - len(reduced):,} held out) ...")
    t = time.time()
    factors = train_matrix_factorisation(reduced, seed=SEED)
    log(f"   retrained in {time.time() - t:.0f} s, "
        f"validation RMSE {factors['val_rmse']:.4f}")

    cf = CollaborativeRecommender(factors, recipe_ids)
    popularity = np.zeros(len(recipe_ids))
    for i, n in Counter(reduced["recipe_id"].to_numpy()).items():
        if int(i) in row_of:
            popularity[row_of[int(i)]] = n

    systems = ("random", "popularity", "content", "collaborative", "switching")
    acc = {s: {f"{m}@{k}": [] for m in ("precision", "recall", "ndcg")
               for k in KS} for s in systems}
    acc_by_pop = {"cold": {s: {f"ndcg@10": []} for s in systems},
                  "warm": {s: {f"ndcg@10": []} for s in systems}}
    switch_choice = Counter()
    top10_support = {"predicted": [], "latent": []}

    for n, u in enumerate(chosen):
        if n and n % 250 == 0:
            log(f"      {n:,}/{len(chosen):,} users scored")
        held = test[u]
        held_rows = [row_of[i] for i in held if i in row_of]
        if not held_rows:
            continue
        seen = [row_of[i] for i, _ in train[u] if i in row_of]
        profile = Profile(ratings={i: r for i, r in train[u]})

        ranked = {}
        ranked["random"] = rng.random(len(recipe_ids))
        ranked["popularity"] = popularity.copy()
        ranked["content"] = content.scores(profile)
        # The controller's own policy, evaluated as the system would apply it.
        controller = SwitchingController(content, cf)
        chosen_rec, why = controller.select(profile)
        picked_cf = "collaborative" in why
        switch_choice["collaborative" if picked_cf else "content"] += 1

        if order_by == "predicted":
            ranked["collaborative"] = cf.predicted_ratings(profile)
            # Before the correction the hybrid inherited whatever ordering its
            # chosen arm produced, so it only differs from the deployed hybrid
            # on users for whom the controller picks the collaborative arm.
            ranked["switching"] = (cf.predicted_ratings(profile) if picked_cf
                                   else controller.scores(profile))
        else:
            ranked["collaborative"] = cf.scores(profile)
            ranked["switching"] = controller.scores(profile)

        if order_by == "predicted":
            # How concentrated each ordering is on barely-rated recipes: the
            # mechanism behind the defect, not just its effect on NDCG.
            for label, vec in (("predicted", cf.predicted_ratings(profile)),
                               ("latent", cf.scores(profile))):
                v = np.asarray(vec, dtype=np.float64).copy()
                v[seen] = -np.inf
                top10 = np.argsort(-v)[:10]
                top10_support[label].append(
                    float(np.median([popularity[r] for r in top10])))

        for s in systems:
            score = np.asarray(ranked[s], dtype=np.float64).copy()
            score[seen] = -np.inf          # never recommend what they rated
            top = np.argpartition(-score, max(KS))[:max(KS)]
            top = top[np.argsort(-score[top])]
            hits = [int(r in held_rows) for r in top]
            for k in KS:
                h = sum(hits[:k])
                acc[s][f"precision@{k}"].append(h / k)
                acc[s][f"recall@{k}"].append(h / len(held_rows))
                acc[s][f"ndcg@{k}"].append(_ndcg(hits, len(held_rows), k))
            bucket = "warm" if len(train[u]) >= 10 else "cold"
            acc_by_pop[bucket][s]["ndcg@10"].append(acc[s]["ndcg@10"][-1])

    table = {s: {m: float(np.mean(v)) for m, v in acc[s].items()}
             for s in systems}
    log()
    log(f"   {'system':<16}" + "".join(f"{'P@' + str(k):>9}" for k in KS)
        + "".join(f"{'NDCG@' + str(k):>10}" for k in KS))
    for s in systems:
        log(f"   {s:<16}"
            + "".join(f"{table[s][f'precision@{k}']:>9.4f}" for k in KS)
            + "".join(f"{table[s][f'ndcg@{k}']:>10.4f}" for k in KS))

    payload = {
        "n_eligible_users": int(n_eligible),
        "n_evaluated": int(len(chosen)),
        "holdout_fraction": HOLDOUT,
        "retrained_val_rmse": float(factors["val_rmse"]),
        "n_train_interactions": int(len(reduced)),
        "n_held_out": int(len(inter) - len(reduced)),
        "metrics": table,
        "switch_selected": dict(switch_choice),
        "by_population": {b: {s: float(np.mean(v["ndcg@10"]))
                              for s, v in d.items() if v["ndcg@10"]}
                          for b, d in acc_by_pop.items()},
    }
    if order_by == "predicted":
        payload["top10_median_ratings"] = {
            k: float(np.median(v)) for k, v in top10_support.items() if v}

    key = "ranking" if order_by == "latent" else "ranking_before"
    save(key, payload)
    results[key] = payload


# ===========================================================================
PROFILES = [
    ("F26 sedentary, no restriction",
     dict(age=26, sex="female", height_cm=163, weight_kg=58,
          activity="inactive",
          liked_ingredients=["tomato", "basil", "chicken"])),
    ("F34 lightly active, vegetarian",
     dict(age=34, sex="female", height_cm=168, weight_kg=64,
          activity="lightly active", diet_regime="vegetarian",
          liked_ingredients=["lentil", "spinach", "feta"])),
    ("F45 active, milk allergy",
     dict(age=45, sex="female", height_cm=160, weight_kg=70,
          activity="active", allergens=["milk"],
          liked_ingredients=["salmon", "broccoli", "rice"])),
    ("F52 lightly active, low sodium",
     dict(age=52, sex="female", height_cm=157, weight_kg=68,
          activity="lightly active", max_sodium_mg=800,
          liked_ingredients=["chicken", "courgette", "lemon"])),
    ("F29 very active, gluten allergy",
     dict(age=29, sex="female", height_cm=172, weight_kg=62,
          activity="very active", allergens=["gluten"],
          liked_ingredients=["rice", "egg", "mushroom"])),
    ("F61 inactive, low sugar",
     dict(age=61, sex="female", height_cm=155, weight_kg=72,
          activity="inactive", max_sugar_g=15,
          liked_ingredients=["fish", "cabbage", "onion"])),
    ("M22 very active, no restriction",
     dict(age=22, sex="male", height_cm=182, weight_kg=76,
          activity="very active",
          liked_ingredients=["beef", "potato", "cheese"])),
    ("M31 lightly active, vegan",
     dict(age=31, sex="male", height_cm=178, weight_kg=80,
          activity="lightly active", diet_regime="vegan",
          liked_ingredients=["chickpea", "tofu", "coriander"])),
    ("M40 active, halal",
     dict(age=40, sex="male", height_cm=175, weight_kg=85,
          activity="active", diet_regime="halal",
          liked_ingredients=["lamb", "aubergine", "yoghurt"])),
    ("M55 inactive, peanut and tree nut allergy",
     dict(age=55, sex="male", height_cm=170, weight_kg=90,
          activity="inactive", allergens=["peanuts", "tree_nuts"],
          liked_ingredients=["chicken", "carrot", "barley"])),
    ("M47 lightly active, low sodium and low sugar",
     dict(age=47, sex="male", height_cm=180, weight_kg=88,
          activity="lightly active", max_sodium_mg=800, max_sugar_g=15,
          liked_ingredients=["turkey", "pepper", "oat"])),
    ("M35 active, vegetarian and egg allergy",
     dict(age=35, sex="male", height_cm=176, weight_kg=74,
          activity="active", diet_regime="vegetarian", allergens=["eggs"],
          liked_ingredients=["bean", "corn", "avocado"])),
]

CEILINGS = ("fat_g", "satfat_g", "sugar_g", "sodium_mg")
TARGETS = ("energy_kcal", "protein_g", "carbs_g")


def _plan_for(spec, controller=None):
    profile = Profile(**spec)
    controller = controller or SwitchingController(content, None)
    return profile, W.plan_week(corpus, df, profile, controller)


def experiment_nutrition():
    """Nutritional attainment over twelve profiles."""
    section(3, "NUTRITIONAL ATTAINMENT")
    rows = []
    for label, spec in PROFILES:
        profile, plan = _plan_for(spec)
        daily = daily_targets(profile)
        per_day = []
        for d in range(len(W.DAYS)):
            totals = plan.day_totals(d)
            totals["satfat_g"] = sum(m.satfat_g for m in plan.day_meals(d))
            per_day.append(totals)
        row = {"profile": label, "unfilled": len(plan.unfilled)}
        for key in TARGETS:
            vals = [100 * t[key] / daily[key] for t in per_day]
            row[key] = float(np.mean(vals))
        for key in CEILINGS:
            vals = [100 * t[key] / daily[key] for t in per_day]
            row[key] = float(np.max(vals))
        row["days_all_ceilings_met"] = int(sum(
            all(t[k] <= daily[k] for k in CEILINGS) for t in per_day))
        rows.append(row)
        log(f"   {label:<44} energy {row['energy_kcal']:5.1f}%  "
            f"worst Na {row['sodium_mg']:5.1f}%  "
            f"{row['days_all_ceilings_met']}/7 days fully compliant")

    payload = {"profiles": rows,
               "mean_energy_attainment": float(np.mean(
                   [r["energy_kcal"] for r in rows])),
               "profiles_with_gaps": int(sum(1 for r in rows
                                             if r["unfilled"] > 0))}
    save("nutrition", payload)
    results["nutrition"] = payload


# ===========================================================================
def _ingredient_sets(plan):
    return [set(df["ingredients_norm"].iloc[m.main.row])
            for m in plan.meals.values()]


def _intra_list_dissimilarity(sets):
    if len(sets) < 2:
        return 0.0
    vals = []
    for a in range(len(sets)):
        for b in range(a + 1, len(sets)):
            union = sets[a] | sets[b]
            if union:
                vals.append(1.0 - len(sets[a] & sets[b]) / len(union))
    return float(np.mean(vals)) if vals else 0.0


def experiment_diversity():
    """Within-week diversity and how much of the corpus is ever reached."""
    section(4, "DIVERSITY AND COVERAGE")
    seen_ids, rows = set(), []
    for label, spec in PROFILES:
        _, plan = _plan_for(spec)
        sets = _ingredient_sets(plan)
        mains = [m.main.recipe_id for m in plan.meals.values()]
        seen_ids.update(rid for m in plan.meals.values()
                        for rid in m.recipe_ids())
        rows.append({"profile": label,
                     "ild": _intra_list_dissimilarity(sets),
                     "distinct_mains": len(set(mains)),
                     "n_meals": len(mains)})
        log(f"   {label:<44} ILD {rows[-1]['ild']:.3f}  "
            f"{rows[-1]['distinct_mains']}/{rows[-1]['n_meals']} distinct mains")

    # Catalogue coverage over a larger set of varied profiles.  Measuring it
    # over the twelve profiles above would say nothing: twelve plans hold a few
    # hundred dishes at most, so the figure would describe the number of plans
    # generated rather than any property of the recommender.  The question
    # worth asking is whether selection concentrates on a few recipes, so the
    # share taken by the single most-selected recipe is reported beside it.
    log()
    log(f"   generating {N_COVERAGE} varied profiles for coverage ...")
    rng = np.random.default_rng(SEED)
    picks = Counter()
    for n in range(N_COVERAGE):
        spec = dict(
            age=int(rng.integers(20, 65)),
            sex=str(rng.choice(["female", "male"])),
            height_cm=float(rng.integers(155, 190)),
            weight_kg=float(rng.integers(50, 95)),
            activity=str(rng.choice(list(PAL))),
            weekday_minutes=int(rng.choice([20, 30, 45])),
            weekend_minutes=int(rng.choice([45, 75, 120])),
        )
        if rng.random() < 0.3:
            spec["diet_regime"] = str(rng.choice(
                ["vegetarian", "vegan", "halal"]))
        if rng.random() < 0.3:
            spec["allergens"] = [str(rng.choice(
                ["milk", "gluten", "eggs", "peanuts"]))]
        _, plan = _plan_for(spec)
        picks.update(rid for m in plan.meals.values() for rid in m.recipe_ids())
        if (n + 1) % 10 == 0:
            log(f"      {n + 1}/{N_COVERAGE} plans, "
                f"{len(picks):,} distinct recipes so far")

    n_main = int((~df["is_side"]).sum())
    n_slots = int(sum(picks.values()))
    coverage = 100.0 * len(picks) / len(df)
    top_share = 100.0 * picks.most_common(1)[0][1] / n_slots
    log(f"   {len(picks):,} distinct recipes over {n_slots:,} slots "
        f"= {coverage:.2f} per cent of the corpus")
    log(f"   most-selected recipe takes {top_share:.2f} per cent of all slots")

    payload = {"per_profile": rows,
               "mean_ild": float(np.mean([r["ild"] for r in rows])),
               "coverage": {
                   "n_plans": N_COVERAGE, "n_slots": n_slots,
                   "distinct_recipes": len(picks),
                   "corpus_size": int(len(df)), "main_corpus_size": n_main,
                   "coverage_percent": coverage,
                   "top_recipe_share_percent": top_share,
                   "recipes_used_once": int(sum(1 for v in picks.values()
                                                if v == 1)),
               }}
    save("diversity", payload)
    results["diversity"] = payload


# ===========================================================================
def experiment_sensitivity():
    """Sweeps over the parameters Chapters 3 and 4 leave open."""
    section(5, "PARAMETER SENSITIVITY")
    sample = PROFILES[:4]
    out = {}

    log("   repeat cap (the diversity/accuracy trade-off of Section 3.6.5)")
    rows = []
    for cap in (1, 2, 3):
        ilds, dist, rel = [], [], []
        for label, spec in sample:
            profile, plan = _plan_for(dict(spec, max_repeats=cap))
            ilds.append(_intra_list_dissimilarity(_ingredient_sets(plan)))
            mains = [m.main.recipe_id for m in plan.meals.values()]
            dist.append(len(set(mains)) / max(len(mains), 1))
            rel.append(float(np.mean([m.terms.get("relevance", 0.0)
                                      for m in plan.meals.values()])))
        rows.append({"max_repeats": cap, "ild": float(np.mean(ilds)),
                     "distinct_fraction": float(np.mean(dist)),
                     "mean_relevance": float(np.mean(rel))})
        log(f"      cap={cap}  ILD {rows[-1]['ild']:.3f}  "
            f"distinct {rows[-1]['distinct_fraction']:.3f}  "
            f"relevance {rows[-1]['mean_relevance']:.4f}")
    out["repeat_cap"] = rows

    log("   main-dish share of the slot target")
    rows = []
    original = C.MAIN_SHARE
    for share in (0.55, 0.65, 0.75):
        C.MAIN_SHARE = share
        devs = []
        for label, spec in sample:
            profile, plan = _plan_for(spec)
            daily = daily_targets(profile)
            devs += [abs(100 * plan.day_totals(d)["energy_kcal"]
                         / daily["energy_kcal"] - 100)
                     for d in range(len(W.DAYS))]
        rows.append({"main_share": share,
                     "mean_energy_deviation": float(np.mean(devs)),
                     "worst_energy_deviation": float(np.max(devs))})
        log(f"      share={share}  mean |dev| {rows[-1]['mean_energy_deviation']:.1f}%"
            f"  worst {rows[-1]['worst_energy_deviation']:.1f}%")
    C.MAIN_SHARE = original
    out["main_share"] = rows

    log("   weight on exceeding a guideline ceiling")
    rows = []
    original = C.CEILING_EMPHASIS
    for emphasis in (0.0, 1.0, 2.0, 4.0):
        C.CEILING_EMPHASIS = emphasis
        worst = {k: [] for k in CEILINGS}
        for label, spec in sample:
            profile, plan = _plan_for(spec)
            daily = daily_targets(profile)
            for d in range(len(W.DAYS)):
                totals = plan.day_totals(d)
                totals["satfat_g"] = sum(m.satfat_g for m in plan.day_meals(d))
                for k in CEILINGS:
                    worst[k].append(100 * totals[k] / daily[k])
        rows.append(dict({"ceiling_emphasis": emphasis},
                         **{k: float(np.max(v)) for k, v in worst.items()}))
        log(f"      emphasis={emphasis}  " + "  ".join(
            f"{k} {rows[-1][k]:.0f}%" for k in CEILINGS))
    C.CEILING_EMPHASIS = original
    out["ceiling_emphasis"] = rows

    save("sensitivity", out)
    results["sensitivity"] = out


# ===========================================================================


# ===========================================================================
def _popularity_week(profile, popularity, apply_filter):
    """A week built by a popularity ranker, with or without the hard filter.

    Both baseline arms are handed the meal-slot structure for free: each slot
    is filled from the recipes tagged for that meal.  Without that they would
    serve dessert for breakfast and the comparison would be against a straw
    man rather than against the strongest simple thing a person might build.
    What the arms do NOT get is the rest of the design -- arm one gets no
    constraint filtering and no nutritional scoring, and arm two gets the
    filter but still no nutritional scoring.
    """
    mask = None
    if apply_filter:
        mask, _ = C.profile_filter(corpus, profile)

    chosen = {}
    for slot in W.SLOTS:
        eligible = corpus.slot[slot].copy()
        if mask is not None:
            eligible &= mask
        order = np.argsort(-np.where(eligible, popularity, -np.inf))
        # Seven days of this meal, most popular first, no repeats.
        chosen[slot] = [int(r) for r in order[:len(W.DAYS)]]

    meals = {}
    for day in range(len(W.DAYS)):
        for slot in W.SLOTS:
            rows = chosen[slot]
            if day < len(rows):
                meals[(day, slot)] = W.Dish(rows[day], corpus, df)
    return meals


def _score_week(meals, profile, daily):
    """The same measurements for every arm, so the arms are comparable."""
    allergen_hits = 0
    regime_hits = 0
    over_time = 0
    per_day = {d: {k: 0.0 for k in list(TARGETS) + list(CEILINGS)}
               for d in range(len(W.DAYS))}

    for (day, slot), dish in meals.items():
        # A Meal knows the allergens of its whole plate; a bare Dish does not,
        # so fall back to the corpus row.  Scoring the full system on its main
        # dishes alone would ignore the accompaniments and flatter it.
        present = set(getattr(dish, "allergens", None)
                      or [c for c in corpus.allergen
                          if corpus.allergen[c][dish.row]])
        if present & set(profile.allergens):
            allergen_hits += 1
        if profile.diet_regime == "vegetarian" and not corpus.is_vegetarian[dish.row]:
            regime_hits += 1
        elif profile.diet_regime == "vegan" and not corpus.is_vegan[dish.row]:
            regime_hits += 1
        elif profile.diet_regime == "halal" and not corpus.halal_ok[dish.row]:
            regime_hits += 1
        if dish.minutes > profile.time_budget(day):
            over_time += 1
        for k in TARGETS:
            per_day[day][k] += getattr(dish, "calories" if k == "energy_kcal"
                                       else k)
        for k in CEILINGS:
            per_day[day][k] += getattr(dish, k)

    energy = float(np.mean([100 * per_day[d]["energy_kcal"]
                            / daily["energy_kcal"] for d in per_day]))
    compliant = int(sum(all(per_day[d][k] <= daily[k] for k in CEILINGS)
                        for d in per_day))
    mains = [dish.recipe_id for dish in meals.values()]
    return {"meals": len(meals), "allergen_violations": allergen_hits,
            "regime_violations": regime_hits, "over_time_meals": over_time,
            "energy_attainment": energy, "days_all_ceilings_met": compliant,
            "distinct_mains": len(set(mains))}


def experiment_ablation():
    """What each layer of the design contributes, without using any ratings.

    Section 5.3 finds that a popularity baseline outranks every personalised
    method on held-out ratings.  That result is real and is reported, but it
    measures the ordering of individual recipes, which is not the task this
    system performs.  This experiment puts the same baseline to the system's
    actual job -- producing a week that respects a person's restrictions and
    approaches their nutritional targets -- and separates the contribution of
    the hard filter from that of the nutritional scoring.
    """
    section(6, "ABLATION: WHAT EACH LAYER CONTRIBUTES")
    popularity = np.zeros(corpus.n)
    for rid, n in Counter(inter["recipe_id"].to_numpy()).items():
        if int(rid) in corpus.row_of:
            popularity[corpus.row_of[int(rid)]] = n

    arms = {"popularity, unfiltered": None,
            "popularity + hard filter": None,
            "full system": None}
    acc = {a: [] for a in arms}

    for label, spec in PROFILES:
        profile = Profile(**spec)
        daily = daily_targets(profile)

        acc["popularity, unfiltered"].append(_score_week(
            _popularity_week(profile, popularity, False), profile, daily))
        acc["popularity + hard filter"].append(_score_week(
            _popularity_week(profile, popularity, True), profile, daily))

        # Meal objects carry the totals for the whole plate -- energy, every
        # nutrient, the combined preparation time and the allergens of every
        # dish on it -- so the full system is scored on what the user actually
        # eats rather than on its main dishes alone.
        _, plan = _plan_for(spec)
        acc["full system"].append(_score_week(plan.meals, profile, daily))

    keys = ("allergen_violations", "regime_violations", "over_time_meals",
            "energy_attainment", "days_all_ceilings_met", "distinct_mains")
    table = {a: {k: float(np.mean([r[k] for r in rows])) for k in keys}
             for a, rows in acc.items()}
    table_tot = {a: {k: int(sum(r[k] for r in rows))
                     for k in ("allergen_violations", "regime_violations",
                               "over_time_meals")}
                 for a, rows in acc.items()}

    log(f"   {'arm':<26}{'allergen':>9}{'regime':>8}{'late':>6}"
        f"{'energy':>9}{'ceil/7':>8}")
    for a in arms:
        log(f"   {a:<26}{table_tot[a]['allergen_violations']:>9}"
            f"{table_tot[a]['regime_violations']:>8}"
            f"{table_tot[a]['over_time_meals']:>6}"
            f"{table[a]['energy_attainment']:>8.1f}%"
            f"{table[a]['days_all_ceilings_met']:>8.1f}")

    payload = {"n_profiles": len(PROFILES), "mean": table,
               "totals_over_all_profiles": table_tot,
               "per_profile": {a: rows for a, rows in acc.items()}}
    save("ablation", payload)
    results["ablation"] = payload


# ===========================================================================
EXPERIMENTS = {
    "rating": experiment_rating,
    "rank": experiment_ranking,
    "rank_before": lambda: experiment_ranking(order_by="predicted"),
    "nutrition": experiment_nutrition,
    "diversity": experiment_diversity,
    "sensitivity": experiment_sensitivity,
    "ablation": experiment_ablation,
}


def main(argv):
    wanted = argv[1:] or list(EXPERIMENTS)
    unknown = [w for w in wanted if w not in EXPERIMENTS]
    if unknown:
        raise SystemExit(f"unknown experiment(s): {unknown}; "
                         f"choose from {list(EXPERIMENTS)}")
    start = time.time()
    for name in wanted:
        EXPERIMENTS[name]()
    log()
    log("=" * 70)
    log(f"finished {len(wanted)} experiment(s) in {time.time() - start:.0f} s")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
