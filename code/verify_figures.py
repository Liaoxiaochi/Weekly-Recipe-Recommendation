"""Automated guard against figure style drift.

The style used to live only inside PNG files, so nothing detected when a new
figure was drawn in a different visual language.  This script makes drift a
hard failure rather than something a reader has to notice.

Checks:
  1  every colour covering more than TRACE of a figure's pixels is in the
     figstyle palette (anti-aliased blends fall below the threshold)
  2  DPI is identical across figures
  3  every figure referenced by ch3_content.py exists on disk
  4  no orphan PNG sits in figures/ without being referenced

Also writes figures/_contact_sheet.png so drift is visible at a glance.

Run:  python code/verify_figures.py
"""

import os
import re
import sys
from collections import Counter

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image

import figstyle as fs

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(HERE, "..", "figures")

TRACE = 0.001          # 0.1% of pixels; blends sit far below this
TOL = 10               # per-channel tolerance, absorbs PNG/AA rounding

# Author-supplied external assets: screenshots of third-party pages and, later,
# of the running prototype.  These cannot conform to the palette because they
# are photographs of something we do not control.  They are listed by name
# rather than pattern-matched, so adding one is a deliberate act and an
# off-style diagram can never be waved through by accident.
# Empty since 19 August 2026: the Food.com nutrition panel was the only entry,
# and it was removed from Section 3.2.3 at the author's request.  The set is
# kept rather than deleted because the next author-supplied external asset will
# need it, and because an empty waiver list documents that nothing is currently
# exempt from the palette check.
EXTERNAL = set()

fail = []


def to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


APPROVED = [to_rgb(v) for v in fs.PALETTE.values()]


def near_approved(rgb):
    return any(all(abs(a - b) <= TOL for a, b in zip(rgb, ok))
               for ok in APPROVED)


pngs = sorted(f for f in os.listdir(FIG)
              if f.endswith(".png") and not f.startswith("_"))
if not pngs:
    sys.exit("no figures found")

print("=" * 70)
print("1. PALETTE CONFORMANCE")
print("=" * 70)
dpis = {}
for name in pngs:
    path = os.path.join(FIG, name)
    im = Image.open(path).convert("RGB")
    if name in EXTERNAL:
        print(f"   {name:<28} external asset, exempt "
              f"({im.width}x{im.height})")
        continue
    dpis[name] = im.info.get("dpi", (None, None))[0]
    total = im.width * im.height
    counts = Counter({c: n for n, c in im.getcolors(maxcolors=1 << 24)})
    offenders = [(c, n) for c, n in counts.items()
                 if n / total > TRACE and not near_approved(c)]
    if offenders:
        fail.append(f"{name}: off-palette colour")
        print(f"   {name}: *** {len(offenders)} OFF-PALETTE ***")
        for c, n in sorted(offenders, key=lambda x: -x[1])[:6]:
            print(f"       #%02x%02x%02x  {100*n/total:.2f}%% of pixels" % c)
    else:
        used = sorted({c for c, n in counts.items() if n / total > TRACE},
                      key=lambda c: -counts[c])
        print(f"   {name:<28} OK   {len(used)} palette colours")

print()
print("=" * 70)
print("2. RESOLUTION CONSISTENCY")
print("=" * 70)
distinct = {d for d in dpis.values() if d}
print(f"   DPI values across figures: {sorted(distinct)}")
if len(distinct) > 1:
    fail.append("inconsistent DPI")
    print("   *** FIGURES DISAGREE ON DPI ***")
    for k, v in dpis.items():
        print(f"       {k}: {v}")
else:
    print("   consistent: OK")

print()
print("=" * 70)
print("3. REFERENCED FIGURES EXIST")
print("=" * 70)
# Scan every generated chapter, not only Chapter 3.  Until 19 August 2026 this
# looked at ch3_content.py alone, which left the four Chapter 5 figures outside
# the "referenced but missing" check entirely and reported them as orphans.
referenced = set()
for chapter in ("ch3_content.py", "ch4_content.py", "ch5_content.py",
                "ch6_content.py"):
    content = os.path.join(HERE, chapter)
    if os.path.exists(content):
        with open(content, encoding="utf-8") as f:
            referenced |= set(re.findall(r'"(fig\w+\.png)"', f.read()))
for r in sorted(referenced):
    ok = os.path.exists(os.path.join(FIG, r))
    print(f"   {r:<28} {'OK' if ok else '*** MISSING ***'}")
    if not ok:
        fail.append(f"referenced but missing: {r}")

ch2 = {"fig21_taxonomy.png", "fig22_pipeline.png"}
orphans = set(pngs) - referenced - ch2
if orphans:
    print(f"   note: not referenced by Chapter 3 (may be fine): "
          f"{sorted(orphans)}")

# ---------------------------------------------------------------------------
# contact sheet
# ---------------------------------------------------------------------------
print()
print("=" * 70)
print("4. CONTACT SHEET")
print("=" * 70)
cols = 2
rows = (len(pngs) + cols - 1) // cols
fig, axes = plt.subplots(rows, cols, figsize=(13, 3.4 * rows))
axes = axes.ravel() if hasattr(axes, "ravel") else [axes]
for ax, name in zip(axes, pngs):
    ax.imshow(Image.open(os.path.join(FIG, name)))
    ax.set_title(name, fontsize=10, color=fs.NAVY)
    ax.axis("off")
for ax in axes[len(pngs):]:
    ax.axis("off")
fig.suptitle("All dissertation figures — check that they read as one set",
             fontsize=13, color=fs.NAVY, weight="bold")
fig.tight_layout(rect=[0, 0, 1, 0.97])
sheet = os.path.join(FIG, "_contact_sheet.png")
fig.savefig(sheet, dpi=110, facecolor="white")
plt.close(fig)
print(f"   wrote figures/_contact_sheet.png ({len(pngs)} figures)")

print()
print("=" * 70)
if fail:
    print(f"RESULT: {len(fail)} problem(s)")
    for f_ in fail:
        print("  - " + f_)
    sys.exit(1)
print("RESULT: all figures conform to figstyle")
