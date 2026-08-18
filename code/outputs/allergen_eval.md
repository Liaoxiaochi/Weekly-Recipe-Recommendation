# Allergen tagging: measured against manual ground truth

Stratified sample of 160 recipes, labelled by hand for the four classes the sample is stratified on. Strata deliberately include recipes the rules called negative, because that is where false negatives hide.

| Class | Truly present | TP | FN | FP | Recall | Precision |
|---|---:|---:|---:|---:|---:|---:|
| gluten | 82 | 74 | 8 | 0 | 0.902 | 1.000 |
| milk | 84 | 83 | 1 | 9 | 0.988 | 0.902 |
| eggs | 51 | 46 | 5 | 4 | 0.902 | 0.920 |
| fish | 27 | 27 | 0 | 0 | 1.000 | 1.000 |
| **micro** | 244 | 230 | 14 | 13 | **0.943** | **0.947** |

Micro false-negative rate: **5.7 per cent**.

## False negatives

- **gluten** in *quick   easy diabetic tiramisu* (sample #33)
- **gluten** in *giada s sausage  peppers  and onions* (sample #36)
- **gluten** in *chipotle cream cheese crescent rolls* (sample #46)
- **gluten** in *yellow squash pie* (sample #57)
- **gluten** in *blue cheese bacon burgers* (sample #122)
- **gluten** in *danish burgers w   herb caper sauce and a mod salad* (sample #142)
- **gluten** in *cookies and cream smoothie* (sample #151)
- **gluten** in *fettuccine with roasted peppers   vegan* (sample #155)
- **milk** in *cranberry walnut salad* (sample #150)
- **eggs** in *quick   easy diabetic tiramisu* (sample #33)
- **eggs** in *steamed shrimp and vegetable dumplings* (sample #69)
- **eggs** in *tortellini and asparagus in garlic cream sauce* (sample #104)
- **eggs** in *bea s chicken caesar skewers* (sample #123)
- **eggs** in *sue s reuben sandwich* (sample #141)

## Borderline judgements

Recorded as absent, which makes the recall estimate a lower bound:

- #23: taco seasoning may contain wheat flour
- #27: enchilada sauce may be thickened with wheat flour
- #32: bouillon cube may contain wheat
- #40: beef bouillon granules may contain wheat
- #50: chocolate protein powder is often whey-based
- #67: margarine may contain milk solids
- #110: ice cream may contain egg
- #115: bottled vinaigrette may contain egg
- #119: dry onion soup mix may contain wheat
- #149: asafoetida powder is often bulked with wheat flour
