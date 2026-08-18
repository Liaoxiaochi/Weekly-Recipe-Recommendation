"""Three-layer allergen lexicon for the fourteen allergen classes listed in
Annex II of Regulation (EU) No 1169/2011.

The lexicon is deliberately built in three layers because a single keyword list
cannot survive user-generated ingredient text:

  DIRECT     the allergen itself, or an obvious substring of it ("peanut").
  DERIVED    synonyms, regional names and derivatives that share no substring
             with the class name ("groundnut", "casein", "semolina", "tahini").
  COMPOSITE  named foods that reliably CONTAIN the allergen without naming it
             ("worcestershire sauce" contains anchovy; "pesto" contains pine
             nuts and hard cheese; most "soy sauce" contains wheat).

The COMPOSITE layer is what drives the false-negative rate down; the other two
layers alone leave obvious holes.  Matching is fail-closed: a composite food is
flagged whenever the allergen is *usually* present, not only when it is always
present, because over-exclusion costs the user a recipe while under-exclusion
can cause harm.
"""

# Each entry: class key -> (direct, derived, composite)
ALLERGENS = {
    "gluten": (
        ["wheat", "rye", "barley", "oats", "oat ", "spelt", "gluten"],
        ["semolina", "durum", "farina", "kamut", "einkorn", "emmer", "triticale",
         "seitan", "bulgur", "couscous", "freekeh", "graham flour", "matzo",
         "matzah", "panko", "breadcrumb", "bread crumb", "malt", "brewer's yeast",
         "wheatgerm", "wheat germ", "bran flake"],
        ["flour", "bread", "pasta", "spaghetti", "macaroni", "noodle", "tortilla",
         "pastry", "puff pastry", "filo", "phyllo", "cracker", "pretzel", "pita",
         "bagel", "croissant", "cake mix", "biscuit mix", "pancake mix",
         "bisquick", "soy sauce", "teriyaki", "hoisin", "beer", "ale ", "lager",
         "stuffing mix", "crouton", "wonton", "gnocchi", "orzo", "udon", "ramen",
         # added after the v1 ground-truth measurement: every term below
         # corresponds to a recipe the v1 lexicon missed
         "bun", "roll", "dough", "pie shell", "pie crust", "cookie", "oreo",
         "wafer", "ladyfinger", "fettuccine", "linguine", "penne", "ziti",
         "rigatoni", "lasagna", "ravioli", "tortellini", "vermicelli",
         "farfalle", "fusilli", "tagliatelle", "cannelloni", "brioche",
         "challah", "muffin", "scone", "waffle", "crepe", "doughnut", "donut",
         "biscotti", "graham", "shortbread", "sponge cake", "angel food"],
    ),
    "crustaceans": (
        ["shrimp", "prawn", "crab", "lobster", "crayfish", "crawfish", "langoustine"],
        ["scampi", "krill"],
        ["seafood", "shrimp paste", "surimi", "bouillabaisse", "paella mix"],
    ),
    "eggs": (
        ["egg", "eggs", "egg white", "egg yolk"],
        ["albumen", "albumin", "ovalbumin", "meringue", "lysozyme"],
        # "pasta" was removed after the v1 measurement: dried Italian pasta is
        # normally eggless, and the term produced four false positives while
        # catching nothing that the specific egg-pasta terms below do not.
        ["mayonnaise", "mayo", "aioli", "hollandaise", "caesar",
         "custard", "eggnog", "marshmallow fluff", "cake mix", "pancake mix",
         "bisquick", "brioche", "challah", "tartar sauce",
         # added after the v1 ground-truth measurement
         "thousand island", "ranch dressing", "ladyfinger", "wonton",
         "tortellini", "ravioli", "fresh pasta", "waffle", "crepe", "quiche",
         "meringue", "sponge cake", "angel food", "profiterole", "macaron"],
    ),
    "fish": (
        ["fish", "salmon", "tuna", "cod", "haddock", "trout", "sardine",
         "anchovy", "anchovies", "mackerel", "herring", "halibut", "tilapia",
         "bass", "snapper", "sole", "pollock"],
        ["caviar", "roe", "bonito", "katsuobushi", "nam pla", "garum"],
        ["worcestershire", "worcester sauce", "fish sauce", "caesar dressing",
         "caesar salad", "surimi", "oyster sauce", "puttanesca", "tapenade",
         "gentleman's relish"],
    ),
    "peanuts": (
        ["peanut", "peanuts", "peanut butter"],
        ["groundnut", "arachis", "monkey nut", "beer nut", "goober"],
        ["satay", "satay sauce", "pad thai sauce", "kung pao", "nutter butter"],
    ),
    "soybeans": (
        ["soy", "soya", "soybean", "soy bean", "tofu", "edamame"],
        ["tempeh", "miso", "natto", "tamari", "textured vegetable protein", "tvp",
         "soy lecithin", "lecithin"],
        ["soy sauce", "teriyaki", "hoisin", "ponzu", "vegetable broth",
         "vegetable oil", "margarine", "worcestershire"],
    ),
    "milk": (
        ["milk", "butter", "cheese", "cream", "yogurt", "yoghurt", "buttermilk"],
        ["casein", "caseinate", "whey", "ghee", "curd", "lactose", "custard",
         "quark", "kefir", "creme fraiche", "mascarpone", "ricotta", "paneer",
         "half-and-half", "half and half"],
        ["parmesan", "mozzarella", "cheddar", "feta", "brie", "gouda",
         "chocolate", "milk chocolate", "white chocolate", "pesto", "alfredo",
         "bechamel", "ranch dressing", "caesar dressing", "ice cream", "gelato",
         "condensed milk", "evaporated milk", "cake mix", "bisquick", "nutella",
         # added after the v1 ground-truth measurement
         "cool whip", "whipped topping", "toffee", "fudge", "butterscotch",
         "velveeta", "havarti", "asiago", "colby", "provolone", "halloumi"],
    ),
    "tree_nuts": (
        ["almond", "hazelnut", "walnut", "cashew", "pecan", "pistachio",
         "macadamia", "brazil nut", "chestnut", "pine nut"],
        ["filbert", "praline", "marzipan", "frangipane", "nougat", "gianduja",
         "nut butter", "almond flour", "almond meal", "amaretto", "pignoli"],
        ["pesto", "nutella", "baklava", "mixed nuts", "trail mix", "granola",
         "muesli", "romesco", "waldorf salad"],
    ),
    "celery": (
        ["celery", "celeriac"],
        ["celery salt", "celery seed"],
        ["mirepoix", "bouquet garni", "stock cube", "bouillon", "vegetable stock",
         "chicken stock", "beef stock", "broth", "v8", "bloody mary mix"],
    ),
    "mustard": (
        ["mustard"],
        ["dijon", "wholegrain mustard", "mustard seed", "mustard powder"],
        ["salad dressing", "vinaigrette", "barbecue sauce", "bbq sauce",
         "ketchup", "mayonnaise", "piccalilli", "curry powder", "chutney"],
    ),
    "sesame": (
        ["sesame", "sesame seed", "sesame oil"],
        ["tahini", "benne", "gingelly", "til "],
        ["hummus", "halva", "za'atar", "zaatar", "burger bun", "bagel",
         "falafel", "baba ganoush"],
    ),
    "sulphites": (
        ["sulphite", "sulfite", "sulphur dioxide", "sulfur dioxide"],
        ["e220", "e221", "e222", "e223", "e224", "e226", "e227", "e228",
         "potassium metabisulphite", "sodium metabisulfite"],
        ["wine", "red wine", "white wine", "vinegar", "balsamic", "dried apricot",
         "raisin", "sultana", "dried fruit", "molasses", "grape juice", "cider"],
    ),
    "lupin": (
        ["lupin", "lupine"],
        ["lupin flour", "lupini"],
        [],
    ),
    "molluscs": (
        ["mussel", "clam", "oyster", "scallop", "squid", "octopus", "snail",
         "cockle", "whelk", "abalone", "calamari"],
        ["escargot", "cuttlefish"],
        ["oyster sauce", "seafood", "paella mix", "clam juice"],
    ),
}

