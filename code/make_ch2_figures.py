"""Chapter 2 figures, rebuilt through figstyle.

These two figures previously existed only as PNGs with no source, which is
how the style drift began: there was nothing for later figures to conform
to, and neither figure could be edited without redrawing it by hand.

Figure 2.2 also drops the USDA branch, superseded by design decision DD-2
(nutrition is taken from the corpus's own per-serving fields).

Run:  python code/make_ch2_figures.py
"""

import os

import figstyle as fs

HERE = os.path.dirname(os.path.abspath(__file__))


def fig21():
    """Taxonomy of recipe-recommendation approaches."""
    fig, ax = fs.canvas(12.2, 6.6)

    fs.box(ax, 33, 80, 34, 15,
           title="Recipe Recommendation\nApproaches", fill=fs.NAVY,
           title_size=13.5)

    families = [
        (1.5, "Content-based",
         "Ingredient / TF-IDF\nsimilarity [23,24]", True),
        (26.0, "Collaborative\nFiltering",
         "Memory-based &\nmatrix factorisation\n[18,25,26]", True),
        (50.5, "Hybrid /\nContext-aware",
         "Switching hybrid +\nweekday/weekend\ncontext [18,27]", True),
        (75.0, "Knowledge-aware\n& Graph",
         "Food ontology &\nheterogeneous GNN\n[19,22]", False),
    ]
    w = 23.5
    for x, name, detail, adopted in families:
        fs.box(ax, x, 52, w, 15, title=name, fill=fs.BLUE, title_size=12.0)
        fs.box(ax, x, 24, w, 18, body=detail, fill=fs.TEAL,
               emphasis=adopted, body_size=10.2)
        cx = x + w / 2
        fs.connector(ax, (50, 80), (cx, 67))
        fs.connector(ax, (cx, 52), (cx, 42))

    fs.note(ax, "Bold path adopted in this project: a switching hybrid over a "
                "content-based / matrix-factorisation core,\nwith "
                "hard-then-soft constraint handling and weekday/weekend "
                "context.", y=3)

    fs.save(fig, "fig21_taxonomy.png")


def fig22():
    """Filter-then-rank pipeline.  USDA branch removed per DD-2."""
    fig, ax = fs.canvas(12.2, 5.9)

    fs.title(ax, "Filter-then-rank pipeline of the proposed system", y=98)

    inputs = [
        (66, "User Profile", "preferences · restrictions", fs.BLUE),
        (41, "Nutritional Target", "from anthropometrics", fs.BLUE),
        (16, "Recipe Corpus", "Food.com · per-serving\nnutrition · allergens",
         fs.GREY),
    ]
    for y, name, detail, fill in inputs:
        fs.box(ax, 1, y, 26, 19, title=name, body=detail, fill=fill,
               title_size=12.0, body_size=9.8)
        fs.arrow(ax, (27, y + 9.5), (37, 50))

    fs.box(ax, 37, 34, 23, 33,
           title="Hard-constraint\nFilter",
           body="allergens · religious ·\nclinical exclusions",
           fill=fs.TEAL, title_size=12.0, body_size=9.8)

    fs.arrow(ax, (60, 50), (68, 50))

    fs.box(ax, 68, 34, 26, 33,
           title="Hybrid Ranking",
           body="content ⇄ collaborative\nswitch  +  soft-penalty\n"
                "& weekday/weekend",
           fill=fs.NAVY, title_size=12.0, body_size=9.8)

    fs.box(ax, 68, 12, 26, 15, title="7-Day\nMeal Plan", fill=fs.TEAL,
           title_size=12.5)
    fs.arrow(ax, (81, 34), (81, 27))

    fs.note(ax, "Hard constraints prune the candidate set before any ranking; "
                "soft preferences are applied as penalties, never as "
                "exclusions.", y=1)

    fs.save(fig, "fig22_pipeline.png")


if __name__ == "__main__":
    print("Chapter 2 figures:")
    fig21()
    fig22()
