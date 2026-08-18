"""Figures for Chapter 5, drawn from the JSON that evaluate.py wrote.

Every figure here reads outputs/eval_*.json rather than any figure taking a
number typed in by hand, so a figure cannot drift from the experiment that
produced it: re-run evaluate.py and re-run this, and the figures follow.

All colours come from figstyle, which is the single source of truth for the
appearance of every figure in the dissertation.  verify_figures.py fails any
figure containing a colour outside that palette, so nothing here may reach for
matplotlib's defaults.

Run:  python code/make_ch5_figures.py
"""

import json
import os

import matplotlib.pyplot as plt
import numpy as np

import figstyle as fs

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "outputs")


def load(name):
    with open(os.path.join(OUT, f"eval_{name}.json"), encoding="utf-8") as f:
        return json.load(f)


def tidy(ax, xlabel=None, ylabel=None, grid_axis="y"):
    ax.tick_params(colors=fs.GREY, labelsize=10)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(fs.GREY)
    if xlabel:
        ax.set_xlabel(xlabel, fontsize=11, color=fs.NAVY)
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=11, color=fs.NAVY)
    ax.grid(axis=grid_axis, color=fs.TINT_GRID, linewidth=1.0)
    ax.set_axisbelow(True)


# ---------------------------------------------------------------------------
# Figure 5.1  Top-N ranking against baselines
# ---------------------------------------------------------------------------
def fig51():
    d = load("ranking")["metrics"]
    systems = ["random", "popularity", "content", "collaborative", "switching"]
    labels = ["Random", "Popularity", "Content-\nbased", "Collaborative",
              "Switching\nhybrid"]
    # The two baselines are grey; the components are blue; the system the
    # design actually deploys is navy, so the eye finds it without a legend.
    colours = [fs.GREY, fs.GREY, fs.BLUE, fs.BLUE, fs.NAVY]

    fig, axes = plt.subplots(1, 2, figsize=(9.6, 4.4))
    for ax, metric, title in zip(axes,
                                 ("precision@10", "ndcg@10"),
                                 ("Precision@10", "NDCG@10")):
        vals = [d[s][metric] for s in systems]
        ax.bar(range(len(systems)), vals, color=colours, width=0.68, zorder=3)
        for i, v in enumerate(vals):
            ax.text(i, v, f"{v:.3f}", ha="center", va="bottom",
                    fontsize=9.5, color=fs.NAVY)
        ax.set_xticks(range(len(systems)))
        ax.set_xticklabels(labels, fontsize=9.5)
        ax.set_title(title, fontsize=12, color=fs.NAVY, pad=10)
        ax.set_ylim(0, max(vals) * 1.28)
        tidy(ax)
    fs.save(fig, "fig51_ranking.png")


# ---------------------------------------------------------------------------
# Figure 5.2  The switching policy, by population
# ---------------------------------------------------------------------------
def fig52():
    d = load("ranking")["by_population"]
    groups = [g for g in ("cold", "warm") if g in d and d[g]]
    systems = ["content", "collaborative", "switching"]
    labels = ["Content-based", "Collaborative", "Switching hybrid"]
    colours = [fs.BLUE, fs.TEAL, fs.NAVY]

    fig, ax = plt.subplots(figsize=(8.6, 4.6))
    width = 0.26
    x = np.arange(len(groups))
    for i, (s, lab, col) in enumerate(zip(systems, labels, colours)):
        vals = [d[g].get(s, 0.0) for g in groups]
        pos = x + (i - 1) * width
        ax.bar(pos, vals, width=width, color=col, label=lab, zorder=3)
        for p, v in zip(pos, vals):
            ax.text(p, v, f"{v:.3f}", ha="center", va="bottom",
                    fontsize=9.2, color=fs.NAVY)

    ax.set_xticks(x)
    ax.set_xticklabels([{"cold": "Fewer than 10 ratings\n(content branch)",
                         "warm": "10 or more ratings\n(collaborative branch)"}[g]
                        for g in groups], fontsize=10.5)
    ax.legend(frameon=False, fontsize=10, labelcolor=fs.NAVY, ncol=3,
              loc="upper center", bbox_to_anchor=(0.5, 1.16))
    tidy(ax, ylabel="NDCG@10")
    ax.set_ylim(0, max(max(d[g].get(s, 0) for s in systems)
                       for g in groups) * 1.30)
    fs.save(fig, "fig52_switching.png")