# Food.com tag names that assert the ABSENCE of an allergen class.  These are
# user-supplied and are therefore used only as corroboration: a tag never marks
# a recipe safe on its own, but a contradiction between rule and tag is a signal
# worth counting.
NEGATIVE_TAGS = {
    "gluten": ["gluten-free"],
    "milk": ["dairy-free", "lactose-free", "vegan"],
    "eggs": ["egg-free", "vegan"],
    "tree_nuts": ["nut-free"],
    "peanuts": ["nut-free"],
}

LAYER_NAMES = ("direct", "derived", "composite")

# Phrases that contain an allergen term as a substring while containing no
# allergen.  Added after the v1 ground-truth measurement, where nine of the
# thirteen false positives came from "coconut milk", "soymilk", "butter beans",
# "butternut squash" and "peanut butter" firing the milk rules.
#
# These are removed from the text BEFORE matching, so they cannot fire a rule.
# A phrase belongs here only when it is never a source of the allergen; a
# phrase that merely usually lacks it stays out, because the fail-closed
# policy prefers an unnecessary exclusion to a missed allergen.
EXEMPT = {
    "milk": ["coconut milk", "coconut cream", "coconut butter", "soy milk",
             "soymilk", "almond milk", "almond butter", "oat milk",
             "rice milk", "cashew milk", "cashew butter", "hemp milk",
             "peanut butter", "nut butter", "apple butter", "cocoa butter",
             "shea butter", "butter bean", "butternut", "butterhead",
             "butter lettuce", "cream of tartar", "soy creamer",
             "non-dairy creamer", "nondairy creamer", "creme de cacao",
             "coconut whipped", "buttercup squash", "butterfly"],
    "eggs": ["eggplant"],
    "gluten": ["gluten-free", "rice flour", "almond flour", "coconut flour",
               "corn tortilla", "rice noodle", "glass noodle", "rice paper",
               "buckwheat noodle", "root beer", "ginger beer", "ginger ale"],
    "soybeans": ["soy-free"],
}


