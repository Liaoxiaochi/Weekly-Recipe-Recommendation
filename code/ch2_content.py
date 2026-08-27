"""Expansion of Chapter 2, applied to the source document as patches.

WHY THIS EXISTS.  Chapters 1 and 2 live inside 毕业论文_修订版.docx rather than
being generated from source, so changes to them are expressed as replacements
and insertions against anchor text rather than as a list of blocks.  This
module follows the pattern established by ch1_additions.py, extended so that an
insertion may carry headings and tables and not only paragraphs, because the
expansion adds two new sections rather than extra prose inside existing ones.

WHAT IS BEING ADDED AND WHY.  The supervisor's reply of 18 August 2026 states
that the 30 per cent allocated to Research Background covers Chapters 1 and 2,
and that "the literature review should contain sufficient depths and critical
analysis".  The chapter as written surveyed the field competently but was
descriptive: it reported what prior systems did without assessing what they
failed to do, and it never stated how the literature had been identified.  The
additions therefore concentrate on three things the chapter lacked --

  * a statement of how the literature was searched, and an honest account of
    the difference between this targeted review and a formal systematic one;
  * criticism of the reviewed methods, including two results from the wider
    recommender-systems literature that bear directly on the design chosen
    here and on the evaluation reported in Chapter 5;
  * a new Section 2.3 that assesses the reviewed systems against the four
    capabilities this project must combine, and states the gap.

NUMBERING.  The thirteen sources added here take [28] to [40], because the
writing standard numbers references by order of first appearance and Chapter 2
precedes Chapter 3.  The ten sources Chapter 3 introduced were shifted to [41]
to [50] by renumber_refs.py before this module was written; in-text citations
below already use the shifted numbers.

SECTION NUMBERING.  Only one existing heading is renumbered: "2.3 Choice of
Methods" becomes 2.4, to make room for the new critical analysis section.  The
subsections 2.1.x and 2.2.x keep their numbers because Chapter 3 refers to
Sections 2.1.3, 2.2.3 and 2.2.4 by number, and renumbering them would silently
break those cross-references.
"""

# ---------------------------------------------------------------------------
# Paragraphs deleted outright.
#
# The chapter opened with a paragraph that only announced what Sections 2.1 to
# 2.4 contain.  The contents page already does that, and the main body sits on
# the 60-page limit, so signposting that repeats the contents page is the first
# thing to go.  The two paragraphs that follow it -- how the literature was
# found, and why the review is targeted rather than systematic -- are evidence
# of a scholarly approach and are kept; after this deletion the chapter opens
# with them.
#
# ORDER MATTERS.  This paragraph is also the anchor for the first entry of
# INSERTIONS below, so build_docx.py must run the deletion AFTER the insertion
# pass.  Deleting it earlier would leave that anchor unfindable and abort the
# build.  The REPLACEMENTS entry that rewrites this same paragraph is left in
# place: it now rewrites a paragraph that is removed a few steps later, which
# is wasted work but cannot produce a wrong document.
# ---------------------------------------------------------------------------
DELETE_CONTAINING = [
    "This chapter establishes the empirical, behavioural and methodological",
]

