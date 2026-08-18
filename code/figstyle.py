"""Single source of truth for every figure in the dissertation.

WHY THIS FILE EXISTS
--------------------
The house style used to live only inside two PNG files with no source code.
When new figures were drawn there was nothing to conform to, so a second,
incompatible style appeared: white boxes with coloured outlines instead of
the original solid fills with white text.  Fixing the drift once does not
prevent it recurring in Chapters 4 to 6.

So the style now lives here, in code:

  * Every figure in figures/ is generated through these primitives.
  * No drawing script may call matplotlib's patch API directly.
  * verify_figures.py fails if a figure contains a colour outside PALETTE.
  * CLAUDE.md records the rule so a future session inherits it.

To restyle the whole dissertation, change this file and re-run the drawing
scripts.  Do not restyle an individual figure in its own script.
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

# ---------------------------------------------------------------------------
# Approved palette.  verify_figures.py asserts that no figure contains any
# other colour at more than a trace proportion of its pixels.
# ---------------------------------------------------------------------------
NAVY = "#1f3a5f"
BLUE = "#2e6ca4"
TEAL = "#2e8b84"
GREY = "#556069"
WHITE = "#ffffff"

# Two light tints, for chart gridlines and area fills.  They are declared
# here, and drawn at full opacity, because an alpha blend produces a colour
# that is in no palette and so trips verify_figures.py.  Never use alpha to
# lighten something -- add the tint you want to this list instead.
TINT_GRID = "#e6e9ec"
TINT_FILL = "#e8eef6"

PALETTE = {
    "navy": NAVY,
    "blue": BLUE,
    "teal": TEAL,
    "grey": GREY,
    "white": WHITE,
    "tint_grid": TINT_GRID,
    "tint_fill": TINT_FILL,
}

# Fills allowed inside a box.  Text on any of these is white.
FILLS = (NAVY, BLUE, TEAL, GREY)

# Corner rounding, line weights and text sizes, matched to fig21/fig22.
ROUNDING = 0.030
EDGE_LW = 2.6          # only used for the "adopted path" emphasis outline
ARROW_LW = 2.0
ARROW_COLOUR = GREY
TITLE_SIZE = 13.5
BOX_TITLE_SIZE = 12.0
BOX_BODY_SIZE = 10.5
NOTE_SIZE = 11.0

DPI = 300

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 11,
    "savefig.dpi": DPI,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.28,
    "figure.facecolor": WHITE,
    "savefig.facecolor": WHITE,
})


def canvas(width, height):
    """A blank figure on a 0-100 coordinate square in both axes."""
    fig, ax = plt.subplots(figsize=(width, height))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")
    return fig, ax


def box(ax, x, y, w, h, title=None, body=None, fill=BLUE,
        emphasis=False, title_size=None, body_size=None, gap=0.30):
    """A solid rounded block with white text -- the house primitive.

    `title` is set bold, `body` regular beneath it.  Passing only `body`
    gives a single regular line; passing only `title` gives a single bold
    line.  `emphasis=True` adds the navy outline that fig21 uses to mark the
    path adopted by this project.
    """
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h,
        boxstyle=f"round,pad=0,rounding_size={ROUNDING * 100}",
        linewidth=EDGE_LW if emphasis else 0,
        edgecolor=NAVY if emphasis else fill,
        facecolor=fill, zorder=2))

    cx, cy = x + w / 2, y + h / 2
    ts = title_size or BOX_TITLE_SIZE
    bs = body_size or BOX_BODY_SIZE

    if title and body:
        n_t = title.count("\n") + 1
        n_b = body.count("\n") + 1
        # split the box between the two blocks, weighted by line count
        total = n_t + n_b
        t_y = cy + h * (n_b / total) * gap
        b_y = cy - h * (n_t / total) * gap
        ax.text(cx, t_y, title, ha="center", va="center", color=WHITE,
                fontsize=ts, weight="bold", zorder=3, linespacing=1.35)
        ax.text(cx, b_y, body, ha="center", va="center", color=WHITE,
                fontsize=bs, zorder=3, linespacing=1.35)
    elif title:
        ax.text(cx, cy, title, ha="center", va="center", color=WHITE,
                fontsize=ts, weight="bold", zorder=3, linespacing=1.35)
    elif body:
        ax.text(cx, cy, body, ha="center", va="center", color=WHITE,
                fontsize=bs, zorder=3, linespacing=1.35)


def arrow(ax, p1, p2, double=False, lw=None):
    """A grey connector with an arrowhead, as in fig22."""
    ax.add_patch(FancyArrowPatch(
        p1, p2,
        arrowstyle="<|-|>" if double else "-|>",
        mutation_scale=15, linewidth=lw or ARROW_LW,
        color=ARROW_COLOUR, zorder=1, shrinkA=3, shrinkB=3))


def connector(ax, p1, p2, lw=None):
    """A plain grey line with no arrowhead, as used by the fig21 tree."""
    ax.plot([p1[0], p2[0]], [p1[1], p2[1]],
            color=ARROW_COLOUR, linewidth=lw or 1.6, zorder=1,
            solid_capstyle="round")


def title(ax, text, y=97):
    """Bold navy heading inside the figure, as in fig22."""
    ax.text(50, y, text, ha="center", va="top", color=NAVY,
            fontsize=TITLE_SIZE, weight="bold")


def note(ax, text, y=2):
    """The italic grey explanatory line along the bottom of fig21/fig22."""
    ax.text(50, y, text, ha="center", va="bottom", color=NAVY,
            fontsize=NOTE_SIZE, style="italic", linespacing=1.5)


def label(ax, x, y, text, colour=GREY, size=10.0, ha="center", va="center",
          italic=False, bold=False):
    """Small free-standing text: an arrow label or an axis annotation."""
    ax.text(x, y, text, ha=ha, va=va, color=colour, fontsize=size,
            style="italic" if italic else "normal",
            weight="bold" if bold else "normal", linespacing=1.4)


def save(fig, filename, figdir=None):
    figdir = figdir or os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "figures")
    path = os.path.join(figdir, filename)
    fig.savefig(path, facecolor=WHITE)
    plt.close(fig)
    print("  wrote", filename)
    return path
