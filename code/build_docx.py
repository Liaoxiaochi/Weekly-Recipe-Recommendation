"""Insert Chapters 3, 4 and 5 into the dissertation and apply the Ch1/Ch2 fixes.

Reads   毕业论文_修订版.docx   (never modified)
Writes  毕业论文_v5.docx

Styles are set by writing the template's style IDs directly rather than by
name, because the Leeds template uses numeric IDs ('1', '2', '3') for the
heading styles and python-docx resolves styles by name.

The Word table of contents is a field and cannot be refreshed from here.
Open the result in Word and press Ctrl+A then F9 to update it.
"""

import os
import shutil

import docx
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

from ch3_content import (BLOCKS as CH3_BLOCKS, CH1_USDA_FIXES,
                         CH2_CAPTION_FIXES, CH2_CROSSREF_FIXES,
                         NEW_REFERENCES)
from ch4_content import BLOCKS as CH4_BLOCKS
from ch5_content import BLOCKS as CH5_BLOCKS

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
SRC = os.path.join(ROOT, "毕业论文_修订版.docx")
DST = os.path.join(ROOT, "毕业论文_v5.docx")
# A copy under a name that never changes.  The versioned file is for
# rolling back; this one is what any instruction to the author should
# name, so that bumping the version number cannot silently send them to
# a stale draft -- which is exactly what happened between v4 and v5.
LATEST = os.path.join(ROOT, "毕业论文_最新.docx")
FIG = os.path.join(ROOT, "figures")

report = []


def log(msg):
    report.append(msg)
    print(msg)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def set_style_id(par, style_id):
    """Apply a style by its w:styleId, bypassing python-docx's name lookup."""
    pPr = par._p.get_or_add_pPr()
    for old in pPr.findall(qn("w:pStyle")):
        pPr.remove(old)
    el = OxmlElement("w:pStyle")
    el.set(qn("w:val"), style_id)
    pPr.insert(0, el)


def para_text(par):
    return "".join(r.text for r in par.runs)


def rewrite_paragraph_text(par, new_text):
    """Replace a paragraph's text, keeping the formatting of its first run.

    Word splits a sentence across many runs, so a target substring often does
    not exist contiguously in any single run.  Collapsing to one run is safe
    for these plain body paragraphs, none of which carries inline formatting.
    """
    runs = par.runs
    if not runs:
        par.add_run(new_text)
        return
    keep = runs[0]
    keep.text = new_text
    for r in runs[1:]:
        r._r.getparent().remove(r._r)


# ---------------------------------------------------------------------------
# open
# ---------------------------------------------------------------------------
shutil.copyfile(SRC, DST)
doc = docx.Document(DST)
body = doc.element.body

# locate the List of References heading -- Chapter 3 goes immediately before it
ref_heading = None
for p in doc.paragraphs:
    if para_text(p).strip() == "List of References":
        ref_heading = p
        break
if ref_heading is None:
    raise SystemExit("could not find the 'List of References' heading")
log(f"anchor found: 'List of References'")


# ---------------------------------------------------------------------------
# Chapter 2 fix 1 -- swap the inverted table numbers
# ---------------------------------------------------------------------------
log("\n--- Chapter 2: table numbering ---")
pending = list(CH2_CAPTION_FIXES)
for p in doc.paragraphs:
    t = para_text(p).strip()
    for old, new in list(pending):
        if t == old.strip():
            rewrite_paragraph_text(p, new)
            log(f"  renumbered: {new[:46]}...")
            pending.remove((old, new))
            break
if pending:
    raise SystemExit(f"caption not matched: {pending}")


# ---------------------------------------------------------------------------
# Chapter 2 fix 2 -- add the missing in-text references to Figure 2.1,
# Table 2.1 and Table 2.2
# ---------------------------------------------------------------------------
log("\n--- Chapter 2: cross-references ---")
pending = list(CH2_CROSSREF_FIXES)
for p in doc.paragraphs:
    t = para_text(p)
    for anchor, addition in list(pending):
        if anchor in t:
            rewrite_paragraph_text(p, t.rstrip() + addition)
            log(f"  added:{addition[:58]}...")
            pending.remove((anchor, addition))
            break
if pending:
    raise SystemExit(f"cross-reference anchor not matched: {pending}")


# ---------------------------------------------------------------------------
# Chapter 1 fix -- remove the USDA promise superseded by design decision DD-2
# ---------------------------------------------------------------------------
log("\n--- Chapter 1: USDA wording ---")
n_usda = 0
for p in doc.paragraphs:
    t = para_text(p)
    if "USDA" not in t:
        continue
    new = t
    new = new.replace(
        "per-recipe nutritional values from USDA FoodData Central and "
        "ingredient-level allergen tags",
        "per-serving nutritional values normalised from the corpus's own "
        "nutrition fields and ingredient-level allergen tags")
    new = new.replace(
        "allergen tags and per-recipe nutritional values from USDA "
        "FoodData Central.",
        "allergen tags and per-serving nutritional values normalised to "
        "absolute quantities.")
    new = new.replace("publicly licensed sources", "a publicly licensed source")
    new = new.replace(" and USDA FoodData Central", "")
    if new != t:
        rewrite_paragraph_text(p, new)
        n_usda += 1
        log(f"  reworded: ...{new[:70]}...")
