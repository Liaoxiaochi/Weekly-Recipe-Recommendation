"""Chapter 3 figures, all drawn through figstyle.

Do not set colours, rounding or fonts here.  Everything visual comes from
figstyle so that Chapters 2 to 6 cannot drift apart; verify_figures.py
enforces it.

Figures produced:
  fig31_architecture.png     layered architecture              (3.1)
  fig33_data_pipeline.png    data preparation pipeline         (3.2)
  fig34_interactions.png     interactions per user, real data  (3.4.3)
  fig35_constraints.png      constraint handling               (3.5)
  fig36_cards.png            weekly plan card interface        (3.7.2)

Figure 3.2 is a screenshot of a Food.com recipe page and is supplied by the
author, not generated here.

Run:  python code/make_ch3_figures.py
"""

import json
import pickle
import os

import figstyle as fs
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle

HERE = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(HERE, "outputs", "dataset_profile.json"),
          encoding="utf-8") as f:
    P = json.load(f)

# The accompaniment pool post-dates the profiling run, so its size is read from
# the corpus the pipeline actually produced rather than from the profile.  Read
# here so that no figure ever carries a hand-typed number.
with open(os.path.join(HERE, "outputs", "corpus.pkl"), "rb") as f:
    SIDE_POOL = int(pickle.load(f)["is_side"].sum())


# ---------------------------------------------------------------------------
# Figure 3.1  Layered architecture
# ---------------------------------------------------------------------------
def fig31():
    fig, ax = fs.canvas(12.2, 8.0)

    rows = [
        (78, "Presentation", [
            ("Profile &\nconstraint form", fs.BLUE),
            ("Seven-day\nplan view", fs.BLUE),
            ("Recipe card\n(full ingredients)", fs.BLUE)]),
        (56, "Application", [
            ("Weekly planner", fs.TEAL),
            ("Constraint engine", fs.TEAL)]),
        (30, "Model", [
            ("Content-based\nrecommender", fs.BLUE),
            ("Collaborative\nrecommender", fs.BLUE),
            ("User model", fs.BLUE)]),
        (4, "Data", [
            ("Recipe corpus\n%s recipes" % f"{P['n_recipes_after_cleaning']:,}",
             fs.GREY),
            ("Interaction matrix\n%s ratings"
             % f"{P['n_interactions_on_clean_corpus']:,}", fs.GREY),
            ("Nutrition (g)\n+ allergen tags", fs.GREY)]),
    ]

    L, R = 14.0, 99.0
    for y, layer, boxes in rows:
        n = len(boxes)
        gap = 3.0
        w = (R - L - gap * (n - 1)) / n
        for i, (text, fill) in enumerate(boxes):
            fs.box(ax, L + i * (w + gap), y, w, 15, body=text, fill=fill,
                   body_size=10.2)
        fs.label(ax, 7.0, y + 7.5, layer, colour=fs.NAVY, size=10.8,
                 italic=True)

    # switching controller sits across the two recommenders
    fs.box(ax, 14, 46, 57.3, 6.5, title="Switching controller", fill=fs.NAVY,
           title_size=11.0)

    W3 = (R - L - 6.0) / 3
    c = [L + W3 / 2, L + W3 + 3 + W3 / 2, L + 2 * (W3 + 3) + W3 / 2]

    fs.arrow(ax, (c[0], 78), (c[0], 71))          # form     -> planner
    fs.arrow(ax, (c[1], 71), (c[1], 78))          # planner  -> plan view
    fs.arrow(ax, (c[2], 71), (c[2], 78))          # engine   -> recipe card
    fs.arrow(ax, (c[0], 56), (c[0], 52.5))        # planner  -> controller
    fs.arrow(ax, (c[2], 56), (c[2], 45))          # engine   -> user model
    fs.arrow(ax, (c[0], 46), (c[0], 45))
    fs.arrow(ax, (c[1], 46), (c[1], 45))
    for cx in c:
        fs.arrow(ax, (cx, 30), (cx, 19))          # model    <- data

    fs.note(ax, "Each layer depends only on the layer beneath it, so a "
                "recommender can be replaced without altering the planner "
                "or the interface.", y=0)

    fs.save(fig, "fig31_architecture.png")