# ---------------------------------------------------------------------------
# Straight replacements, applied wherever the text occurs in the body.
# ---------------------------------------------------------------------------
REPLACEMENTS = [
    # The chapter introduction has to describe the new structure.
    ("Section 2.3 draws the two strands together to justify the "
     "methodological choices implemented in Chapter 3.",
     "Section 2.3 assesses the reviewed systems against the requirements of "
     "this project and states the gap the work addresses, and Section 2.4 "
     "draws the strands together to justify the methodological choices "
     "implemented in Chapter 3."),

    # Room for the new Section 2.3.
    ("2.3 Choice of Methods", "2.4 Choice of Methods"),

    # The pointer to Table 2.2 has to move to the end of the evaluation
    # discussion, because two paragraphs are being inserted after this one and
    # the pointer must stay adjacent to the table it introduces.
    (" Table 2.2 compares the method families discussed in this section and "
     "states the role each plays in the present work.",
     ""),

    # -----------------------------------------------------------------------
    # The supervisor's revisions of 20 August 2026, applied to text that lives
    # in the source document rather than in this module.  They are recorded
    # here because accepting them in the built .docx would not survive the
    # next run of build_docx.py, which regenerates that file from scratch.
    # -----------------------------------------------------------------------

    # He struck "methodologically" and the clause announcing what the
    # subsection was about to do, and asked for a plainer opening.
    ("Each is examined methodologically in Section 2.2; the present "
     "subsection situates them in the recipe domain, where rich textual "
     "content (ingredient lists, instructions) and small numbers of explicit "
     "ratings per user are characteristic features.",
     "Each is examined in Section 2.2. This section reviews recipe "
     "recommendation, where rich textual content such as ingredient lists and "
     "instructions, together with small numbers of explicit ratings per user, "
     "are characteristic features."),

    # Comment: 'Replace "frame the methodological" to "inform the". It reads
    # better and less hard to read.'
    ("These two observations frame the methodological choices in Section 2.2 "
     "and the constraint handling discussed in Section 2.2.4.",
     "These two observations inform the choices in Section 2.2 and the "
     "constraint handling discussed in Section 2.2.4."),
]

