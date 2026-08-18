"""Re-score the revised lexicon on the SAME 160 recipes as version 1.

Methodological warning, stated here and repeated in the output because it
governs how the number may be used:

    The v2 lexicon was extended using the errors found on this very sample.
    Its recall on this sample is therefore an IN-SAMPLE, optimistically
    biased figure.  It shows that the identified gaps were closed; it does
    NOT estimate the false-negative rate on unseen recipes.  The unbiased
    v1 figure is the one to quote as an estimate, and an unbiased v2 figure
    requires a fresh sample, which is registered as outstanding work for
    Chapter 5.

The sample itself is NOT redrawn: sample_allergen_gt.py stratifies on the
rule outcome, so re-running it under the new rules would select different
recipes and invalidate the manual labels.

Run:  python code/rescore_allergen_v2.py
"""

import ast
import os

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "outputs")

from allergen_ground_truth import CODE, LABELS
from allergen_lexicon import build_matcher, fires

CLASSES = ["gluten", "milk", "eggs", "fish"]

sample = pd.read_csv(os.path.join(OUT, "allergen_sample.csv"))
v1 = pd.read_csv(os.path.join(OUT, "allergen_sample_rules.csv"))
assert len(sample) == len(LABELS) == len(v1)

matcher = build_matcher()
ing_text = sample["ingredients"].map(
    lambda s: " | ".join(ast.literal_eval(s)).lower())

v2 = pd.DataFrame({c: ing_text.map(lambda t, c=c: fires(t, c, matcher))
                   for c in CLASSES})
v2.insert(0, "recipe_id", sample["id"].values)
v2.to_csv(os.path.join(OUT, "allergen_sample_rules_v2.csv"), index=False)


def score(pred):
    out = []
    for cls in CLASSES:
        code = [k for k, v in CODE.items() if v == cls][0]
        tp = fp = fn = 0
        for i in range(len(sample)):
            truth = code in LABELS[i + 1]
            p = bool(pred[cls].iloc[i])
            if truth and p:
                tp += 1
            elif truth and not p:
                fn += 1
            elif p and not truth:
                fp += 1
        out.append({"class": cls, "present": tp + fn, "TP": tp, "FN": fn,
                    "FP": fp,
                    "recall": tp / (tp + fn) if tp + fn else float("nan"),
                    "precision": tp / (tp + fp) if tp + fp else float("nan")})
    return pd.DataFrame(out)


a, b = score(v1), score(v2)

print("=" * 76)
print("ALLERGEN LEXICON  v1 -> v2   (same 160 recipes, same manual labels)")
print("=" * 76)
print(f"{'class':<9}{'present':>8}{'FN v1':>7}{'FN v2':>7}"
      f"{'recall v1':>11}{'recall v2':>11}{'prec v1':>9}{'prec v2':>9}")
for i in range(len(a)):
    ra, rb = a.iloc[i], b.iloc[i]
    print(f"{ra['class']:<9}{ra['present']:>8}{ra['FN']:>7}{rb['FN']:>7}"
          f"{ra['recall']:>11.3f}{rb['recall']:>11.3f}"
          f"{ra['precision']:>9.3f}{rb['precision']:>9.3f}")


def micro(d):
    tp, fn, fp = d["TP"].sum(), d["FN"].sum(), d["FP"].sum()
    return tp / (tp + fn), tp / (tp + fp), fn, fp


ra, pa, fna, fpa = micro(a)
rb, pb, fnb, fpb = micro(b)
print("-" * 76)
print(f"{'micro':<9}{a['present'].sum():>8}{fna:>7}{fnb:>7}"
      f"{ra:>11.3f}{rb:>11.3f}{pa:>9.3f}{pb:>9.3f}")
print(f"\nfalse negatives : {fna} -> {fnb}")
print(f"false positives : {fpa} -> {fpb}")
print(f"\nv1 false-negative rate: {100*(1-ra):.1f} per cent   "
      f"(unbiased, sample not used to build v1)")
print(f"v2 false-negative rate: {100*(1-rb):.1f} per cent   "
      f"*** IN-SAMPLE, OPTIMISTICALLY BIASED ***")

rem = []
for cls in CLASSES:
    code = [k for k, v in CODE.items() if v == cls][0]
    for i in range(len(sample)):
        if code in LABELS[i + 1] and not bool(v2[cls].iloc[i]):
            rem.append((i + 1, cls, sample["name"].iloc[i].strip()))
print("\nremaining false negatives after v2:")
if rem:
    for i, c, n in rem:
        print(f"   [{i}] {c}: {n[:56]}")
else:
    print("   none on this sample (which is what in-sample means)")

lines = [
    "# Allergen lexicon: v1 measured, v2 after closing the gaps", "",
    "> **The v2 column is in-sample.** The lexicon was extended using the "
    "errors found on this sample, so its recall here is optimistically "
    "biased. Quote the v1 figure as the estimate of the false-negative rate; "
    "an unbiased v2 figure needs a fresh sample.", "",
    "| Class | Truly present | FN v1 | FN v2 | Recall v1 | Recall v2 | "
    "Precision v1 | Precision v2 |",
    "|---|---:|---:|---:|---:|---:|---:|---:|",
]
for i in range(len(a)):
    x, y = a.iloc[i], b.iloc[i]
    lines.append(f"| {x['class']} | {x['present']} | {x['FN']} | {y['FN']} | "
                 f"{x['recall']:.3f} | {y['recall']:.3f} | "
                 f"{x['precision']:.3f} | {y['precision']:.3f} |")
lines.append(f"| **micro** | {a['present'].sum()} | {fna} | {fnb} | "
             f"**{ra:.3f}** | *{rb:.3f}* | {pa:.3f} | {pb:.3f} |")
lines += ["",
          f"- v1 false-negative rate: **{100*(1-ra):.1f} per cent** (unbiased)",
          f"- v2 false-negative rate: *{100*(1-rb):.1f} per cent* (in-sample)",
          f"- false positives: {fpa} to {fpb}", ""]
with open(os.path.join(OUT, "allergen_eval_v1_v2.md"), "w",
          encoding="utf-8") as f:
    f.write("\n".join(lines))
print("\nwrote outputs/allergen_eval_v1_v2.md")
