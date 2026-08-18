"""Interface palette and CSS.  The counterpart to figstyle, for the screen.

WHY THIS IS SEPARATE FROM figstyle.py
-------------------------------------
figstyle.py is the single source of truth for every figure in the dissertation,
and verify_figures.py fails a figure containing any colour outside its palette.
Adding warm interface colours there would weaken that check for the figures,
which is the one place the check earns its keep.

So the two are split along what they serve:

  figstyle   the printed page -- navy, blue, teal, grey on white.  A reader is
             looking at evidence, and the palette is chosen to survive
             greyscale printing.

  uistyle    the screen -- warm cream, deep brown, terracotta.  A user is
             deciding what to cook, and the page should feel like something
             worth cooking from.

One rule bridges them, and it is the reason a screenshot still belongs in the
dissertation: **every chart element in the interface uses figstyle colours.**
Macronutrient bars, energy charts and category marks are drawn in navy, blue
and teal, so a screenshot in Chapter 4 sits beside Figure 3.3 without a change
of visual language, while the page around it stays warm.
"""

# Warm chrome -- page, surfaces, type, accent.
CREAM = "#F7F3EC"          # page background
CREAM_DEEP = "#EFE7DA"     # gradient end, section fills
SURFACE = "#FFFDF9"        # cards
INK = "#3A322B"            # body text
INK_SOFT = "#7A6E62"       # secondary text
TERRACOTTA = "#B85C38"     # accent: actions, emphasis
TERRACOTTA_SOFT = "#E8D5CB"
LINE = "#E3D9CA"           # hairlines

UI_PALETTE = {
    "cream": CREAM, "cream_deep": CREAM_DEEP, "surface": SURFACE,
    "ink": INK, "ink_soft": INK_SOFT, "terracotta": TERRACOTTA,
    "terracotta_soft": TERRACOTTA_SOFT, "line": LINE,
}

# A serif for display type, a sans for everything else.  Both are stacks of
# faces already present on Windows and macOS -- no webfont is fetched, so the
# page renders identically offline and adds no third-party dependency to
# declare in Appendix A.
SERIF = "'Iowan Old Style', 'Palatino Linotype', Palatino, Georgia, serif"
SANS = "'Segoe UI', -apple-system, 'Helvetica Neue', Arial, sans-serif"


def page_css(background_uri=""):
    """The stylesheet.  Contains no text drawn from the corpus (see app.py)."""
    backdrop = (f"background-image: url('{background_uri}'), "
                f"linear-gradient(160deg, {CREAM} 0%, {CREAM_DEEP} 100%);"
                if background_uri else
                f"background-image: linear-gradient(160deg, {CREAM} 0%, "
                f"{CREAM_DEEP} 100%);")
    return f"""
<style>
  .stApp {{
      {backdrop}
      background-attachment: fixed;
      background-size: cover;
  }}
  html, body, [class*="css"] {{ font-family: {SANS}; color: {INK}; }}

  h1, h2, h3 {{ font-family: {SERIF}; color: {INK}; letter-spacing: -0.01em; }}
  h1 {{ font-weight: 600; font-size: 2.3rem; margin-bottom: 0.1rem; }}
  h2 {{ font-weight: 600; font-size: 1.45rem; margin-top: 1.6rem; }}
  h3 {{ font-weight: 600; font-size: 1.1rem; }}

  /* Cards: one surface, one hairline, generous air.  No box inside a box. */
  div[data-testid="stVerticalBlockBorderWrapper"] {{
      background: {SURFACE};
      border: 1px solid {LINE};
      border-radius: 12px;
      box-shadow: 0 1px 2px rgba(58,50,43,0.04);
  }}
  section[data-testid="stSidebar"] {{
      background: {SURFACE}; border-right: 1px solid {LINE};
  }}
  .stButton button {{
      border-radius: 8px; border: 1px solid {LINE};
      background: {SURFACE}; color: {INK}; font-weight: 500;
  }}
  .stButton button:hover {{
      border-color: {TERRACOTTA}; color: {TERRACOTTA};
  }}
  .stButton button[kind="primary"] {{
      background: {TERRACOTTA}; border-color: {TERRACOTTA}; color: #fff;
  }}

  /* The day heading: serif, quiet rule beneath. */
  .daylabel {{ font-family: {SERIF}; font-size: 1.15rem; font-weight: 600;
               color: {INK}; padding-bottom: 0.15rem; }}
  .daysub {{ color: {INK_SOFT}; font-size: 0.7rem; text-transform: uppercase;
             letter-spacing: 0.09em; border-bottom: 1px solid {LINE};
             padding-bottom: 0.5rem; margin-bottom: 0.6rem; }}
  .weekend .daylabel {{ color: {TERRACOTTA}; }}
  .weekend .daysub {{ border-bottom-color: {TERRACOTTA_SOFT}; }}

  .mark {{ font-size: 1.6rem; line-height: 1; }}
  .mark-sm {{ font-size: 1rem; line-height: 1; margin-right: 0.3rem; }}
  .slotname {{ color: {INK_SOFT}; font-size: 0.68rem; text-transform: uppercase;
               letter-spacing: 0.1em; }}

  /* Card header: mark, slot name and the plate's energy on one baseline, so
     the three things a user scans for are never pushed onto separate lines. */
  .cardhead {{ display: flex; align-items: center; gap: 0.5rem;
               margin-bottom: 0.1rem; }}
  .cardhead .kcal {{ margin-left: auto; font-weight: 600; font-size: 0.82rem;
                     color: {TERRACOTTA}; }}

  /* The glance strip. */
  .glance {{ display: flex; align-items: center; margin-top: 0.5rem; }}
  .daytotal {{ margin-top: 0.6rem; padding-top: 0.4rem;
               border-top: 1px solid {LINE}; font-size: 0.78rem;
               font-weight: 600; color: {TERRACOTTA}; }}

  .dishname {{ font-family: {SERIF}; font-size: 1.02rem; font-weight: 600;
               line-height: 1.25; color: {INK}; margin: 0.15rem 0 0.1rem 0; }}
  .plateline {{ border-top: 1px solid {LINE}; margin-top: 0.5rem;
                padding-top: 0.4rem; color: {INK_SOFT}; font-size: 0.78rem; }}

  /* The recipe author's own words, set as a quotation.  Styled through the
     element rather than a wrapper of ours, because the text is corpus text and
     corpus text is never placed inside raw HTML (see app.py).  It reaches the
     page as a markdown blockquote and is styled here. */
  blockquote {{ border-left: 3px solid {TERRACOTTA_SOFT} !important;
                background: transparent !important;
                padding: 0.1rem 0 0.1rem 0.9rem !important;
                color: {INK_SOFT}; font-family: {SERIF}; font-size: 0.95rem;
                font-style: italic; margin: 0.4rem 0 0.8rem 0; }}

  /* Charts keep the dissertation's palette -- see the module docstring. */
  .macrobar {{ display: flex; height: 7px; border-radius: 4px;
               overflow: hidden; margin: 0.4rem 0 0.1rem 0; }}
  .macrobar span {{ display: block; height: 100%; }}
  .meter {{ height: 9px; border-radius: 5px; background: {CREAM_DEEP};
            overflow: hidden; margin: 0.25rem 0; }}
  .meter span {{ display: block; height: 100%; border-radius: 5px; }}
  .locked {{ opacity: 0.45; pointer-events: none; }}
</style>
"""
