"""User model: profile representation and nutritional targets.

Implements Section 3.3 of the dissertation.

A profile has three parts, and they are kept separate because they enter the
pipeline at different points.  Restrictions are consumed by the hard filter of
Section 3.5.1, preferences by the ranker of Section 3.4, and body data by the
target calculation below.  Nothing here is persisted: a Profile lives for the
duration of a session and is held in Streamlit's session state.

Two reference systems meet in this module and must not be confused with each
other.  The United States daily values in preprocessing.py are a decoding key,
needed only because that is how Food.com encoded its nutrition field.  The
United Kingdom government dietary recommendations used here define what the
system steers the user towards.  Section 3.3.2 states the distinction.
"""

from dataclasses import dataclass, field

# Physical activity levels offered by the interface (Table 3.3).  Four bands is
# a design choice: enough to span ordinary adult activity, few enough that a
# user can answer honestly.
PAL = {
    "inactive": 1.4,
    "lightly active": 1.6,
    "active": 1.75,
    "very active": 1.9,
}

# Energy shares per meal slot (Section 3.6.1).  A design choice rather than a
# derived quantity, placing the largest meal in the evening; exposed here as a
# parameter so alternative splits can be examined.
SLOT_SHARE = {"breakfast": 0.25, "lunch": 0.35, "dinner": 0.40}

# Energy yields, used to turn a share of food energy into a mass.
KCAL_PER_G = {"protein": 4.0, "carbohydrate": 4.0, "fat": 9.0}


@dataclass
class Profile:
    """Everything the system knows about one user for the length of a session."""

    # -- body data: feeds the target calculation only --------------------
    age: int = 30
    sex: str = "female"                 # "male" or "female"
    height_cm: float = 165.0
    weight_kg: float = 65.0
    activity: str = "lightly active"

    # -- restrictions: consumed by the hard filter, never by the ranker ---
    allergens: list = field(default_factory=list)      # keys of ALLERGENS
    diet_regime: str = "none"           # none | vegetarian | vegan | halal
    max_sodium_mg: float | None = None  # clinical exclusion, per serving
    max_sugar_g: float | None = None    # clinical exclusion, per serving
    banned_ingredients: list = field(default_factory=list)

    # -- preferences: consumed by the ranker only ------------------------
    liked_ingredients: list = field(default_factory=list)
    liked_cuisines: list = field(default_factory=list)
    ratings: dict = field(default_factory=dict)        # recipe id -> 1..5
    rejected: list = field(default_factory=list)       # ids replaced by hand

    # -- context ----------------------------------------------------------
    weekday_minutes: int = 30
    weekend_minutes: int = 75

    # How many times one main dish may appear across the week.  Exposed to the
    # user rather than fixed, because how much variety a week should carry is a
    # preference and not a property of the corpus; see Section 3.6.5.
    max_repeats: int = 2

    def n_interactions(self):
        """History size, the criterion the switching policy tests (§3.4.3).

        A rejection is an interaction: Section 3.6.3 treats a replacement as a
        negative preference signal, and it counts towards the history for the
        same reason it counts towards the user vector.
        """
        return len(self.ratings) + len(self.rejected)

    def time_budget(self, day_index):
        """Preparation-time budget for a day, Monday being 0 (§3.6.4)."""
        return self.weekend_minutes if day_index >= 5 else self.weekday_minutes


def basal_metabolic_rate(profile):
    """Mifflin-St Jeor, as given in Table 3.3.

    Chosen because it was derived on a healthy adult sample and is the
    predictive equation most commonly recommended for adults without a
    clinical condition [31].
    """
    base = (10.0 * profile.weight_kg
            + 6.25 * profile.height_cm
            - 5.0 * profile.age)
    return base + 5.0 if profile.sex == "male" else base - 161.0


def daily_targets(profile):
    """Daily energy and macronutrient targets for one user.

    Energy comes from basal metabolic rate scaled by a physical activity level,
    the factorial approach behind the United Kingdom dietary reference values
    for energy [32].  The macronutrient targets are the United Kingdom
    government dietary recommendations [33], expressed as shares of food energy
    except protein, which is specified per kilogram of body weight and is
    converted to a daily mass here.

    Returned masses are the quantities the soft constraints of Section 3.5.2
    measure deviation against.  Note that the recommendations treat fat,
    saturated fat, free sugars and sodium as upper bounds rather than as
    targets in the ordinary sense, whereas Section 3.5.2 defines its penalty as
    the absolute deviation of protein, fat and carbohydrate from the slot
    target.  Fat is therefore steered towards its ceiling rather than kept
    below it, which is a simplification of the guidance and is recorded in
    Chapter 4 as such.
    """
    tee = basal_metabolic_rate(profile) * PAL[profile.activity]
    return {
        "energy_kcal": tee,
        "fat_g": 0.35 * tee / KCAL_PER_G["fat"],
        "satfat_g": 0.11 * tee / KCAL_PER_G["fat"],
        "carbs_g": 0.50 * tee / KCAL_PER_G["carbohydrate"],
        "sugar_g": 0.05 * tee / KCAL_PER_G["carbohydrate"],
        "protein_g": 0.75 * profile.weight_kg,
        "sodium_mg": 2400.0,
    }


def slot_targets(daily, slot, shares=None):
    """A slot's share of the daily targets (§3.6.1)."""
    share = (shares or SLOT_SHARE)[slot]
    return {k: v * share for k, v in daily.items()}


# ---------------------------------------------------------------------------
# Preference tokens
# ---------------------------------------------------------------------------

def preference_tokens(profile):
    """The pseudo-profile a cold-start user is represented by (§3.3.3).

    A new user of the prototype has no interaction history, so every preference
    signal has to come from the form.  Declared likes are emitted as tokens in
    the same vocabulary the recipes are indexed in, and are then treated exactly
    as though they were the aggregate of a short interaction history.  Ratings
    collected during the session are added by recommenders.user_vector(), which
    is where the two sources are combined.
    """
    tokens = []
    for item in profile.liked_ingredients:
        item = item.strip().lower()
        if item:
            tokens.append(item.replace(" ", "_"))
    for item in profile.liked_cuisines:
        item = item.strip().lower()
        if item:
            # Cuisines are corpus tags, which are hyphenated rather than spaced.
            tokens.append(item.replace(" ", "-"))
    return tokens