def build_matcher():
    """Return {class: [(term, layer), ...]} sorted longest-first.

    Longest-first matching matters: "peanut butter" must be tested before
    "butter" so the more specific term wins when reporting which layer fired.
    """
    matcher = {}
    for cls, layers in ALLERGENS.items():
        terms = []
        for layer, words in zip(LAYER_NAMES, layers):
            for w in words:
                terms.append((w.strip().lower(), layer))
        terms.sort(key=lambda t: -len(t[0]))
        matcher[cls] = terms
    return matcher


def masked_text(ingredient_text, cls):
    """Blank out this class's exempt phrases so they cannot fire a rule."""
    t = ingredient_text
    for phrase in EXEMPT.get(cls, []):
        t = t.replace(phrase, " " * len(phrase))
    return t


def classify(ingredient_text, matcher):
    """Return {class: layer} for every allergen class fired by this text.

    `ingredient_text` should be a single lower-cased string containing all the
    ingredients of one recipe.  Substring matching is used deliberately: it
    over-matches, which is the safe direction under the fail-closed policy,
    except where EXEMPT records that a phrase never carries the allergen.
    """
    hits = {}
    for cls, terms in matcher.items():
        t = masked_text(ingredient_text, cls)
        for term, layer in terms:
            if term in t:
                hits[cls] = layer
                break
    return hits


def fires(ingredient_text, cls, matcher):
    """True if any rule for `cls` fires on this text."""
    t = masked_text(ingredient_text, cls)
    return any(term in t for term, _ in matcher[cls])
