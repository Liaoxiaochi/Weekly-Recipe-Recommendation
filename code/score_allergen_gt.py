"""Score the allergen lexicon against the manual ground truth.

Recall is the quantity that matters: it is one minus the false-negative rate,
and a false negative is the failure mode that can cause harm.  Precision is
reported alongside it because the fail-closed design deliberately trades
precision away, and the size of that trade should be visible.

Run:  python code/score_allergen_gt.py
Out:  code/outputs/allergen_eval.md      table for Chapter 5
      code/outputs/allergen_errors.csv   every disagreement, for inspection
"""

import ast
import os

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "outputs")

from allergen_ground_truth import BORDERLINE, CODE, LABELS

sample = pd.read_csv(os.path.join(OUT, "allergen_sample.csv"))
rules = pd.read_csv(os.path.join(OUT, "allergen_sample_rules.csv"))
assert len(sample) == len(LABELS) == len(rules), "sample / labels out of step"

CLASSES = ["gluten", "milk", "eggs", "fish"]

rows, errors = [], []
for cls in CLASSES:
    code = [k for k, v in CODE.items() if v == cls][0]
    tp = fp = fn = tn = 0
    for i in range(len(sample)):
        truth = code in LABELS[i + 1]
        pred = bool(rules[cls].iloc[i])
        if truth and pred:
            tp += 1
        elif truth and not pred:
            fn += 1
            errors.append({"idx": i + 1, "class": cls, "type": "false negative",
                           "name": sample["name"].iloc[i].strip(),
                           "ingredients": sample["ingredients"].iloc[i]})
        elif pred and not truth:
            fp += 1
            errors.append({"idx": i + 1, "class": cls, "type": "false positive",
                           "name": sample["name"].iloc[i].strip(),
                           "ingredients": sample["ingredients"].iloc[i]})
        else:
            tn += 1
    recall = tp / (tp + fn) if tp + fn else float("nan")
    prec = tp / (tp + fp) if tp + fp else float("nan")
    rows.append({"class": cls, "present": tp + fn, "TP": tp, "FN": fn,
                 "FP": fp, "TN": tn,
                 "recall": recall, "precision": prec})

res = pd.DataFrame(rows)
err = pd.DataFrame(errors)

print("=" * 74)
print(f"ALLERGEN TAGGING vs MANUAL GROUND TRUTH   (n = {len(sample)} recipes)")
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
print(f"\nfalse-negative rate (micro): {100*(1-micro_r):.1f} per cent")

print("\n" + "=" * 74)
print("FALSE NEGATIVES  (the safety-critical errors)")
print("=" * 74)
if err.empty:
    print("none")
else:
    for _, e in err[err["type"] == "false negative"].iterrows():
        ings = ", ".join(ast.literal_eval(e["ingredients"]))
        print(f"\n[{e['idx']}] {e['class']}: {e['name'][:52]}")
        print(f"     {ings[:150]}")

    print("\n" + "=" * 74)
    print("FALSE POSITIVES  (the cost of the fail-closed policy)")
    print("=" * 74)
    for _, e in err[err["type"] == "false positive"].iterrows():
        print(f"[{e['idx']}] {e['class']}: {e['name'][:60]}")

res.to_csv(os.path.join(OUT, "allergen_eval.csv"), index=False)
err.to_csv(os.path.join(OUT, "allergen_errors.csv"), index=False)

lines = [
    "# Allergen tagging: measured against manual ground truth", "",
    f"Stratified sample of {len(sample)} recipes, labelled by hand for the "
    "four classes the sample is stratified on. Strata deliberately include "
    "recipes the rules called negative, because that is where false negatives "
    "hide.", "",
    "| Class | Truly present | TP | FN | FP | Recall | Precision |",
    "|---|---:|---:|---:|---:|---:|---:|",
]
for _, r in res.iterrows():
    lines.append(f"| {r['class']} | {r['present']} | {r['TP']} | {r['FN']} | "
                 f"{r['FP']} | {r['recall']:.3f} | {r['precision']:.3f} |")
lines.append(f"| **micro** | {res['present'].sum()} | {tot_tp} | {tot_fn} | "
             f"{tot_fp} | **{micro_r:.3f}** | **{micro_p:.3f}** |")
lines += ["", f"Micro false-negative rate: **{100*(1-micro_r):.1f} per cent**.",
          "", "## False negatives", ""]
for _, e in err[err["type"] == "false negative"].iterrows():
    lines.append(f"- **{e['class']}** in *{e['name']}* (sample #{e['idx']})")
lines += ["", "## Borderline judgements", "",
          "Recorded as absent, which makes the recall estimate a lower bound:",
          ""]
for k, v in BORDERLINE.items():
    lines.append(f"- #{k}: {v}")
lines.append("")

with open(os.path.join(OUT, "allergen_eval.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("\nwrote outputs/allergen_eval.md and allergen_eval.csv")
