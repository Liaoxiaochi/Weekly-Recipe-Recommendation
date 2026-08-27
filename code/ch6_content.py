"""Chapter 6 -- Conclusion and Future Work.

WHY THIS CHAPTER IS SHAPED THIS WAY.  The marking guidance places "quantified
outcomes of the study and ideas for future work" in the same criterion as the
evaluation, and asks that results be "clearly related to aim and
motivation/goals".  Chapter 5 reports the numbers; this chapter is where they
are read back against the four objectives stated in Section 1.2.  Section 6.2
therefore takes those objectives one at a time and says what was achieved,
citing the section and the figure that support each claim rather than asserting
success in general terms.

ON THE FOURTH OBJECTIVE.  Objective four promised "a small user-based usability
study" and no such study was run.  The supervisor advised on 18 August 2026
that seeking ethical approval at that stage of the project would not be a good
use of the time remaining.  That makes the omission a decision with a stated
basis rather than an unfinished task, and it is written here as one -- but the
objective is still recorded as partly met, because a decision not to do
something does not convert into having done it.

NO NEW REFERENCES.  Every citation here already appears in Chapter 2 or
Chapter 3.  Future work should point at literature the reader has already been
introduced to; a source appearing for the first time in a conclusion has not
been reviewed anywhere.
"""