# ---------------------------------------------------------------------------
# Figure 5.3  Nutritional attainment across profiles
# ---------------------------------------------------------------------------
def fig53():
    rows = load("nutrition")["profiles"]
    names = [r["profile"].split(",")[0] for r in rows]
    energy = [r["energy_kcal"] for r in rows]
    sodium = [r["sodium_mg"] for r in rows]
    fat = [r["fat_g"] for r in rows]

    fig, ax = plt.subplots(figsize=(9.6, 5.2))
    y = np.arange(len(rows))
    h = 0.26
    ax.barh(y + h, energy, height=h, color=fs.BLUE, zorder=3,
            label="Energy, mean of seven days")
    ax.barh(y, fat, height=h, color=fs.TEAL, zorder=3,
            label="Fat, worst day")
    ax.barh(y - h, sodium, height=h, color=fs.NAVY, zorder=3,
            label="Sodium, worst day")

    # The line every bar is measured against: 100 per cent of the target or
    # of the guideline ceiling, depending on the series.
    ax.axvline(100, color=fs.GREY, linewidth=2.0, linestyle="--", zorder=4)
    ax.text(100.8, len(rows) - 0.35, "target / ceiling", fontsize=9.6,
            color=fs.GREY, va="top")

    ax.set_yticks(y)
    ax.set_yticklabels(names, fontsize=9.6)
    ax.invert_yaxis()
    ax.legend(frameon=False, fontsize=10, labelcolor=fs.NAVY, ncol=3,
              loc="upper center", bbox_to_anchor=(0.5, 1.10))
    tidy(ax, xlabel="Per cent of the daily target or ceiling", grid_axis="x")
    ax.set_xlim(0, 118)
    fs.save(fig, "fig53_nutrition.png")


# ---------------------------------------------------------------------------
# Figure 5.4  The weight on exceeding a guideline ceiling
#
# This replaced a figure of the repeat-cap sweep, which would have plotted
# three identical points: the cap never binds, for the reason Section 5.6
# gives.  A flat line is a finding but not a figure, so the finding is stated
# in the text and the space given to a parameter that does something.
# ---------------------------------------------------------------------------
def fig54():
    rows = load("sensitivity")["ceiling_emphasis"]
    weights = [r["ceiling_emphasis"] for r in rows]
    series = [("sugar_g", "Free sugars", fs.NAVY),
              ("satfat_g", "Saturated fat", fs.BLUE),
              ("sodium_mg", "Sodium", fs.TEAL),
              ("fat_g", "Fat", fs.GREY)]

    fig, ax = plt.subplots(figsize=(8.6, 4.8))
    for key, label, col in series:
        vals = [r[key] for r in rows]
        ax.plot(weights, vals, marker="o", markersize=6.5, linewidth=2.4,
                color=col, label=label, zorder=3)

    ax.axhline(100, color=fs.GREY, linewidth=1.8, linestyle="--", zorder=2)
    ax.text(weights[-1], 104, "guideline ceiling", fontsize=9.6,
            color=fs.GREY, ha="right")
    ax.set_yscale("log")
    ax.set_yticks([100, 200, 400, 600])
    ax.set_yticklabels(["100%", "200%", "400%", "600%"])
    ax.set_xticks(weights)
    ax.legend(frameon=False, fontsize=10, labelcolor=fs.NAVY, ncol=4,
              loc="upper center", bbox_to_anchor=(0.5, 1.14))
    tidy(ax, xlabel="Weight on exceeding a ceiling in the nutritional term",
         ylabel="Worst day, per cent of the ceiling")
    fs.save(fig, "fig54_ceiling_weight.png")


FIGURES = {"fig51": fig51, "fig52": fig52, "fig53": fig53, "fig54": fig54}

if __name__ == "__main__":
    import sys
    wanted = sys.argv[1:] or list(FIGURES)
    for name in wanted:
        FIGURES[name]()
        print(f"  {name} written")