# ---------------------------------------------------------------------------
# Figure 3.3  Data preparation pipeline
# ---------------------------------------------------------------------------
def fig33():
    fig, ax = fs.canvas(11.6, 9.0)

    fs.box(ax, 2, 88, 45, 11,
           title="RAW_recipes.csv", body=f"{P['n_recipes_raw']:,} recipes",
           fill=fs.GREY, title_size=11.0, body_size=10.0)
    fs.box(ax, 53, 88, 45, 11,
           title="RAW_interactions.csv",
           body=f"{P['n_interactions_raw']:,} ratings",
           fill=fs.GREY, title_size=11.0, body_size=10.0)

    # The eight validity rules, that is every cleaning rule except the course
    # tag one, which is where the pipeline forks rather than simply discards.
    validity_dropped = sum(
        d["n_newly_dropped"] for name, d in P["cleaning_rules"].items()
        if name != "not assignable to a meal slot")
    after_validity = P["n_recipes_raw"] - validity_dropped
    mains = P["n_recipes_after_cleaning"]
    discarded = after_validity - mains - SIDE_POOL

    steps = [
        (73, "Parse and validate", "nutrition tuple, ingredient and tag lists",
         fs.BLUE),
        (59, "Apply validity rules",
         f"{after_validity:,} retained; {validity_dropped:,} removed for "
         f"implausible energy, time or structure", fs.BLUE),
        (45, "Normalise nutrition",
         "percentages of a daily value converted to grams", fs.TEAL),
        (31, "Normalise ingredients",
         f"{P['pct_ingredient_occurrences_matched']}% of ingredient "
         f"occurrences resolved", fs.TEAL),
        (17, "Tag allergens",
         "three-layer lexicon over the fourteen EU classes", fs.TEAL),
    ]
    for y, head, sub, fill in steps:
        fs.box(ax, 12, y, 76, 11, title=head, body=sub, fill=fill,
               title_size=11.5, body_size=9.6)

    # The course tag decides the fork.  A recipe carrying one becomes a main
    # dish; one tagged as something served beside a meal joins the
    # accompaniment pool; the remainder leaves the pipeline.
    fs.box(ax, 1, 0.5, 40, 10.5,
           title=f"Main dishes  {mains:,}",
           body=f"breakfast {P['clean_meal_slot_counts']['breakfast']:,}  ·  "
                f"lunch {P['clean_meal_slot_counts']['lunch']:,}\n"
                f"dinner {P['clean_meal_slot_counts']['dinner']:,}",
           fill=fs.BLUE, title_size=11.5, body_size=9.6)
    fs.box(ax, 45, 0.5, 30, 10.5,
           title=f"Accompaniments  {SIDE_POOL:,}",
           body="served beside a meal,\nnot as one",
           fill=fs.NAVY, title_size=11.0, body_size=9.6)
    fs.box(ax, 79, 0.5, 20, 10.5,
           title=f"Discarded  {discarded:,}",
           body="no usable\ncourse tag",
           fill=fs.GREY, title_size=11.0, body_size=9.6)

    fs.arrow(ax, (24, 88), (38, 84))
    fs.arrow(ax, (76, 88), (62, 84))
    for a, b in [(73, 70), (59, 56), (45, 42), (31, 28)]:
        fs.arrow(ax, (50, a), (50, b))
    # Labels sit directly above their destination, clear of every arrow line.
    for x_from, x_to, text in [(40, 21, "meal course tag"),
                               (50, 60, "side-dish tag"),
                               (60, 89, "neither")]:
        fs.arrow(ax, (x_from, 17), (x_to, 14.6))
        fs.label(ax, x_to, 12.9, text, size=8.8, italic=True)

    fs.save(fig, "fig33_data_pipeline.png")


