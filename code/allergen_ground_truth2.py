"""Manual allergen ground truth for the SECOND, independent 104-recipe sample.

Labelled the same way as the first sample and under the same policy, so that
the two measurements are comparable.  Each ingredient list was read and, for
the four classes the sample is stratified on, a decision made about whether the
allergen is genuinely present.

Composite products are resolved by their usual composition: soy sauce and
kecap manis contain wheat, Worcestershire sauce contains anchovy, mayonnaise is
made with egg, cake and brownie mixes contain wheat, corn flakes contain barley
malt, and Cool Whip contains milk solids.

Where a product's composition genuinely varies between brands -- margarine,
bouillon granules, stock, instant pudding mix, chocolate chips, bloody mary
mix, French dressing -- the label records the allergen as ABSENT unless it is
present in the great majority of formulations.  That is the conservative choice
for this measurement: a borderline case counted as absent can never be scored
as a miss, so the estimated recall is a lower bound rather than an optimistic
figure.

ONE BOUNDARY WORTH STATING.  The class labelled `f` here is fish in the sense of
Annex II to Regulation (EU) No 1169/2011, which lists crustaceans and molluscs
as separate classes.  Crab, prawn, shrimp paste and oyster sauce are therefore
NOT labelled as fish, even though a rule set may flag them, and the resulting
disagreements are counted against precision rather than quietly reconciled.

Codes:  g = cereals containing gluten,  m = milk,  e = eggs,  f = fish
Index is the 1-based position in outputs/allergen_sample2.csv.
"""

LABELS = {
    # --- gluten_pos ----------------------------------------------------
    1: "ge",    # flour, eggs
    2: "ge",    # sweet soy sauce + soy sauce (wheat), eggs
    3: "ge",    # flour, eggs
    4: "ge",    # flour, beer, mayonnaise
    5: "g",     # plain flour; vegan margarine and soymilk are not dairy
    6: "gm",    # sweet biscuits; butter, cream cheese, cream
    7: "ge",    # panko, rolls; mayonnaise, egg
    8: "g",     # soy sauce; bouillon granule varies, counted absent
    9: "gme",   # cake mix; sour cream, Cool Whip; eggs
    10: "gme",  # cake mix; butter; eggs
    11: "g",    # soy sauce
    12: "gm",   # pasta; buttermilk dressing
    13: "g",    # flour; soymilk is not dairy

    # --- gluten_neg ----------------------------------------------------
    14: "m",    # heavy cream, butter, parmesan
    15: "",
    16: "",
    17: "",
    18: "",
    19: "",
    20: "",
    21: "m",    # parmesan
    22: "e",    # mayonnaise, egg yolks; crab is crustacean, not fish
    23: "me",   # sour cream; eggs
    24: "m",    # butter
    25: "",
    26: "m",    # yogurt

    # --- milk_pos ------------------------------------------------------
    27: "gme",  # breadcrumbs; butter; eggs, mayonnaise
    28: "m",    # butter, milk
    29: "m",    # butter, half-and-half
    30: "gme",  # flour; milk, butter; egg
    31: "gme",  # cake mix; butter; eggs
    32: "gme",  # flour; butter; eggs
    33: "gm",   # plain flour; butter
    34: "me",   # milk; egg
    35: "gme",  # brownie mix; milk, Cool Whip; eggs
    36: "m",    # butter, whipping cream
    37: "mf",   # butter, parmesan; salmon
    38: "gm",   # vanilla wafer crumbs; butter
    39: "gme",  # flour; butter; eggs

    # --- milk_neg ------------------------------------------------------
    40: "",
    41: "gf",   # flour; tilapia
    42: "",
    43: "",
    44: "",
    45: "",
    46: "",
    47: "g",    # bagels
    48: "ge",   # pasta; mayonnaise
    49: "gef",  # flour, beer; egg yolk and white; Worcestershire
    50: "",
    51: "g",    # light soy sauce; prawns are crustacean, not fish
    52: "ge",   # whole wheat flour; eggs

    # --- eggs_pos ------------------------------------------------------
    53: "ge",   # breadcrumb, egg noodles; egg
    54: "ge",   # flour, oats, oatmeal; eggs; margarine counted absent
    55: "gme",  # bread; evaporated milk, milk; eggs
    56: "mef",  # butter; egg; catfish
    57: "gme",  # flour; milk; eggs
    58: "gme",  # bread; milk, butter; eggs
    59: "gme",  # flour; butter, sour cream; egg yolks
    60: "me",   # milk, heavy cream; eggs
    61: "gme",  # flour; butter; eggs
    62: "gme",  # croutons, panko; cheddar; egg
    63: "gmef",  # breadcrumbs, puff pastry, flour; butter; eggs; Worcestershire
    64: "e",    # mayonnaise
    65: "gme",  # flour; butter; eggs

    # --- eggs_neg ------------------------------------------------------
    66: "",
    67: "gm",   # corn flakes carry barley malt; cream soup, sour cream, cheddar
    68: "gm",   # flour, oatmeal; butter, condensed milk
    69: "",     # bloody mary mix varies, counted absent
    70: "g",    # bulgar wheat
    71: "m",    # butter
    72: "",
    73: "gm",   # flour; queso fresco
    74: "m",    # cream liqueur, cream
    75: "gm",   # flour; milk
    76: "",
    77: "",
    78: "gm",   # flour; butter, cream cheese, cream, milk, parmesan

    # --- fish_pos ------------------------------------------------------
    79: "mf",   # butter; Worcestershire
    80: "f",    # Worcestershire
    81: "gf",   # baguette; anchovy
    82: "gmf",  # flour; butter; tilapia
    83: "mef",  # sour cream; mayonnaise; tuna
    84: "gmf",  # breadcrumbs; butter; Worcestershire
    85: "",     # shrimp paste and oyster sauce are crustacean and mollusc
    86: "mf",   # cream; Worcestershire
    87: "gmef",  # soy sauce, oats; buttermilk; eggs; Worcestershire
    88: "mf",   # butter; Worcestershire; shrimp is crustacean
    89: "gmf",  # french bread; butter, cheeses; Worcestershire
    90: "mef",  # yogurt, cheddar; mayonnaise; tilapia and fish
    91: "gf",   # flour; Worcestershire

    # --- fish_neg ------------------------------------------------------
    92: "gm",   # flour; butter
    93: "",
    94: "m",    # evaporated milk, butter
    95: "m",    # cheddar, sour cream
    96: "",
    97: "g",    # dinner rolls; margarine counted absent
    98: "m",    # butter, cream of mushroom soup
    99: "m",    # butter
    100: "m",   # butter, parmesan
    101: "gme",  # english muffins; cheddar; mayonnaise
    102: "m",   # butter
    103: "m",   # cream of chicken soup, butter, colby, monterey jack
    104: "m",   # yogurt, milk
}

CLASS_OF = {"g": "gluten", "m": "milk", "e": "eggs", "f": "fish"}