BLOCKS = [

("h1", "Chapter 6 Conclusion and Future Work"),

# ---------------------------------------------------------------------------
("h2", "6.1  Conclusions"),

("p", "This project set out to produce a personalised weekly recipe "
      "recommender respecting a user's dietary restrictions while working "
      "towards their nutritional targets. A corpus of 128,403 recipes and "
      "655,954 interactions was prepared from the Food.com dataset, carrying "
      "per-serving quantities and allergen tags over the fourteen classes of "
      "Annex II to Regulation (EU) No 1169/2011 [43]. A user model turns "
      "anthropometric inputs into daily targets divided across meal slots. A "
      "content-based component and a matrix factorisation are selected "
      "between by how much history a user has, behind a constraint layer "
      "that removes what must not be offered before any ranking and "
      "expresses the rest as penalties. A planner assembles twenty-one meals "
      "into a week, presented as replaceable cards whose reasoning is shown "
      "as a sum of named terms."),

("p", "Six experiments evaluated it, reported in Chapter 5. One of them "
      "found a defect in the recommendation engine that the verification "
      "suite of Chapter 4 could not have found, which is discussed below "
      "because it bears on what this project can claim."),

# ---------------------------------------------------------------------------
("h2", "6.2  Achievement of the objectives"),

("p", "Objective O1 was to curate a cleaned recipe corpus augmented "
      "with per-serving nutritional values and ingredient-level allergen "
      "tags. This was met. Section 3.2 specifies the pipeline and Section 4.2 "
      "reports its execution: 231,637 raw recipes reduce to 128,403 usable "
      "ones, each carrying absolute nutritional quantities whose internal "
      "consistency was checked by reconstructing energy from macronutrients "
      "to a median relative error of 2.86 per cent. The allergen tagging is "
      "the part of this objective with a measured error rate rather than an "
      "assumed one: Section 5.8 reports a false-negative rate of 2.5 per cent "
      "against manual labels on 104 recipes the lexicon was not built from. "
      "The objective is met, and the quality of the result is stated as a "
      "number rather than asserted."),

("p", "Objective O2 was a user model capturing explicit preferences, "
      "dietary restrictions and a daily nutritional target derived from "
      "anthropometric inputs. This was met. Section 3.3 derives resting "
      "energy expenditure by the Mifflin-St Jeor equation [44], scales it by "
      "an activity factor and divides the result across meal slots, and "
      "Section 5.5 shows the consequence across twelve profiles: energy "
      "attainment averages 92.2 per cent of target with every one of the "
      "twenty-one meal slots filled. The profile also carries the "
      "restrictions that the constraint layer treats as non-negotiable, which "
      "is what makes the third objective enforceable."),

("p", "Objective O3 was a hybrid engine producing a seven-day plan "
      "that respects hard constraints, soft preferences and weekday-weekend "
      "context. This was met. Section 5.4 isolates what each layer "
      "contributes: an unfiltered popularity baseline produces 44 allergen "
      "violations and 65 dietary-regime violations across twelve profiles, "
      "and both fall to zero once the hard filter is applied, and remain at "
      "zero in the complete system. The switching policy selects the stronger "
      "component in each regime, as Section 5.3 shows. One "
      "element of this objective performed less well than intended and is "
      "reported as such: Section 5.7 shows that the bound on how often a main "
      "dish may recur never fires, so a feature that is implemented and "
      "exposed to the user has no effect on the plans produced."),

("p", "Objective O4 was to evaluate the system using "
      "rating-prediction metrics, nutritional adherence and a small "
      "user-based usability study. This was met in part. The technical "
      "evaluation was carried out in full and went beyond what the objective "
      "specified, adding an ablation across three system configurations, a "
      "parameter sensitivity analysis and an unbiased retest of the allergen "
      "lexicon on an independent sample. The usability study was not run. "
      "Such a study requires ethical approval, and the supervisor advised on "
      "18 August 2026 that beginning an application at that stage of the "
      "project would not be a sound use of the remaining time. The study "
      "materials had been prepared and are retained, but preparing them is "
      "not the same as running them, and this objective is therefore recorded "
      "as partly rather than fully achieved."),

# ---------------------------------------------------------------------------
("h2", "6.3  Contributions"),

("p", "The principal contribution is a working demonstration that four "
      "capabilities the literature of Section 2.3 shows to have been "
      "developed separately can be combined in one system: non-negotiable "
      "exclusion, a seven-day horizon, weekday and weekend differentiation, "
      "and reported measurement of both ranking quality and nutritional "
      "attainment for the same plans. Assembling them exposed interactions "
      "the separate components do not show. Hard filtering applied on its own "
      "reduces the variety of plans for users with restrictive diets, from "
      "twenty-one distinct main dishes to as few as sixteen, an effect the "
      "complete system reverses; and the advantage of the switching policy "
      "appears only when cold-start and active users are reported "
      "separately."),

("p", "A second contribution is methodological and arises from a failure "
      "rather than a success. The collaborative component passed the whole "
      "verification suite, predicted ratings more accurately than any "
      "baseline, and still ranked at chance, for the reason Section 5.3 "
      "gives. The general point is one this project can make from its own "
      "record rather than from the literature: a test suite certifies the "
      "behaviours its author thought to encode, and evaluation therefore "
      "belongs inside development rather than after it."),

("p", "A third contribution is a quantified allergen filter. Systems "
      "enforcing dietary exclusion commonly describe the mechanism without "
      "reporting how often it fails against real ingredient text; Section 5.8 "
      "reports that rate on an independent sample, with the four recipes the "
      "lexicon missed and why."),

# ---------------------------------------------------------------------------
("h2", "6.4  Limitations"),

("p", "Section 5.9 states the limitations in full. Three bound the "
      "contributions above directly: the absence of an independent user "
      "evaluation, the narrow and unrepresentative population on which the "
      "ranking results rest, and the reliance on the corpus's own "
      "user-contributed nutritional values."),

# ---------------------------------------------------------------------------
("h2", "6.5  Future work"),

("p", "The most valuable next step is the user study that was not run, and "
      "this project says something specific about when it should happen. "
      "Ethical approval is a lead-time cost rather than an effort cost: it "
      "must begin early to be available late, and cannot be compressed by "
      "working harder on it. A repetition of this work should submit the "
      "application in parallel with the first prototype rather than after it. "
      "Chapter 4 indicates what such a study would return: of twelve defects "
      "recorded there, six were found by a person using the system rather "
      "than by the test suite, and four of those concerned assumptions about "
      "what a user would want or understand. An author cannot write an "
      "assertion against their own assumption."),

("p", "The repetition bound of Section 3.6.5 should be made effective or "
      "removed. It is inert because each position is scored against what "
      "remains of that day's allowance, so no two positions pose the same "
      "problem and the recipe that wins one rarely wins another. Making it "
      "effective would require it to act on a candidate set genuinely shared "
      "across positions. Leaving a feature in place that a user asked for, "
      "that the interface exposes, and that does nothing is the least "
      "acceptable of the three options. The same section should also correct "
      "the time budget identified in Section 5.4, which is applied to the "
      "main dish and not re-applied when accompaniments are added."),

("p", "Two directions from the literature reviewed in Chapter 2 remain open. "
      "A food knowledge graph linking ingredients, dishes and nutritional "
      "concepts would allow substitution to be reasoned about rather than "
      "matched by string: Zioutos et al. [19] report improvements in both "
      "nutritional adherence and diversity from injecting a curated ontology "
      "into a weekly planner. The allergen failures of Section 5.8, which "
      "were baguette, corn flakes, brownie mix and queso fresco, are "
      "composite foods whose constituents an ontology would know and a "
      "lexicon cannot. Multimodal graph methods [22] report the strongest "
      "standalone ranking accuracy in this domain, though the caution of "
      "Ferrari Dacrema et al. [35] applies: their reported margins over "
      "well-tuned conventional baselines should be reproduced before being "
      "relied upon."),

("p", "Two limits of the data would repay attention before any of that. The "
      "corpus records ingredient names without quantities, so its recipes can "
      "be filtered, scored and scheduled, which is what this system does, "
      "but cannot be cooked from without following the link to the "
      "originating page. Recovering quantities, whether by parsing "
      "instruction text or by joining to a source that holds them, would let "
      "nutritional totals be computed rather than trusted, and would remove "
      "the dependence on user-contributed values noted in Section 6.4. "
      "Separately, the switching threshold of ten interactions was set from "
      "the observed distribution rather than tuned against an outcome; with "
      "the ranking evaluation of Section 5.3 now in place, it could be "
      "selected by sweeping it against NDCG measured separately in each "
      "population."),

("p", "Finally, the evaluation reported here is entirely offline, and Section "
      "2.2.4 sets out why that bounds rather than settles the question. An "
      "online comparison, in which users receive plans from the full system "
      "or from a configuration with one layer removed and their subsequent "
      "choices are observed, would measure what this dissertation has had to "
      "infer: whether a plan that satisfies a person's constraints and "
      "approaches their nutritional targets is one they actually cook."),

]