log(f"  {n_usda} paragraph(s) changed")
for p in doc.paragraphs:
    if "USDA" in para_text(p):
        raise SystemExit("a USDA mention survived: " + para_text(p)[:90])


# ---------------------------------------------------------------------------
# Chapter 3 -- build the blocks and move each one before the anchor
# ---------------------------------------------------------------------------
log("\n--- Chapter 3: inserting blocks ---")
STYLE_FOR = {"h1": "1", "h2": "2", "h3": "3",
             "figurecaption": "figurecaption", "tablecaption": "tablecaption"}
counts = {}
placeholders = []


def emit(el):
    """Move a freshly appended element to just before the anchor heading."""
    ref_heading._p.addprevious(el)


for block in list(CH3_BLOCKS) + list(CH4_BLOCKS) + list(CH5_BLOCKS):
    kind = block[0]
    counts[kind] = counts.get(kind, 0) + 1

    if kind in ("h1", "h2", "h3"):
        p = doc.add_paragraph(block[1])
        set_style_id(p, STYLE_FOR[kind])
        emit(p._p)

    elif kind == "p":
        p = doc.add_paragraph(block[1])
        set_style_id(p, "a")
        emit(p._p)

    elif kind in ("figurecaption", "tablecaption"):
        p = doc.add_paragraph(block[1])
        set_style_id(p, STYLE_FOR[kind])
        emit(p._p)

    elif kind == "eq":
        p = doc.add_paragraph()
        set_style_id(p, "a")
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(block[1])
        r.italic = True
        emit(p._p)

    elif kind == "image":
        p = doc.add_paragraph()
        set_style_id(p, "a")
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        if block[1].startswith("[["):
            # an asset only the author can supply; leave a visible marker
            # rather than a silent gap, and log it for the pending register
            r = p.add_run(block[1])
            r.bold = True
            r.font.color.rgb = RGBColor(0xC0, 0x00, 0x00)
            placeholders.append(block[1])
        else:
            path = os.path.join(FIG, block[1])
            if not os.path.exists(path):
                raise SystemExit(f"missing figure: {path}")
            p.add_run().add_picture(path, width=Inches(block[2]))
        emit(p._p)

    elif kind == "table":
        rows = block[1]
        t = doc.add_table(rows=len(rows), cols=len(rows[0]))
        t.style = doc.styles["Table Grid"]
        t.autofit = True
        for i, row in enumerate(rows):
            for j, cell in enumerate(row):
                c = t.cell(i, j)
                c.text = ""
                par = c.paragraphs[0]
                set_style_id(par, "a")
                run = par.add_run(str(cell))
                run.font.size = Pt(9)
                if i == 0:
                    run.bold = True
        emit(t._tbl)

    elif kind == "algo":
        cap = doc.add_paragraph(block[1])
        set_style_id(cap, "tablecaption")
        emit(cap._p)
        t = doc.add_table(rows=1, cols=1)
        t.style = doc.styles["Table Grid"]
        cell = t.cell(0, 0)
        cell.text = ""
        first = True
        for line in block[2]:
            par = cell.paragraphs[0] if first else cell.add_paragraph()
            first = False
            set_style_id(par, "a")
            pf = par.paragraph_format
            pf.space_after = Pt(0)
            pf.line_spacing = 1.0
            run = par.add_run(line if line else " ")
            run.font.name = "Consolas"
            run.font.size = Pt(8.5)
            run._element.rPr.rFonts.set(qn("w:eastAsia"), "Consolas")
        emit(t._tbl)

    else:
        raise SystemExit(f"unknown block kind: {kind}")

log("  blocks inserted: " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))
if placeholders:
    log(f"  {len(placeholders)} placeholder(s) awaiting an author-supplied asset:")
    for ph in placeholders:
        log(f"    {ph}")


# ---------------------------------------------------------------------------
# References -- append [28]..[37] in the style of the existing 27 entries
# ---------------------------------------------------------------------------
log("\n--- References ---")
last_ref = None
seen_refs = False
for p in doc.paragraphs:
    t = para_text(p).strip()
    if t == "List of References":
        seen_refs = True
        continue
    if seen_refs:
        if t.startswith("[") and "]" in t:
            last_ref = p
        elif t.startswith("Appendix"):
            break
if last_ref is None:
    raise SystemExit("could not find the end of the reference list")
log(f"  last existing entry: {para_text(last_ref)[:44]}...")

anchor = last_ref
for num, text in NEW_REFERENCES:
    p = doc.add_paragraph(f"[{num}]  {text}")
    set_style_id(p, "a")
    anchor._p.addnext(p._p)
    anchor = p
log(f"  appended [{NEW_REFERENCES[0][0]}]..[{NEW_REFERENCES[-1][0]}] "
    f"({len(NEW_REFERENCES)} entries)")


doc.save(DST)
shutil.copyfile(DST, LATEST)
log("")
log(f"saved: {os.path.relpath(DST, ROOT)}   (versioned, for rollback)")
log(f"       {os.path.relpath(LATEST, ROOT)}   <-- OPEN THIS ONE")
log("NOTE: open in Word and press Ctrl+A then F9 to rebuild the "
    "table of contents.")

with open(os.path.join(HERE, "outputs", "build_report.txt"), "w",
          encoding="utf-8") as f:
    f.write("\n".join(report))