# ---------------------------------------------------------------------------
# Insertions.  Each entry is (where, anchor, blocks), where `where` is "after"
# or "before" and `anchor` is matched against body paragraphs only -- the table
# of contents repeats every heading verbatim, and anchoring on a heading
# without that restriction would splice the new text into the contents page.
# ---------------------------------------------------------------------------
INSERTIONS = [

    # -- how the literature was found, stated at the top of the chapter ------
    ("after",
     "justify the methodological choices implemented in Chapter 3",
     [
      ("p",
       "The literature was identified by searching the ACM Digital Library, "
       "IEEE Xplore, Scopus and Google Scholar for work on recipe "
       "recommendation, meal planning and nutritional constraints, and by "
       "following citations from the most recent surveys of the field. "
       "Peer-reviewed publications were preferred, and recent work was "
       "favoured except where an older paper is the origin of a technique "
       "still in use."),
      ("p",
       "The review is targeted rather than exhaustive. A systematic review "
       "in the formal sense fixes its protocol in advance, screens every "
       "retrieved record against stated criteria and reports how many were "
       "excluded at each stage; Mahajan and Kaur [28] provide such a review "
       "of food recommender systems, at a breadth not attempted here. The "
       "purpose here is narrower. It is to establish what has been "
       "demonstrated about the four capabilities this project must combine, "
       "namely exclusion of unsafe or prohibited dishes, planning across "
       "several days, sensitivity to temporal context and reported "
       "nutritional outcomes, and to locate where those capabilities have "
       "not previously been brought together. Sections 2.1 and 2.2 assemble "
       "that evidence and Section 2.3 draws the comparison."),
     ]),

    # -- 2.1.2: the provenance of recipe corpora, and what it costs ----------
    ("before",
     "Two features distinguish recipe recommendation from canonical product "
     "recommendation",
     [
      ("p",
       "The scope of this field has grown significantly. Min et al. [29] "
       "survey food computing as a field in its own right, spanning recipe "
       "retrieval, dietary assessment and health-oriented recommendation. "
       "The corpus used here is, like the other large recipe datasets "
       "available for research, written by members of the public rather "
       "than compiled by professionals. This has two consequences. It "
       "supplies the volume of interaction data that collaborative methods "
       "require, but it also means there is no guarantee that the "
       "nutritional information attached to a recipe has been checked by "
       "anyone."),
      ("p",
       "This has been measured. Trattner and "
       "Elsweiler [31] assessed 60,983 recipes from a large online portal "
       "against World Health Organization criteria and found that fewer than "
       "40 per cent satisfied them, with fat and saturated fat the most "
       "frequent failures. Recommending dishes a user will like therefore "
       "does not, on average, produce a reasonable diet. Any nutritional "
       "property the system is expected to have must be built in "
       "deliberately rather than inherited from the data, which is the "
       "reason nutrition enters the design of Chapter 3 as a scored "
       "objective and "
       "not as a filter applied at the end."),
     ]),

    # -- 2.1.3: the two systems closest to this project ----------------------
    ("before",
     "Longitudinal planning also brings constraint handling into sharper "
     "focus",
     [
      ("p",
       "Two systems address the weekly horizon directly and are the closest "
       "prior work to this project. Harvey and Elsweiler [32] generate "
       "personalised meal plans that respect daily nutritional guidelines "
       "while ranking dishes by predicted preference, demonstrating that "
       "taste modelling and nutritional adherence can be combined within a "
       "single plan rather than traded against one another. Gaál et al. [33] "
       "approach the same problem from the opposite direction, treating "
       "weekly menu generation as a constrained optimisation solved by a "
       "genetic algorithm over nutrient targets defined at meal, daily and "
       "weekly levels. The contrast is instructive. The optimisation "
       "formulation gives strong guarantees about nutrient totals but holds "
       "no model of what an individual user likes; the recommendation "
       "formulation personalises well but enforces nutrition only softly. "
       "Section 2.3 returns to this tension, which the present design "
       "resolves by separating the constraints that must hold from the "
       "preferences that may be traded."),
     ]),

    # -- 2.2.1: what the ingredient representation cannot see ----------------
    ("after",
     "replaces hand-crafted ingredient features with deep-learning ingredient "
     "detection",
     [
      ("p",
       "The limits of the approach in this domain are equally well "
       "documented. Because the representation is dominated by the "
       "ingredient list, two dishes sharing ingredients but differing "
       "entirely in preparation, effort or the occasion they suit are treated "
       "as near neighbours: the representation captures what a dish is made "
       "of, but not what it is for. Trattner and Elsweiler [30] identify this "
       "insensitivity to context as one reason content-based food "
       "recommenders tend to plateau once a user's profile has stabilised. "
       "The implication for the present work is specific rather than "
       "general. Content similarity is retained for the cold phase, where "
       "nothing else is available, but the assignment of a dish to a "
       "breakfast, lunch or dinner position is handled by explicit tagging "
       "rather than left for similarity to discover."),
     ]),

    # -- 2.2.2: what recipe ratings actually contain -------------------------
    ("after",
     "anticipate the hybrid direction developed in Section 2.2.3",
     [
      ("p",
       "Whether latent-factor models are the right instrument for recipe data "
       "depends on what recipe ratings contain, and Harvey et al. [34] study "
       "rating prediction on exactly this kind of corpus. The distribution "
       "matters. In the corpus used here, 88.9 per cent of ratings are four "
       "or five stars, so a model has little variance left to explain, and "
       "what it does explain may be closer to how often a dish is rated than "
       "to who rated it. That property anticipates a "
       "defect found during the evaluation of the present system and reported "
       "in Section 5.3, where ranking by predicted rating turned out to be "
       "ranking by item bias. A collaborative model can therefore be accurate "
       "in the sense that error metrics measure while carrying little "
       "information about which of two acceptable dishes a particular user "
       "would prefer."),
     ]),

    # -- 2.2.3: why conventional components are a defensible choice ----------
    ("after",
     "they are revisited only as future-work directions",
     [
      ("p",
       "A cautionary result from the wider recommender-systems literature "
       "bears directly on the choice made here. Ferrari Dacrema et al. [35] "
       "reproduced eighteen neural recommendation methods published at major "
       "venues and found that most were outperformed by carefully tuned "
       "conventional baselines, and that several of the original comparisons "
       "had used baselines that were not tuned at all. This does not show "
       "that graph or neural methods lack value, but it does show that their "
       "reported margins cannot be taken at face value, and that a "
       "well-implemented conventional method is a reasonable point of "
       "departure rather than a concession. The present project adopts that "
       "position deliberately: the components it combines are conventional, "
       "and the contribution claimed lies in the constraint handling and "
       "weekly structure built around them rather than in the ranking model "
       "itself."),
     ]),

    # -- 2.2.4: how the choice of metric changes the conclusion --------------
    ("after",
     "which guards against degenerate recommendations that repeat similar "
     "items across days",
     [
      ("p",
       "The choice among these axes is not neutral, and the literature has "
       "repeatedly found that it changes conclusions. Herlocker et al. [36] "
       "argue that no single accuracy measure serves every user task, and "
       "that the task a system is intended to support must determine the "
       "metric rather than the reverse. Cremonesi et al. [37] made the point "
       "concretely: algorithms tuned to minimise rating-prediction error did "
       "not retain their advantage when the same models were evaluated on a "
       "top-N recommendation task, and an unpersonalised popularity ranking "
       "proved a strong competitor on that task. Their explanation is that "
       "held-out ratings are not a random sample of the items a user would "
       "have valued, because users rate popular items disproportionately, so "
       "a popularity ranking is rewarded by the sampling process itself."),
      ("p",
       "A further limitation applies to all three axes together. Knijnenburg "
       "et al. [38] show through controlled user studies that objective "
       "accuracy accounts for only part of a user's experience of a "
       "recommender, and that perceived quality, perceived effort and "
       "control mediate between the algorithm and the outcome a user "
       "reports. Offline measurement therefore bounds what may be claimed "
       "rather than settling it, a constraint that Section 5.9 returns to "
       "when stating the limits of this dissertation's own evaluation. Table "
       "2.2 compares the method families discussed in this section and "
       "states the role each plays in the present work."),
     ]),

    # -- new 2.2.5 and the whole of the new Section 2.3, placed before the
    #    heading that was 2.3 and is now 2.4.
    ("before",
     "2.4 Choice of Methods",
     [
      ("h3", "2.2.5 Cold Start and Data Sparsity"),
      ("p",
       "Every method family reviewed above degrades when a user is new, and "
       "the severity of that degradation determines which family a system can "
       "rely on at the moment a person first uses it. Schein et al. [39] give "
       "the standard formulation, separating the cold-start problem for new "
       "items, where no interaction history exists to place an item among its "
       "neighbours, from the harder case of new users, where nothing about "
       "preference is known at all. A methodological consequence follows, and "
       "this dissertation acts on it: cold-start performance cannot be read "
       "from an accuracy figure aggregated over all users, because the users "
       "who dominate such an average are those with the longest histories. "
       "Section 5.3 reports the two populations separately for that reason."),
      ("p",
       "That point is decisive for this project. The corpus used here is "
       "severely sparse, as Section 3.2.1 reports, and the "
       "great majority of its users have rated too few recipes for a "
       "latent-factor model to place them meaningfully in the factor space. "
       "A system evaluated only on its most active users would report a level "
       "of performance that almost none of its users would experience."),
      ("p",
       "Two responses appear in the literature. The first augments the "
       "collaborative model with content, as in the content-boosted "
       "factorisation of Forbes and Zhu [25], so that a single model degrades "
       "gracefully as evidence thins. The second switches between models "
       "according to how much evidence is available, which is the switching "
       "hybrid in Burke's taxonomy [49]. The present work takes the second "
       "route for a practical rather than a theoretical reason: a switching "
       "policy makes the basis of each recommendation explicit, and therefore "
       "reportable to the user, whereas a blended model yields a single score "
       "whose composition cannot be shown."),

      ("h2", "2.3 Critical Analysis and Research Gap"),
      ("p",
       "The systems reviewed in this chapter are individually strong and "
       "collectively incomplete. This project requires four capabilities at "
       "once: exclusion "
       "of unsafe or prohibited dishes with no possibility of override; "
       "planning across a multi-day horizon rather than a single meal; "
       "sensitivity to the temporal context in which a meal is eaten; and "
       "reported evidence that the plans produced meet nutritional targets. "
       "Assessed against those four, the reviewed work divides along a line "
       "that is not primarily technical."),
      ("p",
       "One group originates in clinical or dietetic practice. The Diet4You "
       "menu planner [16] and the flexible planner of Amiri et al. [12] treat "
       "exclusion as non-negotiable, the requirement to exclude being medical; "
       "the genetic-algorithm menu generator of Gaál et al. [33] works "
       "instead from numerical nutrient targets. All three plan over more "
       "than one meal, with a horizon closer to a course of treatment than to "
       "a single occasion, and all three report nutritional outcomes in some "
       "form. None models the temporal context in which a meal is eaten. A "
       "second group originates in recommendation research and inverts that "
       "profile: Freyne and Berkovsky [24], Forbes and Zhu [25], Ge et al. "
       "[26] and Harvey et al. [34] are concerned with rating or ranking "
       "accuracy rather than with exclusion, multi-day structure or "
       "nutrition. "
       "Between the two lie the systems that borrow from both. Elsweiler et "
       "al. [17] add a health objective to a ranking model and quantify what "
       "it costs in accuracy; Zhang et al. [11] treat exclusion as hard while "
       "relaxing softer preferences in a controlled order; Zioutos et al. "
       "[19] and Harvey and Elsweiler [32] generate whole plans against "
       "nutritional guidelines while leaving exclusion to a curated ontology "
       "or to the user; and Rostami et al. [27] are the only reviewed system "
       "to model when a meal is eaten, though they apply that signal to the "
       "ranking of individual dishes rather than to the composition of a "
       "plan."),
      ("p",
       "The consequence is that the two lineages report different quantities "
       "and neither reports the other's. The dietetic systems report "
       "nutritional adherence and rarely preference accuracy; the "
       "recommendation systems report ranking metrics and rarely whether the "
       "plans they produce are nutritionally sound. No reviewed system "
       "reports both for the same plans."),
      ("p",
       "The gap this project addresses is therefore the intersection rather "
       "than any single one of these capabilities. No reviewed system "
       "combines "
       "non-negotiable exclusion, a seven-day horizon, weekday and weekend "
       "differentiation, and a report of both ranking quality and nutritional "
       "attainment for the same plans. This is not a claim that the "
       "combination is difficult in principle, since each component exists "
       "somewhere in the work reviewed above. It is a claim that it has not "
       "been assembled and measured, and that assembling it exposes "
       "interactions the separate components do not show. Chapter 5 reports "
       "two of them: hard filtering applied on its own reduces the variety of "
       "plans produced for users with restrictive diets, an effect visible "
       "only when exclusion and diversity are measured on the same plans; and "
       "the advantage of the switching policy appears only when cold and "
       "active users are reported separately."),
      ("p",
       "A second and narrower gap concerns what is reported rather than what "
       "is built. Systems that enforce allergen exclusion describe the "
       "mechanism, but do not generally quantify how often that mechanism "
       "fails against real ingredient text. Because exclusion in this domain "
       "carries a safety implication, an unquantified filter is a weaker "
       "result than a quantified imperfect one: a reader can act on a known "
       "error rate and cannot act on an unstated one. Section 5.8 therefore "
       "reports a measured false-negative rate on manually labelled recipes "
       "that the lexicon was not built from, and Appendix B states plainly "
       "what that rate means for somebody relying on the system."),
     ]),

    # -- 2.4: why the reasoning has to be visible ----------------------------
    ("after",
     "The concrete algorithms, scoring function and software tooling that "
     "realise this design are specified in Chapter 3",
     [
      ("p",
       "One further property was treated as a requirement rather than an "
       "enhancement. Because the system must sometimes decline to offer a "
       "dish the user would enjoy, and must sometimes place a dish that is "
       "not their favourite in order to hold a day within its limits, the "
       "reason for each decision has to be available to them. Tintarev and "
       "Masthoff [40] distinguish several purposes an explanation may serve, "
       "among them transparency, trust and effectiveness, and note that these "
       "are neither interchangeable nor all served by the same design. The "
       "purpose relevant here is transparency about trade-offs. The scoring "
       "function is therefore composed of separately named terms whose "
       "individual contributions can be displayed, rather than a single "
       "learned quantity, and Section 3.5.2 specifies that decomposition."),
     ]),
]

