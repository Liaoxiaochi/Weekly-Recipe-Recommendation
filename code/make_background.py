"""Generate the page backdrop.

A photograph is not an option here: the corpus carries no images, and the
recipe text itself is used under a research exemption rather than a licence, so
there is no dish photograph this project may lawfully show (see the design log,
DD-23).  A stock photograph behind the page would also be the wrong choice on
its own merits -- it competes with the content it sits behind.

What the page gets instead is generated: a very low-contrast field of soft
circles in the interface palette, drawn here and embedded as a data URI so the
application fetches nothing at run time.  It is deterministic, so the same
backdrop is produced on any machine and the figure is reproducible in the same
sense as every other artefact in this project.

Run:  python code/make_background.py
Out:  code/outputs/backdrop.png
"""

import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "outputs")

# Deliberately tiny in contrast: the backdrop should be felt, not seen.  If it
# is noticeable at a glance it is too strong.
SIZE = (1600, 1000)
SEED = 20260816
N_BLOBS = 26
BLUR = 90


def hex_to_rgb(value):
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def build():
    import sys
    sys.path.insert(0, HERE)
    from uistyle import CREAM, CREAM_DEEP, TERRACOTTA_SOFT

    rng = np.random.default_rng(SEED)
    base = Image.new("RGB", SIZE, hex_to_rgb(CREAM))
    layer = Image.new("RGB", SIZE, hex_to_rgb(CREAM))
    draw = ImageDraw.Draw(layer)

    tints = [hex_to_rgb(CREAM_DEEP), hex_to_rgb(TERRACOTTA_SOFT)]
    for _ in range(N_BLOBS):
        cx = rng.integers(-200, SIZE[0] + 200)
        cy = rng.integers(-200, SIZE[1] + 200)
        r = rng.integers(140, 420)
        tint = tints[rng.integers(0, len(tints))]
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=tint)

    layer = layer.filter(ImageFilter.GaussianBlur(BLUR))
    # 8 per cent is the whole point: enough to break a flat fill, far too
    # little to read as a picture.
    out = Image.blend(base, layer, 0.08)

    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, "backdrop.png")
    out.save(path, optimize=True)
    return path


def data_uri(path=None):
    """The backdrop as a data: URI, so the page fetches nothing at run time."""
    import base64
    path = path or os.path.join(OUT, "backdrop.png")
    if not os.path.exists(path):
        return ""
    with open(path, "rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode()


if __name__ == "__main__":
    path = build()
    print(f"wrote {path} ({os.path.getsize(path) / 1000:.0f} kB)")
