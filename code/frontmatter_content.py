"""Title page, Summary and Acknowledgements.

WHY THIS EXISTS.  The front matter was still the Leeds template, and nothing in
the project caught it.  verify_thesis.py looks for our own placeholder
convention, "[[...]]", while the template marks its gaps with "<...>" -- and
several of the template's notes run across paragraph boundaries, so even a
regular expression over single paragraphs finds nothing.  The result was a
dissertation whose first page after the title read:

    <Concise statement of the problem you intended to solve and main
    achievements (no more than one A4 page)>

That is the first thing an examiner reads.  Alongside it the document still
carried the template's own instructions to the author -- margins, page
numbering, the sixty-page rule -- as if they were part of the report.

WHAT IS CORRECTED HERE.  The Summary and Acknowledgements are written; the
template's instructional blocks are deleted; the title-page placeholders are
filled; and the deliverables table is rebuilt to describe what is actually
being submitted.

THE DELIVERABLES TABLE NEEDED MORE THAN DATES.  Its template row for
"Participant consent forms" no longer applies, because the usability study was
not run.  Leaving it would promise the School an envelope of signed forms that
does not exist.  The rows are also aligned with the four deliverables listed in
Section 1.3, and the third of them is described as rebuilt from the submitted
pipeline rather than handed over: Appendix A explains that the corpus carries
no redistribution licence, and a title page promising to deliver it would
contradict the appendix.

PAGE BUDGET.  None of this touches the sixty-page limit.  The Summary and
Acknowledgements are front matter, numbered in Roman numerals, and the limit
covers the main body only.
"""

# ---------------------------------------------------------------------------
# Straight text substitutions, applied only to paragraphs before Chapter 1.
# ---------------------------------------------------------------------------
REPLACEMENTS = [
    ("<2025/2026>", "2025/2026"),
    ("© <Year of Submission> The University of Leeds and "
     "<full name of candidate>",
     "© 2026 The University of Leeds and Xiaochi Liao"),
]

# ---------------------------------------------------------------------------
# Paragraphs deleted outright: every one is an instruction the template gives
# the author, not part of the report.
# ---------------------------------------------------------------------------
DELETE_CONTAINING = [
    "<As an example>",
    "<Reminder about basic requirements of layout and format",
    "The report must be in typescript, sequentially page numbered",
    "Page Numbering: The pages preceding the body of the text",
    "Length: The main body of a 60 credit project report",
    "Note that it is not acceptable to solicit assistance on",
]

# ---------------------------------------------------------------------------
# Placeholder paragraphs replaced by real content.
# ---------------------------------------------------------------------------
SUMMARY = [
    ("p",
     "Diet-related chronic disease is driven in large part by everyday food "
     "choices, and generic dietary advice translates poorly into what people "
     "actually cook. Recommender systems can personalise those choices, but "
     "the literature has developed the necessary capabilities separately: "
     "systems that enforce dietary exclusion rarely plan across several days, "
     "systems that plan across several days rarely model the context in which "
     "a meal is eaten, and few report both how well their suggestions match a "
     "person's taste and whether the resulting plans are nutritionally "
     "sound."),
    ("p",
     "This dissertation designs, implements and evaluates a system that "
     "combines them. A corpus of 128,403 recipes and 655,954 interactions was "
     "prepared from the Food.com dataset, with per-serving nutritional "
     "quantities recovered from the percentage figures the source records and "
     "allergen tags derived from ingredient text against the fourteen classes "
     "of European food information law. A user model converts anthropometric "
     "inputs into daily nutritional targets. A contextual-switching hybrid "
     "selects between content-based and collaborative recommendation "
     "according to how much history a user has, behind a constraint layer "
     "that removes what must not be offered before any ranking occurs and "
     "expresses nutritional preferences as penalties on the score. A planner "
     "assembles twenty-one meals into a week, distinguishing weekdays from "
     "weekends, and presents them through a web interface in which any meal "
     "can be replaced."),
    ("p",
     "Six experiments evaluate the result. The collaborative component "
     "reaches a rating error of 1.1826 against 1.2306 for the strongest "
     "trivial baseline. Across twelve user profiles the planner fills every "
     "meal slot, reaches 92 per cent of energy target, and admits no "
     "declared allergen; the screening behind that last property misses 2.5 "
     "per cent of the allergens genuinely present, measured on recipes it was "
     "not built from rather than assumed. The evaluation also found and "
     "corrected a defect that no assertion in the verification suite could "
     "have caught: the collaborative component predicted ratings better than "
     "any baseline and ranked at chance, because ranking by predicted rating "
     "ranks by item bias."),
    ("p",
     "No independent user evaluation was carried out, and that is the "
     "principal limitation of this work."),
]

ACKNOWLEDGEMENTS = [
    ("p",
     "I would like to thank my supervisor, Dr Kelvin Lau, for his guidance "
     "throughout this project, and in particular for the advice that settled "
     "its final scope. I am grateful to my assessor for the feedback given at "
     "the progress meeting, which changed the order in which the work was "
     "done and led to a working prototype earlier than I had planned. The "
     "recipe data used here was collected and released by Majumder et al., "
     "and I acknowledge the individual contributors to the originating site, "
     "who wrote the recipes this system reasons about."),
]

REPLACE_WITH_BLOCKS = [
    ("<Concise statement of the problem you intended to solve", SUMMARY),
    ("<This page should contain any acknowledgements", ACKNOWLEDGEMENTS),
]

# ---------------------------------------------------------------------------
# The deliverables table on the title page, rebuilt.  Identified by its header
# row rather than by position.
# ---------------------------------------------------------------------------
# The supervisor asked on 20 August 2026 why the evaluation results were being
# sent to the SSO as a deliverable of their own.  They were not: Chapter 5 is
# part of the report, and listing it separately implied a second submission
# that does not exist.  The processed corpus was listed for the same wrong
# reason -- Appendix A explains that it is rebuilt rather than handed over.
# The table now names only what is physically submitted, and to whom.
DELIVERABLES_HEADER = "Items"
# The bracketed labels tie each row to the deliverables listed in Section 1.3.
# Without them the page appears to contradict that section, which names four
# deliverables where this table has two rows: D1 and D4 are both parts of the
# report, and D2 and D3 are both parts of the software submission.
DELIVERABLES = [
    ["Items", "Format", "Recipient(s) and Date"],
    ["Dissertation report, including the evaluation in Chapter 5 (D1 and D4)",
     "Report", "SSO (31/08/2026)"],
    ["Software prototype and the pipeline that rebuilds the corpus "
     "(D2 and D3)",
     "Software codes or URL", "Supervisor, assessor (31/08/2026)"],
]
