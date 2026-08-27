"""Measure the real page count of the dissertation.

WHY THIS EXISTS.  The 60-page limit is a hard school rule and the only number
that can confirm compliance is the one Word itself computes after the fields
and the table of contents have been refreshed.  Asking the author to do that by
hand (Ctrl+A, F9, read the last page number) left item A-1 of the pending
register open from 17 to 18 August, blocking every decision about what to cut.
Word and pywin32 are both installed on this machine, so the measurement can be
made directly and repeated after every build.

WHAT IT REPORTS.  The limit excludes the references and the appendices, so a
single total is not enough.  The script walks the document's headings, records
the page each chapter starts on, and reports the body span (Chapter 1 to the
last page before "List of References") separately from the total.

The document is opened read-only and closed without saving.  Nothing here
modifies the .docx; the field update happens in Word's memory only.
"""

import os
import sys

try:
    import win32com.client as win32
except ImportError:
    sys.exit("pywin32 is required: pip install pywin32")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
DOC = os.path.join(ROOT, "毕业论文_最新.docx")
REPORT = os.path.join(HERE, "outputs", "page_report.txt")

LIMIT = 60

# Word enumeration constants, named so the calls below can be read without the
# reference manual open.
WD_ACTIVE_END_PAGE = 3        # wdActiveEndPageNumber
WD_STATISTIC_PAGES = 2        # wdStatisticPages
WD_STATISTIC_WORDS = 0        # wdStatisticWords
WD_DO_NOT_SAVE = 0            # wdDoNotSaveChanges
WD_OUTLINE_LEVEL_1 = 1        # wdOutlineLevel1, i.e. a top-level heading

# Headings that end the body.  Everything from here on is excluded from the
# 60-page limit.
BODY_END = ("List of References",)


def main():
    if not os.path.exists(DOC):
        sys.exit("not found: " + DOC)

    word = win32.Dispatch("Word.Application")
    word.Visible = False
    word.DisplayAlerts = False
    lines = []
    try:
        doc = word.Documents.Open(DOC, ReadOnly=True, AddToRecentFiles=False)
        try:
            # Page numbers are meaningless until the fields are repaginated:
            # the table of contents still carries whatever was cached at the
            # last save, and a stale ToC is a different length from a fresh one.
            doc.Fields.Update()
            for i in range(1, doc.TablesOfContents.Count + 1):
                doc.TablesOfContents(i).Update()
            doc.Repaginate()

            total_pages = int(doc.ComputeStatistics(WD_STATISTIC_PAGES))
            total_words = int(doc.ComputeStatistics(WD_STATISTIC_WORDS))

            # Walk the top-level headings and note where each one falls.
            #
            # Match on OutlineLevel rather than on the style name.  This
            # Office install is Chinese, so Style.NameLocal returns
            # "标题 1" and a test for "Heading 1" silently matches nothing:
            # the first run of this script reported no sections at all for
            # exactly that reason.  OutlineLevel is a number and does not
            # vary with the interface language.
            marks = []
            for para in doc.Paragraphs:
                if int(para.OutlineLevel) != WD_OUTLINE_LEVEL_1:
                    continue
                text = para.Range.Text.strip().replace("\r", "")
                if not text:
                    continue
                page = int(para.Range.Information(WD_ACTIVE_END_PAGE))
                marks.append((page, text))

            body_start = None
            body_end_page = None
            for page, text in marks:
                if body_start is None and text.startswith("Chapter"):
                    body_start = page
                if any(text.startswith(e) for e in BODY_END):
                    body_end_page = page
                    break

            lines.append("Page report for 毕业论文_最新.docx")
            lines.append("=" * 58)
            lines.append("")
            lines.append("Whole document : %d pages, %d words" % (total_pages, total_words))
            lines.append("")
            lines.append("Section starts (page : heading)")
            for page, text in marks:
                lines.append("  %4d : %s" % (page, text))
            lines.append("")

            if body_start is None or body_end_page is None:
                lines.append("Body span could not be determined: expected a "
                             "'Chapter ...' heading and a 'List of References' "
                             "heading.")
                verdict = None
            else:
                # The references start on their own page, so the last body page
                # is the one before it.
                body_pages = body_end_page - body_start
                verdict = body_pages
                lines.append("BODY (Chapter 1 .. last page before References)")
                lines.append("  starts on page %d, references begin on page %d"
                             % (body_start, body_end_page))
                lines.append("  body length : %d pages" % body_pages)
                lines.append("  limit       : %d pages" % LIMIT)
                headroom = LIMIT - body_pages
                if headroom >= 0:
                    lines.append("  headroom    : %d pages remaining" % headroom)
                else:
                    lines.append("  OVER LIMIT  : %d pages must be removed" % -headroom)
        finally:
            doc.Close(WD_DO_NOT_SAVE)
    finally:
        word.Quit()

    report = "\n".join(lines)
    print(report)
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as fh:
        fh.write(report + "\n")
    print("\nwritten to " + REPORT)

    return 0 if verdict is None or verdict <= LIMIT else 1


if __name__ == "__main__":
    sys.exit(main())
