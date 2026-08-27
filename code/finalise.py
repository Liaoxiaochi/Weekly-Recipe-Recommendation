"""Rebuild the table of contents and write the file that gets submitted.

WHY THIS EXISTS.  Word's table of contents is a field.  build_docx.py writes the
document with python-docx, which does not evaluate fields, so the contents page
keeps whatever was cached the last time a human opened the file in Word and
pressed F9.  On 23 August 2026 that meant the contents page listed Chapter 1 and
Chapter 2 and nothing else: Chapters 3 to 6 were absent entirely and the
references were shown on page 9 when they are on page 61.  A reader opening the
submission would have been told the dissertation has two chapters.

The remedy has always been Ctrl+A then F9 in Word, and that instruction appeared
in every handover note for a week without being carried out.  A manual step that
reliably does not happen is a defect in the process, not in the person, so it is
automated here.

WHAT IT PRODUCES.  毕业论文_提交版.docx -- the same content as 毕业论文_最新.docx
with every field evaluated and the contents page rebuilt.  The input is left
untouched, so re-running build_docx.py never has to reckon with a file Word has
rewritten.

After running this, run page_count.py to confirm the body is still within the
sixty-page limit: a longer contents page moves the front matter, which is
numbered in Roman numerals and does not count towards the limit, but the check
is cheap and the limit is hard.
"""

import os
import shutil
import sys

try:
    import win32com.client as win32
except ImportError:
    sys.exit("pywin32 is required: pip install pywin32")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
SRC = os.path.join(ROOT, "毕业论文_最新.docx")
DST = os.path.join(ROOT, "毕业论文_提交版.docx")

WD_SAVE_CHANGES = -1          # wdSaveChanges
WD_DO_NOT_SAVE = 0            # wdDoNotSaveChanges
WD_OUTLINE_LEVEL_1 = 1        # wdOutlineLevel1
WD_ACTIVE_END_PAGE = 3        # wdActiveEndPageNumber


def main():
    if not os.path.exists(SRC):
        sys.exit("not found: " + SRC)

    # Work on a copy so the generated file stays exactly as build_docx.py left
    # it.  Word rewrites a document it saves, and a later diff against the
    # builder's output would then be meaningless.
    shutil.copyfile(SRC, DST)
    print("copied  %s" % os.path.basename(SRC))
    print("     -> %s" % os.path.basename(DST))

    word = win32.Dispatch("Word.Application")
    word.Visible = False
    word.DisplayAlerts = False
    try:
        doc = word.Documents.Open(DST, ReadOnly=False, AddToRecentFiles=False)
        try:
            n_toc = doc.TablesOfContents.Count
            if n_toc == 0:
                raise SystemExit("no table of contents found -- nothing to "
                                 "rebuild, which is itself a problem")

            # Update the whole field set first, then the contents specifically.
            # The order matters: a page number inside the contents is only
            # correct once the rest of the document has been repaginated.
            doc.Fields.Update()
            for i in range(1, n_toc + 1):
                doc.TablesOfContents(i).Update()
            doc.Repaginate()

            entries = doc.TablesOfContents(1).Range.Text.count(chr(13))
            print("rebuilt %d table(s) of contents, %d line(s)"
                  % (n_toc, entries))

            # Report what the contents page now claims, so the run itself shows
            # whether every chapter made it in.
            print()
            print("top-level entries and the page each starts on:")
            for para in doc.Paragraphs:
                if int(para.OutlineLevel) != WD_OUTLINE_LEVEL_1:
                    continue
                text = para.Range.Text.strip().replace(chr(13), "")
                if not text:
                    continue
                page = int(para.Range.Information(WD_ACTIVE_END_PAGE))
                print("   %4d  %s" % (page, text))

            doc.Save()
        finally:
            doc.Close(WD_DO_NOT_SAVE)
    finally:
        word.Quit()

    print()
    print("written: %s" % os.path.relpath(DST, ROOT))
    print("Open it and check the contents page lists Chapters 1 to 6, the "
          "references and both appendices.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
