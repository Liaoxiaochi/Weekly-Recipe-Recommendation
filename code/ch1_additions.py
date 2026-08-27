"""Corrections and additions to Chapter 1, applied to the source document.

WHY THIS EXISTS.  Chapters 1 and 2 live in the source .docx rather than being
generated, so changes to them are expressed here as text replacements and
insertions rather than as blocks.

TWO THINGS ARE BEING FIXED IN SECTION 1.4.

The first is a factual error.  The section stated that the data comes from "a
publicly licensed source".  It does not.  The Kaggle release carries the terms
"Data files (c) Original Authors", which grants no licence at all; the corpus
is used here under the research exemption in sections 29 and 29A of the
Copyright, Designs and Patents Act 1988, and is deliberately not redistributed
with the submitted code.  Appendix A states this, and Chapter 1 contradicted
it.

The second is an omission.  The marking guidance asks for discussion of "each
of legal, social, professional and ethical issues, including explanations if
not relevant".  The section covered three of the four and did not mention
professional issues at all.
"""

# ---------------------------------------------------------------------------
# Straight replacements, applied wherever the text occurs in Chapters 1 and 2.
# ---------------------------------------------------------------------------
REPLACEMENTS = [
    # The heading has to name all four categories the guidance asks for.
    ("1.4  Ethical, Legal and Social Issues",
     "1.4  Ethical, Legal, Social and Professional Issues"),
    ("1.4 Ethical, Legal and Social Issues",
     "1.4 Ethical, Legal, Social and Professional Issues"),

    # The licence claim was wrong.  See the module docstring.
    # Matched on the short distinctive fragment: the surrounding sentence
    # contains en-dashes whose exact code point in the source cannot be
    # relied on, and matching across them silently fails.
    ("a publicly licensed source", "a single public dataset"),

    # -- Section 1.1 must OPEN with the aim.
    #
    # "Structure of MSc Dissertation" is explicit: the first paragraph of
    # Section 1.1 "should start with: 'The aim of this project is to ....'".
    # It did not.  The aim was stated accurately but sat in the third
    # paragraph, behind two paragraphs of disease-burden context, and the
    # marking guidance scores "conforms to the required structure" under
    # presentation.
    #
    # This is done as two replacements rather than by inserting a paragraph,
    # because the insertion mechanism below matches on the first paragraph
    # containing its anchor and the source document carries a contents page:
    # anchoring on "1.1 Project Aim" would write into the table of contents.
    #
    # The two edits are a pair.  The first prepends the aim; the second
    # removes the same sentence from where it used to live, so the aim is
    # stated once and the section grows by about fifteen words.
    ("Diet-related chronic disease is the largest preventable burden on "
     "contemporary healthcare.",
     "The aim of this project is to design and implement a personalised, "
     "context-aware weekly recipe recommendation system that produces "
     "seven-day meal plans tailored to each user's tastes, dietary "
     "restrictions and nutritional targets. The need for such a system "
     "begins with the scale of the problem. Diet-related chronic disease "
     "is the largest preventable burden on contemporary healthcare."),

    ("This project addresses that gap by designing and implementing a "
     "personalised, context-aware weekly recipe recommendation system that "
     "produces seven-day meal plans tailored to each user's tastes, dietary "
     "restrictions and nutritional targets. The proposed system distinguishes",
     "This project addresses that gap. The proposed system distinguishes"),

    # -- Section 1.1 signposting, removed.
    #
    # The contents page already says what Sections 1.2 to 1.4 contain, and the
    # main body sits exactly on the 60-page limit, so a sentence that only
    # repeats the contents page is the first thing that should go.
    (" The remainder of this chapter formalises the project's objectives "
     "(Section 1.2), deliverables (Section 1.3) and ethical considerations "
     "(Section 1.4).",
     ""),
]

# ---------------------------------------------------------------------------
# Labels for the objectives and deliverables.
#
# WHY.  Both lists were written as plain consecutive paragraphs with no
# numbering, no bullets and no indent -- eight paragraphs in a row that the
# reader has to separate by eye.  Sub-headings would be worse: Section 1.2 runs
# to about ninety words, so four headings would fill the contents page with
# near-empty entries.  Labelling and indenting them turns the walls into lists
# without touching the structure.
#
# The labels also earn their keep later: Section 6.2 reports the outcome of
# each objective in turn, and can now name the one it is discussing instead of
# saying "the first objective".
#
# Each entry is (opening words of the paragraph, label).  Matching is on the
# start of the paragraph so that a phrase recurring elsewhere in the document
# cannot be labelled by accident.
# ---------------------------------------------------------------------------
NUMBERED_LISTS = [
    ("Curate a cleaned recipe corpus", "O1"),
    ("Design a user model that captures", "O2"),
    ("Implement a hybrid recommendation engine", "O3"),
    ("Evaluate the system using rating-prediction metrics", "O4"),

    ("A dissertation report covering", "D1"),
    ("A working Python prototype", "D2"),
    ("A processed subset of the Food.com data", "D3"),
    ("An evaluation report comparing", "D4"),
]

# ---------------------------------------------------------------------------
# Paragraphs inserted after the paragraph containing the anchor text.
# ---------------------------------------------------------------------------
INSERT_AFTER = [
    # -- legal, stated accurately, after the paragraph that used to overclaim
    ("no personally identifiable information is collected", [
        "The legal position of that dataset requires care, because it is more "
        "restrictive than it first appears. The Food.com release is "
        "distributed under the terms “Data files © Original "
        "Authors”, which grants no licence to redistribute it. It is "
        "used here for non-commercial research under the exceptions in "
        "sections 29 and 29A of the Copyright, Designs and Patents Act 1988, "
        "and it is deliberately not included with the submitted software; "
        "Appendix A records how the corpus can instead be obtained and "
        "reproduced from its original source. The recipe text itself remains "
        "the property of the individual contributors who wrote it, which is "
        "the reason the interface links each dish to its page on the "
        "originating site rather than reproducing it wholesale.",
    ]),

    # -- professional, the category the guidance names and the section lacked
    ("privacy-by-design approach with explicit consent", [
        "The professional issues are distinct from the ethical ones and are "
        "worth separating. The author is a computer scientist and not a "
        "registered dietitian, and a system that appears to give dietary "
        "advice while being built by someone unqualified to give it is a "
        "professional problem before it is an ethical one. The response is "
        "not a disclaimer alone but a series of choices about what the "
        "system is permitted to claim. It presents suggestions rather than "
        "prescriptions; it exposes the reasoning behind each choice as a sum "
        "of named terms rather than as an authoritative verdict; and it "
        "declines to make any statement about medical suitability anywhere in "
        "the interface, a restriction enforced in code rather than left to "
        "the wording of individual messages.",

        "Competence carries a second obligation, which is to be honest about "
        "the limits of what has been built. The allergen screening in this "
        "system will miss some allergens that are genuinely present, because "
        "the underlying data does not record composite ingredients reliably. "
        "The professional response to that is neither to hide it nor to "
        "abandon the feature, but to measure the error rate rather than "
        "assume it away, to design the filter so that its errors fall on the "
        "side of excluding too much, and to tell the user plainly and "
        "repeatedly that the screening is automated and is not a safety "
        "guarantee. Chapter 5 reports the measured rate. A system of this "
        "kind is only responsibly deployable if the person deploying it knows "
        "that number and says it out loud.",
    ]),
]
