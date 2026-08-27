"""Build the software deliverable as a zip that is safe to send.

WHY THIS IS A SCRIPT.  The obvious way to produce this deliverable is to
right-click the project folder and compress it.  That would ship 870 MB of
Food.com data, the derived pickles and .streamlit/secrets.toml, which holds a
live API key.  The data carries no redistribution licence (Appendix A) and the
key must never leave this machine, so the packaging step is automated and
asserts both facts before it writes anything.

WHAT GOES IN.  Whatever git would track: the working tree filtered through
.gitignore.  Deliberately taken from the working tree rather than from HEAD,
because the repository is usually behind and a package built from the last
commit would not reproduce the current dissertation.

Run from code/.
"""

import os
import subprocess
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
OUT = os.path.join(ROOT, "Liao_Xiaochi_software_deliverable.zip")

# Kept in the repository, left out of the deliverable: a superseded draft and
# the figures retired from the report.  Neither helps a reader run the system.
EXCLUDE_PREFIXES = ("figures/_retired/",)
EXCLUDE_NAMES = ("code/ch3_content_BACKUP_7691w.py",)

# Nothing matching these may ever appear in the archive.
FORBIDDEN = ("data/", ".pkl", "secrets.toml", ".docx")


def tracked_files():
    out = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT, capture_output=True, text=True, check=True)
    return [line.strip() for line in out.stdout.splitlines() if line.strip()]


def main():
    files = tracked_files()
    kept = [f for f in files
            if not f.startswith(EXCLUDE_PREFIXES) and f not in EXCLUDE_NAMES
            and os.path.exists(os.path.join(ROOT, f))]

    # git still lists files that were deleted or moved since the last commit --
    # the four retired figures, for instance.  Packaging them would fail; more
    # to the point, they are no longer part of the system.
    missing = [f for f in files if not os.path.exists(os.path.join(ROOT, f))]
    if missing:
        print("skipped %d file(s) git still tracks but which no longer exist"
              % len(missing))

    # Refuse to write rather than warn.  A warning in a build log is not a
    # control; the whole point of this script is that the unsafe package cannot
    # be produced by accident.
    offenders = [f for f in kept
                 if any(bad in f for bad in FORBIDDEN)]
    if offenders:
        sys.exit("refusing to package, forbidden content: %s" % offenders)

    if os.path.exists(OUT):
        os.remove(OUT)
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        for f in kept:
            z.write(os.path.join(ROOT, f), arcname=f)

    size = os.path.getsize(OUT) / 1024.0 / 1024.0
    print("%d files considered, %d packaged, %d excluded"
          % (len(files), len(kept), len(files) - len(kept)))
    print("no data files, no pickles, no credentials, no report: checked")
    print("written: %s (%.1f MB)" % (os.path.relpath(OUT, ROOT), size))

    # Read the archive back and check again, so the guarantee is about the file
    # that exists rather than about the list that was intended.
    with zipfile.ZipFile(OUT) as z:
        names = z.namelist()
    late = [n for n in names if any(bad in n for bad in FORBIDDEN)]
    if late:
        sys.exit("archive contains forbidden content after writing: %s" % late)
    print("re-checked the written archive: %d entries, all clean" % len(names))
    return 0


if __name__ == "__main__":
    sys.exit(main())