# ---------------------------------------------------------------------------
# Rows appended to Table 2.1, so that the systems newly discussed appear in the
# summary alongside those already there.
# ---------------------------------------------------------------------------
TABLE_2_1_ADDITIONS = [
    ["Harvey et al. [34]", "Collaborative",
     "Rating prediction for recipes from learned representations of user "
     "taste"],
    ["Harvey & Elsweiler [32]", "Hybrid, plan-level",
     "Generates whole meal plans meeting daily nutritional guidelines while "
     "ranking dishes by predicted preference"],
    ["Gaál et al. [33]", "Constrained optimisation",
     "Weekly menu generation as a genetic-algorithm search over nutrient "
     "targets at meal, daily and weekly level"],
]

# ---------------------------------------------------------------------------
# New references, numbered by order of first appearance in Chapter 2.
# Every entry was verified against the publisher record or DBLP before being
# written into the text, and the verification links were put to the author for
# confirmation before this module was written.
# ---------------------------------------------------------------------------
NEW_REFERENCES = [
    (28, "Mahajan, P. and Kaur, P.D. 2024. A Systematic Literature Review of "
         "Food Recommender Systems. SN Computer Science, 5(1), article 174."),
    (29, "Min, W., Jiang, S., Liu, L., Rui, Y. and Jain, R. 2019. A Survey on "
         "Food Computing. ACM Computing Surveys, 52(5), article 92."),
    (30, "Trattner, C. and Elsweiler, D. 2017. Food recommender systems: "
         "important contributions, challenges and future research "
         "directions. arXiv:1711.02760."),
    (31, "Trattner, C. and Elsweiler, D. 2017. Investigating the healthiness "
         "of internet-sourced recipes: implications for meal planning and "
         "recommender systems. In: Proceedings of the 26th International "
         "Conference on World Wide Web (WWW '17). Perth: International World "
         "Wide Web Conferences Steering Committee, pp.489-498."),
    (32, "Harvey, M. and Elsweiler, D. 2015. Automated recommendation of "
         "healthy, personalised meal plans. In: Proceedings of the 9th ACM "
         "Conference on Recommender Systems (RecSys '15). Vienna: ACM, "
         "pp.327-328."),
    (33, "Gaál, B., Vassányi, I. and Kozmann, G. 2007. Application of "
         "artificial intelligence for weekly dietary menu planning. In: "
         "Advanced Computational Intelligence Paradigms in Healthcare - 2. "
         "Studies in Computational Intelligence, vol.65. Berlin: Springer, "
         "pp.27-48."),
    (34, "Harvey, M., Ludwig, B. and Elsweiler, D. 2013. You are what you "
         "eat: learning user tastes for rating prediction. In: String "
         "Processing and Information Retrieval (SPIRE 2013). Lecture Notes in "
         "Computer Science, vol.8214. Cham: Springer, pp.153-164."),
    (35, "Ferrari Dacrema, M., Cremonesi, P. and Jannach, D. 2019. Are we "
         "really making much progress? A worrying analysis of recent neural "
         "recommendation approaches. In: Proceedings of the 13th ACM "
         "Conference on Recommender Systems (RecSys '19). Copenhagen: ACM, "
         "pp.101-109."),
    (36, "Herlocker, J.L., Konstan, J.A., Terveen, L.G. and Riedl, J.T. 2004. "
         "Evaluating collaborative filtering recommender systems. ACM "
         "Transactions on Information Systems, 22(1), pp.5-53."),
    (37, "Cremonesi, P., Koren, Y. and Turrin, R. 2010. Performance of "
         "recommender algorithms on top-N recommendation tasks. In: "
         "Proceedings of the 4th ACM Conference on Recommender Systems "
         "(RecSys '10). Barcelona: ACM, pp.39-46."),
    (38, "Knijnenburg, B.P., Willemsen, M.C., Gantner, Z., Soncu, H. and "
         "Newell, C. 2012. Explaining the user experience of recommender "
         "systems. User Modeling and User-Adapted Interaction, 22(4-5), "
         "pp.411-504."),
    (39, "Schein, A.I., Popescul, A., Ungar, L.H. and Pennock, D.M. 2002. "
         "Methods and metrics for cold-start recommendations. In: "
         "Proceedings of the 25th Annual International ACM SIGIR Conference "
         "on Research and Development in Information Retrieval (SIGIR '02). "
         "Tampere: ACM, pp.253-260."),
    (40, "Tintarev, N. and Masthoff, J. 2011. Designing and evaluating "
         "explanations for recommender systems. In: Ricci, F., Rokach, L., "
         "Shapira, B. and Kantor, P.B. eds. Recommender Systems Handbook. "
         "Boston: Springer, pp.479-510."),
]
