"""Score the revised allergen lexicon on the INDEPENDENT second sample.

This is the measurement Section 4.2 of the dissertation promises and the one
Chapter 5 quotes.  The first sample cannot supply it: the lexicon was revised
using the errors found there, so its recall on that sample is an estimate of
how thoroughly the repair was applied rather than of how well the rules
generalise.  Here the rules meet 104 recipes they were not built from.

Recall is the quantity that matters, because a false negative is the failure
that can cause harm.  Precision is reported beside it because the fail-closed
design deliberately trades precision away, and the size of that trade should be
visible rather than implied.

Run:  python code/score_allergen_gt2.py
Out:  code/outputs/allergen_eval2.md       table for Chapter 5
      code/outputs/allergen_errors2.csv    every disagreement, for inspection
"""

import ast
import os

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "outputs")

from allergen_ground_truth2 import CLASS_OF, LABELS  # noqa: E402

sample = pd.read_csv(os.path.join(OUT, "allergen_sample2.csv"))
rules = pd.read_csv(os.path.join(OUT, "allergen_sample2_rules.csv"))
assert len(sample) == len(LABELS) == len(rules), "sample / labels out of step"

# The independence of this sample is the whole point, so it is asserted here
# too rather than trusted to the sampler that produced it.
first = pd.read_csv(os.path.join(OUT, "allergen_sample.csv"))
overlap = set(sample["id"].astype(int)) & set(first["id"].astype(int))
assert not overlap, f"sample overlaps the first: {overlap}"

CLASSES = ["gluten", "milk", "eggs", "fish"]

rows, errors = [], []
for cls in CLASSES:
    code = [k for k, v in CLASS_OF.items() if v == cls][0]
    tp = fp = fn = tn = 0
    for i in range(len(sample)):
        truth = code in LABELS[i + 1]
        pred = bool(rules[cls].iloc[i])
        if truth and pred:
            tp += 1
        elif truth and not pred:
            fn += 1
            errors.append({"idx": i + 1, "class": cls, "type": "false negative",
                           "name": str(sample["name"].iloc[i]).strip(),
                           "ingredients": sample["ingredients"].iloc[i]})
        elif pred and not truth:
            fp += 1
            errors.append({"idx": i + 1, "class": cls, "type": "false positive",
                           "name": str(sample["name"].iloc[i]).strip(),
                           "ingredients": sample["ingredients"].iloc[i]})
        else:
            tn += 1
    rows.append({"class": cls, "present": tp + fn, "TP": tp, "FN": fn,
                 "FP": fp, "TN": tn,
                 "recall": tp / (tp + fn) if tp + fn else float("nan"),
                 "precision": tp / (tp + fp) if tp + fp else float("nan")})

res = pd.DataFrame(rows)
err = pd.DataFrame(errors)

print("=" * 74)
print(f"REVISED LEXICON vs MANUAL GROUND TRUTH, INDEPENDENT SAMPLE "
      f"(n = {len(sample)})")
print("=" * 74)
print(f"{'class':<10}{'present':>8}{'TP':>6}{'FN':>5}{'FP':>5}"
      f"{'recall':>9}{'precision':>11}")
for _, r in res.iterrows():
    print(f"{r['class']:<10}{r['present']:>8}{r['TP']:>6}{r['FN']:>5}"
          f"{r['FP']:>5}{r['recall']:>9.3f}{r['precision']:>11.3f}")

tot_tp, tot_fn, tot_fp = res["TP"].sum(), res["FN"].sum(), res["FP"].sum()
micro_r = tot_tp / (tot_tp + tot_fn)
micro_p = tot_tp / (tot_tp + tot_fp)
print("-" * 74)
print(f"{'micro':<10}{res['present'].sum():>8}{tot_tp:>6}{tot_fn:>5}"
      f"{tot_fp:>5}{micro_r:>9.3f}{micro_p:>11.3f}")
print(f"\nfalse-negative rate (micro): {100 * (1 - micro_r):.1f} per cent")

print("\n" + "=" * 74)
print("FALSE NEGATIVES  (the safety-critical errors)")
print("=" * 74)
fns = err[err["type"] == "false negative"] if not err.empty else err
if fns.empty:
    print("none")
else:
    for _, e in fns.iterrows():
        print(f"\n[{e['idx']}] {e['class']}: {e['name']}")
        print("     " + ", ".join(ast.literal_eval(e["ingredients"])))

if not err.empty:
    err.to_csv(os.path.join(OUT, "allergen_errors2.csv"), index=False)

with open(os.path.join(OUT, "allergen_eval2.md"), "w", encoding="utf-8") as f:
    f.write("# Allergen lexicon on an independent sample\n\n")
    f.write(f"> {len(sample)} recipes, stratified on the rule outcome for four "
            f"classes, drawn with a different seed and **excluding every recipe "
            f"in the first sample**. The revised lexicon has not been changed "
            f"in response to anything found here, so these figures are "
            f"unbiased estimates of its behaviour.\n\n")
    f.write("| Class | Truly present | TP | FN | FP | Recall | Precision |\n")
    f.write("|---|---:|---:|---:|---:|---:|---:|\n")
    for _, r in res.iterrows():
        f.write(f"| {r['class']} | {r['present']} | {r['TP']} | {r['FN']} | "
                f"{r['FP']} | {r['recall']:.3f} | {r['precision']:.3f} |\n")
    f.write(f"| **micro** | {res['present'].sum()} | {tot_tp} | {tot_fn} | "
            f"{tot_fp} | **{micro_r:.3f}** | {micro_p:.3f} |\n\n")
    f.write(f"- false-negative rate: **{100 * (1 - micro_r):.1f} per cent**\n")
    f.write(f"- false positives: {tot_fp}\n")
print("\nwrote outputs/allergen_eval2.md")
