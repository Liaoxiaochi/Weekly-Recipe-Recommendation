"""A short written note about one dish, for the recipe detail view.

WHAT THIS IS, AND WHAT IT IS NOT
--------------------------------
This module is a presentation-layer aid.  It writes one or two sentences to
help a user decide about a meal.  It is **not part of the recommendation
system**: nothing here influences which recipes are chosen, ranked, filtered or
excluded.  The planner produces a week; this module only describes what the
planner already decided.  Chapter 4 states the separation explicitly, because
blurring it would misrepresent what the project contributes.

TWO SOURCES, IN THIS ORDER
--------------------------
1.  A note derived arithmetically from the plan (`derived_note`).  Every clause
    traces to a number this codebase computed.  It cannot be wrong about the
    data because it *is* the data.
2.  A language model rewriting those same facts into fluent prose
    (`model_note`), used only when a key is configured and the safety filter
    passes it.

The derived note is the floor, not the fallback of last resort.  With no API
key, no network, a provider outage, or a filtered response, the interface still
shows a useful note and the user test is unaffected.

THE SAFETY BOUNDARY
-------------------
The system's whole position on allergens is fail-closed: it screens, it errs
towards exclusion, and it tells the user plainly that screening is not a safety
guarantee (§3.7.2).  A generated sentence asserting that a dish is safe would
contradict that position in the one place a user is most likely to believe it.

So the boundary is enforced twice, and neither layer is optional:

  * the instruction forbids any claim about allergens, safety, or health; and
  * `passes_safety_filter()` discards any response that makes one anyway.

A model that ignores the instruction therefore still cannot put a safety claim
on screen -- the filter runs on the output, not on trust.
"""

import os
import re

# Vocabulary that must never appear in a generated note.  A hit is not
# sanitised or edited around: the whole response is discarded and the derived
# note is shown instead.  Rewriting a partially unsafe sentence would leave the
# judgement of what is safe to keep with the thing that just got it wrong.
FORBIDDEN = (
    "safe", "safety", "allergen", "allergy", "allergic", "intoleran",
    "medical", "medicine", "doctor", "diagnos", "cure", "treat", "prescri",
    "healthy for you", "good for your", "won't harm", "no risk", "risk-free",
)

# Anything longer is a sign the instruction was ignored; the card has room for
# two sentences, not a paragraph.
MAX_CHARS = 320

SYSTEM_PROMPT = """You write one short note about a meal in a weekly meal plan.

Rules, in order of importance:

1. Use ONLY the facts given to you. Do not add cooking advice, nutrition
   claims, ingredient substitutions, or any information not in the input. If
   you do not know something, do not mention it.
2. Never say or imply anything about allergens, allergies, dietary safety,
   health benefits, or medical suitability. Never say a dish is safe, healthy,
   good for someone, or suitable for a condition. This is absolute: the system
   this note appears in makes its own allergen screening decisions and states
   plainly that screening is not a safety guarantee. A sentence from you
   suggesting otherwise would mislead someone who may be at risk.
3. Two sentences maximum. Plain language. No headings, no lists, no emoji.
4. Be concrete and specific to this dish and this user's plan. Say something
   the numbers actually support -- how it fits the day, how it compares with
   their time budget, what it contributes. Do not pad with generic praise.
5. Address the reader as "you"."""


def _client():
    """An OpenAI-compatible client pointed at DeepSeek, or None if unconfigured.

    The key is read from Streamlit's secrets store or the environment, never
    from source.  Returning None rather than raising is deliberate: an absent
    key is an ordinary state, not an error, and the caller falls back.
    """
    key = os.environ.get("DEEPSEEK_API_KEY")
    if not key:
        try:
            import streamlit as st
            key = st.secrets.get("DEEPSEEK_API_KEY")
        except Exception:
            key = None
    if not key:
        return None, None
    try:
        from openai import OpenAI
    except ImportError:
        return None, None
    model = os.environ.get("DEEPSEEK_MODEL")
    if not model:
        try:
            import streamlit as st
            model = st.secrets.get("DEEPSEEK_MODEL")
        except Exception:
            model = None
    return OpenAI(api_key=key, base_url="https://api.deepseek.com"), \
        (model or "deepseek-chat")


def is_configured():
    """Whether a generated note is available at all."""
    return _client()[0] is not None


def passes_safety_filter(text):
    """Whether a generated note may be shown.

    Rejects on any forbidden term, on excessive length, and on empty output.
    Case-insensitive and substring-based, which over-rejects -- "intoleran"
    catches "intolerant" and "intolerance", "treat" catches "treatment" and
    also the innocent "treat".  That is the intended direction of error: the
    cost of a false rejection is a slightly plainer note, and the cost of a
    false acceptance is a safety claim on screen.
    """
    if not text or not text.strip():
        return False
    if len(text) > MAX_CHARS:
        return False
    lowered = text.lower()
    return not any(term in lowered for term in FORBIDDEN)


