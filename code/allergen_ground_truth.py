"""Manual allergen ground truth for the 160-recipe stratified sample.

Labelled by reading each ingredient list and deciding, for the four classes
the sample is stratified on, whether the allergen is genuinely present.
Composite products were resolved by their usual composition: ladyfingers and
wonton wrappers contain wheat and egg, tortellini contains egg, Worcestershire
sauce contains anchovy, Cool Whip contains milk solids.

Where a product's composition genuinely varies between brands -- taco
seasoning, bouillon cubes, stock granules, margarine, thousand island
dressing -- the label records the allergen as ABSENT unless it is present in
the great majority of formulations. That is the conservative choice for this
measurement: it makes the estimated recall a lower bound rather than an
optimistic one, because a borderline case counted as absent can never be
scored as a miss.

Codes:  g = cereals containing gluten,  m = milk,  e = eggs,  f = fish
Index is the 1-based position in outputs/allergen_sample.csv.
"""

LABELS = {
    # --- gluten_pos ---------------------------------------------------
    1: "gme", 2: "gm", 3: "gm", 4: "gme", 5: "gm",
    6: "g", 7: "gme", 8: "gm", 9: "gm", 10: "gef",
    11: "gme", 12: "gme", 13: "gm", 14: "gme", 15: "gm",
    16: "gm", 17: "g", 18: "gm", 19: "gme", 20: "gm",
    # --- gluten_neg ---------------------------------------------------
    21: "", 22: "", 23: "", 24: "m", 25: "m",
    26: "m", 27: "m", 28: "m", 29: "", 30: "m",
    31: "f", 32: "m", 33: "gme", 34: "m", 35: "m",
    36: "g", 37: "", 38: "m", 39: "m", 40: "",
    # --- milk_pos -----------------------------------------------------
    41: "m", 42: "me", 43: "gme", 44: "m", 45: "gm",
    46: "gm", 47: "gme", 48: "", 49: "gmef", 50: "",
    51: "", 52: "gme", 53: "m", 54: "gm", 55: "",
    56: "gme", 57: "gme", 58: "gm", 59: "m", 60: "gme",
    # --- milk_neg -----------------------------------------------------
    61: "", 62: "g", 63: "", 64: "", 65: "",
    66: "g", 67: "", 68: "ge", 69: "ge", 70: "e",
    71: "gf", 72: "", 73: "", 74: "ge", 75: "",
    76: "", 77: "g", 78: "", 79: "f", 80: "g",
    # --- eggs_pos -----------------------------------------------------
    81: "gef", 82: "e", 83: "gme", 84: "gme", 85: "gme",
    86: "gm", 87: "gme", 88: "ge", 89: "e", 90: "gm",
    91: "ge", 92: "e", 93: "gme", 94: "mef", 95: "gme",
    96: "gme", 97: "ge", 98: "gme", 99: "gme", 100: "me",
    # --- eggs_neg -----------------------------------------------------
    101: "", 102: "", 103: "", 104: "gme", 105: "m",
    106: "g", 107: "", 108: "g", 109: "", 110: "m",
    111: "g", 112: "gm", 113: "", 114: "", 115: "",
    116: "m", 117: "", 118: "g", 119: "m", 120: "g",
    # --- fish_pos -----------------------------------------------------
    121: "gmef", 122: "gmef", 123: "gmef", 124: "gf", 125: "gmef",
    126: "f", 127: "f", 128: "f", 129: "mef", 130: "f",
    131: "gmf", 132: "ef", 133: "mf", 134: "mf", 135: "f",
    136: "gf", 137: "f", 138: "f", 139: "gmf", 140: "mef",
    # --- fish_neg -----------------------------------------------------
    141: "gme", 142: "gm", 143: "gm", 144: "gme", 145: "",
    146: "", 147: "", 148: "", 149: "", 150: "m",
    151: "gm", 152: "g", 153: "gm", 154: "", 155: "g",
    156: "g", 157: "m", 158: "", 159: "gme", 160: "gme",
}

CODE = {"g": "gluten", "m": "milk", "e": "eggs", "f": "fish"}

# Recipes whose composition is genuinely brand-dependent, recorded so that the
# sensitivity of the result to these judgements can be reported honestly.
BORDERLINE = {
    23: "taco seasoning may contain wheat flour",
    27: "enchilada sauce may be thickened with wheat flour",
    32: "bouillon cube may contain wheat",
    40: "beef bouillon granules may contain wheat",
    50: "chocolate protein powder is often whey-based",
    67: "margarine may contain milk solids",
    110: "ice cream may contain egg",
    115: "bottled vinaigrette may contain egg",
    119: "dry onion soup mix may contain wheat",
    149: "asafoetida powder is often bulked with wheat flour",
}