# ---------------------------------------------------------------------------
# Figure 3.4  Interactions per user -- real data, replaces the old flowchart
# ---------------------------------------------------------------------------
def fig34():
    fig, ax = plt.subplots(figsize=(9.2, 5.0))

    d = P["users_with_at_least"]
    ns = sorted(int(k) for k in d)
    pct = [d[str(n)]["pct"] for n in ns]

    ax.plot(ns, pct, marker="o", markersize=6, linewidth=2.4,
            color=fs.BLUE, zorder=3)
    ax.fill_between(ns, pct, color=fs.TINT_FILL, zorder=1)

    chosen = 10
    ax.axvline(chosen, color=fs.TEAL, linewidth=2.2, linestyle="--", zorder=2)
    ax.annotate(f"adopted threshold  N = {chosen}\n"
                f"only {d[str(chosen)]['pct']}% of users ever reach\n"
                f"the collaborative branch",
                xy=(chosen, d[str(chosen)]["pct"]), xytext=(2.35, 62),
                fontsize=10.5, color=fs.NAVY, ha="left",
                arrowprops=dict(arrowstyle="-|>", color=fs.GREY, linewidth=1.8,
                                shrinkA=6, shrinkB=6))

    for n, dy in ((5, 8.5), (20, 8.5)):     # labelled in place, no leader lines
        ax.text(n, d[str(n)]["pct"] + dy, f"{d[str(n)]['pct']}%",
                fontsize=9.8, color=fs.GREY, ha="center", va="bottom")

    ax.set_xscale("log")
    ax.set_xticks(ns)
    ax.set_xticklabels([str(n) for n in ns], fontsize=10)
    ax.set_xlabel("N  (minimum number of rated recipes)", fontsize=11,
                  color=fs.NAVY)
    ax.set_ylabel("Users with at least N ratings (%)", fontsize=11,
                  color=fs.NAVY)
    ax.set_ylim(0, 104)
    ax.tick_params(colors=fs.GREY, labelsize=10)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(fs.GREY)
    ax.grid(axis="y", color=fs.TINT_GRID, linewidth=1.0)
    ax.set_axisbelow(True)

    fs.save(fig, "fig34_interactions.png")


# ---------------------------------------------------------------------------
# Figure 3.5  Constraint handling
# ---------------------------------------------------------------------------
def fig35():
    fig, ax = fs.canvas(12.2, 7.6)

    fs.box(ax, 26, 89, 48, 9,
           body=f"Candidate recipes  ({P['n_recipes_after_cleaning']:,})",
           fill=fs.GREY, body_size=10.6)

    fs.label(ax, 3, 74, "Stage 1", colour=fs.NAVY, size=11.0, ha="left",
             bold=True)
    fs.label(ax, 3, 70, "hard filter", colour=fs.GREY, size=9.8, ha="left",
             italic=True)
    hard = ["Allergens\n(EU 14 classes)", "Religious and\nethical rules",
            "Clinical\nexclusions", "Unresolved\ningredient"]
    for i, t in enumerate(hard):
        fs.box(ax, 20 + i * 20, 66, 18, 13, body=t, fill=fs.NAVY,
               body_size=9.6)

    fs.label(ax, 50, 61.5,
             "fail-closed: a recipe that cannot be shown to be free of a "
             "declared allergen is discarded",
             colour=fs.TEAL, size=9.8, bold=True)

    fs.label(ax, 3, 46, "Stage 2", colour=fs.NAVY, size=11.0, ha="left",
             bold=True)
    fs.label(ax, 3, 42, "soft penalty", colour=fs.GREY, size=9.8, ha="left",
             italic=True)
    soft = ["Energy\ndeviation", "Macronutrient\ndeviation",
            "Repetition /\ndiversity", "Preparation\ntime"]
    for i, t in enumerate(soft):
        fs.box(ax, 20 + i * 20, 38, 18, 13, body=t, fill=fs.TEAL,
               body_size=9.6)

    fs.label(ax, 50, 33.5,
             "penalised, never removed -- the recipe keeps its place in the "
             "ranking at a lower score", colour=fs.GREY, size=9.8)

    fs.label(ax, 3, 21, "Stage 3", colour=fs.NAVY, size=11.0, ha="left",
             bold=True)
    fs.label(ax, 3, 17, "relaxation", colour=fs.GREY, size=9.8, ha="left",
             italic=True)
    fs.box(ax, 20, 14, 36, 13,
           body="Soft weights loosened in a\nfixed order when too few\n"
                "candidates remain", fill=fs.BLUE, body_size=9.6)
    fs.box(ax, 60, 14, 38, 13,
           body="Allergen filters are never\nrelaxed: an incomplete plan is\n"
                "returned and the gap reported", fill=fs.NAVY,
           emphasis=True, body_size=9.6)

    fs.arrow(ax, (50, 89), (50, 79))
    fs.arrow(ax, (50, 66), (50, 51))
    fs.arrow(ax, (38, 38), (38, 27))
    fs.arrow(ax, (56, 20.5), (60, 20.5))
    fs.arrow(ax, (38, 14), (38, 8))
    fs.box(ax, 14, -2, 48, 9, body="Ranked, constraint-respecting candidates",
           fill=fs.GREY, body_size=10.6)

    fs.save(fig, "fig35_constraints.png")