def derived_note(dish, meal, allowance, daily, profile, week_count=1):
    """A note assembled from the plan's own arithmetic.

    Every clause below is a number this codebase computed, so the note is exact
    by construction.  It is the note shown whenever the generated one is
    unavailable or rejected, and it is also the factual input the model is
    asked to rewrite -- the two never disagree, because they are the same
    facts.
    """
    facts = []

    share = 100.0 * dish.calories / max(daily["energy_kcal"], 1.0)
    facts.append(f"supplies {share:.0f} per cent of your day's energy")

    if daily.get("protein_g"):
        p = 100.0 * dish.protein_g / max(daily["protein_g"], 1e-6)
        if p >= 15:
            facts.append(f"and {p:.0f} per cent of your daily protein")

    budget = profile.time_budget(meal.day_index) if meal is not None else None
    if budget:
        if dish.minutes > budget:
            facts.append(f"it needs {dish.minutes - budget} minutes more than "
                         f"your {budget}-minute budget for {meal.day}")
        elif dish.minutes <= budget * 0.5:
            facts.append(f"and takes {dish.minutes} minutes, well inside your "
                         f"{budget}-minute budget")

    if week_count > 1:
        facts.append(f"it appears {week_count} times this week")

    liked = [i for i in profile.liked_ingredients
             if i.strip() and any(i.strip().lower() in ing.lower()
                                  for ing in dish.ingredients)]
    if liked:
        facts.append("it uses " + ", ".join(sorted(set(liked)))
                     + ", which you said you enjoy")

    if not facts:
        return ""
    first = facts[0][0].upper() + facts[0][1:]
    rest = facts[1:]
    out = first + ("; " + "; ".join(rest) if rest else "") + "."
    return out.replace("; and ", " and ")


def _fact_block(dish, meal, allowance, daily, profile, week_count):
    """The facts handed to the model.  It may rewrite these and nothing else."""
    lines = [
        f"Dish: {dish.name}",
        f"Served: {dish.servings:g} serving(s), {dish.calories:.0f} kcal",
        f"Preparation time: {dish.minutes} minutes",
        f"Ingredients: {', '.join(dish.ingredients)}",
        f"This meal's slot allows about {allowance['energy_kcal']:.0f} kcal",
        f"The user's daily energy target is {daily['energy_kcal']:.0f} kcal "
        f"and daily protein target {daily['protein_g']:.0f} g",
        f"This dish provides {dish.protein_g:.0f} g protein, "
        f"{dish.carbs_g:.0f} g carbohydrate, {dish.fat_g:.0f} g fat",
    ]
    if meal is not None:
        budget = profile.time_budget(meal.day_index)
        lines.append(f"It is planned for {meal.day} {meal.slot}, when the user "
                     f"has {budget} minutes to cook")
    if week_count > 1:
        lines.append(f"It appears {week_count} times in this week's plan")
    if profile.liked_ingredients:
        lines.append("The user said they enjoy: "
                     + ", ".join(profile.liked_ingredients))
    return "\n".join(lines)


def model_note(dish, meal, allowance, daily, profile, week_count=1,
               timeout=20.0):
    """A generated note, or None if unavailable or rejected by the filter."""
    client, model = _client()
    if client is None:
        return None
    facts = _fact_block(dish, meal, allowance, daily, profile, week_count)
    try:
        response = client.chat.completions.create(
            model=model,
            max_tokens=160,
            temperature=0.6,
            timeout=timeout,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": facts},
            ],
        )
        text = (response.choices[0].message.content or "").strip()
    except Exception:
        # Any provider failure -- no network, bad key, rate limit, timeout --
        # is an ordinary state here, not an error worth surfacing.  The caller
        # falls back to the derived note and the user sees no difference.
        return None
    text = re.sub(r"\s+", " ", text).strip().strip('"')
    return text if passes_safety_filter(text) else None


def note_for(dish, meal, allowance, daily, profile, week_count=1):
    """The note to display, and how it was produced.

    Returns (text, source) where source is "model" or "derived", so the
    interface can label generated text as generated -- a user is entitled to
    know which sentences a machine wrote.
    """
    generated = model_note(dish, meal, allowance, daily, profile, week_count)
    if generated:
        return generated, "model"
    return derived_note(dish, meal, allowance, daily, profile, week_count), \
        "derived"
