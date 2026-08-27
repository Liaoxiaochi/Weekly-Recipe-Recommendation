"""Shift Chapter 3's references from [28]-[37] to [41]-[50].

WHY THIS EXISTS.  The writing standard requires references to be numbered by
order of first appearance in the body.  Chapter 2 sits before Chapter 3, so the
thirteen sources added to the expanded literature review claim [28]-[40], and
the ten sources that Chapter 3 introduced must move up by thirteen to keep the
sequence honest.  Doing that by hand across a 980-line content module is how
duplicated and skipped numbers get created, and verify_thesis.py's fourth check
would then fail with no clue as to which edit caused it.

HOW IT AVOIDS COLLISIONS.  The substitution runs from the highest number down.
Rewriting [28] to [41] first would create a second [41] that the later pass for
the original [41] could not tell apart from the one it was meant to produce --
descending order guarantees each target number is still unused when it is
written.

The script is idempotent by refusing to run twice: if any citation in the
[41]-[50] band already exists, the shift has been applied and it stops.
"""

import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.join(HERE, "ch3_content.py")

OLD_LO, OLD_HI = 28, 37
SHIFT = 13


def main():
    src = io.open(TARGET, encoding="utf-8").read()

    present = sorted({int(n) for n in re.findall(r"\[(\d+)\]", src)})
    if any(OLD_LO + SHIFT <= n <= OLD_HI + SHIFT for n in present):
        sys.exit("citations in the [%d]-[%d] band already exist -- the shift "
                 "looks applied already, refusing to run twice"
                 % (OLD_LO + SHIFT, OLD_HI + SHIFT))

    expected = list(range(OLD_LO, OLD_HI + 1))
    missing = [n for n in expected if n not in present]
    if missing:
        sys.exit("expected citations not found in %s: %s"
                 % (os.path.basename(TARGET), missing))

    # 1. In-text citation markers, highest first.
    n_cites = 0
    for n in range(OLD_HI, OLD_LO - 1, -1):
        marker = "[%d]" % n
        n_cites += src.count(marker)
        src = src.replace(marker, "[%d]" % (n + SHIFT))

    # 2. The reference list itself, whose numbers are tuple keys rather than
    #    bracketed markers and so are untouched by the pass above.
    n_entries = 0
    for n in range(OLD_HI, OLD_LO - 1, -1):
        old_key = "    (%d, " % n
        new_key = "    (%d, " % (n + SHIFT)
        if old_key not in src:
            sys.exit("reference list entry not found: %s" % old_key.strip())
        n_entries += src.count(old_key)
        src = src.replace(old_key, new_key)

    io.open(TARGET, "w", encoding="utf-8", newline="").write(src)

    print("shifted [%d]-[%d] to [%d]-[%d] in %s"
          % (OLD_LO, OLD_HI, OLD_LO + SHIFT, OLD_HI + SHIFT,
             os.path.basename(TARGET)))
    print("  %d in-text citation markers" % n_cites)
    print("  %d reference list entries" % n_entries)
    print("  [%d]-[%d] are now free for Chapter 2" % (OLD_LO, OLD_LO + 12))


if __name__ == "__main__":
    main()