# ---------------------------------------------------------------------------
# Figure 3.6  Weekly plan as cards, with click-to-replace
# ---------------------------------------------------------------------------
def fig36():
    fig, ax = fs.canvas(12.2, 7.2)

    fs.title(ax, "Weekly plan presented as replaceable cards", y=99)

    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    meals = ["Breakfast", "Lunch", "Dinner"]
    x0, top = 13.0, 80.0
    cw, ch, gx, gy = 11.4, 14.0, 1.2, 2.0

    for i, day in enumerate(days):          # day labels above the top row
        xx = x0 + i * (cw + gx)
        fs.label(ax, xx + cw / 2, top + 3.0, day,
                 colour=fs.TEAL if i >= 5 else fs.NAVY, size=10.2,
                 bold=i >= 5)

    for k, meal in enumerate(meals):        # rows run top-down
        yy = top - k * (ch + gy) - ch
        fs.label(ax, 11.5, yy + ch / 2, meal, colour=fs.NAVY, size=9.8,
                 ha="right")
        for i in range(len(days)):
            fs.box(ax, x0 + i * (cw + gx), yy, cw, ch,
                   fill=fs.TEAL if i >= 5 else fs.BLUE)

    # one card enlarged to show what it carries
    ex, ey, ew, eh = 28.0, 2.0, 44.0, 26.0
    fs.box(ax, ex, ey, ew, eh, fill=fs.NAVY)
    fs.label(ax, ex + 3.0, ey + 22.5, "Tue  ·  Dinner",
             colour=fs.WHITE, size=9.4, ha="left", italic=True)
    fs.label(ax, ex + 3.0, ey + 17.0, "Lemon Herb Chicken",
             colour=fs.WHITE, size=12.0, ha="left", bold=True)
    fs.label(ax, ex + 3.0, ey + 12.0, "520 kcal   ·   35 min",
             colour=fs.WHITE, size=10.0, ha="left")
    fs.label(ax, ex + 3.0, ey + 7.5, "contains milk, gluten",
             colour=fs.WHITE, size=9.6, ha="left")
    fs.label(ax, ex + 3.0, ey + 3.0,
             "full ingredient list        replace",
             colour=fs.WHITE, size=9.2, ha="left", italic=True)

    fs.arrow(ax, (34.0, 31.0), (42.0, 28.5))

    fs.box(ax, 77, 8, 22, 14,
           body="Replace takes the\nnext candidate that\nstill passes every\n"
                "hard constraint", fill=fs.TEAL, body_size=9.2)
    fs.arrow(ax, (72, 15), (77, 15))

    fs.note(ax, "The corpus carries no recipe images, so a card is identified "
                "by name, energy, preparation time and allergen flags. "
                "Weekend cards are shown in the lighter colour.", y=-7)

    fs.save(fig, "fig36_cards.png")


if __name__ == "__main__":
    # fig35 and fig36 are retired.  The constraint diagram duplicated the
    # filter-then-rank pipeline of Figure 2.2, and the card sketch duplicated
    # Figure 4.2, which is a photograph of the interface as built rather than a
    # drawing of the intention.  Both functions are kept so either can be
    # restored; their PNGs live in figures/_retired/, which verify_figures.py
    # does not scan.
    print("Chapter 3 figures:")
    fig31()
    fig33()
    fig34()
