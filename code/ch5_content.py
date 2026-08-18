"""Chapter 5 text, tables and figure placement.

Same block vocabulary as ch3_content.py and ch4_content.py.

EVERY NUMBER IN THIS CHAPTER COMES FROM outputs/eval_*.json, written by
code/evaluate.py.  None is typed in from memory, and verify_thesis.py checks
that the figures the chapter quotes for the corpus contract match the ones
Chapters 3 and 4 quote.

WHAT THIS CHAPTER IS HONEST ABOUT, because the temptation runs the other way:

  *  A popularity baseline outranks every personalised method tested here.
     That is reported in the first table of Section 5.3 rather than omitted,
     and Section 5.10 explains both why it happens and why it does not mean
     what it appears to mean.

  *  The evaluation found a defect in the recommender rather than merely
     scoring it.  Section 5.3 reports the defect, the diagnosis and the
     correction, with the measurement before and after.

  *  No independent user evaluation was carried out.  Section 5.9 says so
     plainly and treats it as the principal limitation of the work rather than
     as a gap to be glossed.

British English throughout.  No new citations: this chapter reports the
author's own experiments, and the external references it needs are established
in Chapters 2 and 3.
"""

BLOCKS = [

# ===========================================================================
("h1", "Chapter 5 Evaluation"),

("p", "This chapter evaluates the system against the objectives of Section "
      "1.2. It reports rating prediction accuracy, top-N ranking quality "
      "against four baselines, nutritional attainment, diversity and "
      "coverage, the sensitivity of the design to its main parameters, and "
      "the error rate of the allergen screening measured on data it was not "
      "built from. One experiment did more than measure the system: it found "
      "a defect in it, which Section 5.3 reports along with the correction."),

# ---------------------------------------------------------------------------
("h2", "5.1  Method and experimental setup"),

("p", "All experiments are driven by a single script, which writes its results "
      "to machine-readable files from which the tables and figures in this "
      "chapter are generated. No figure in this chapter contains a number "
      "entered by hand, so re-running the experiments regenerates the chapter's "
      "evidence rather than merely confirming it."),

("p", "Two properties of the corpus constrain what any offline experiment on "
      "it can show, and both are stated here because they govern how the "
      "results should be read. The first is sparsity: the median user has "
      "rated exactly one recipe, and only 5.6 per cent have rated ten or "
      "more. A held-out ranking experiment is therefore possible only for the "
      "minority with enough history to hold anything out, and its results "
      "describe that minority rather than users in general. The second is "
      "skew: 88.9 per cent of ratings are four or five stars. Precision is "
      "consequently a weak discriminator, and an absolute value of it carries "
      "no information without a baseline beside it. Every ranking result "
      "below is therefore reported against a random and a popularity "
      "baseline."),

("p", "The ranking experiment uses the 8,076 users who have at least ten "
      "interactions of which at least five are positive, taking a rating of "
      "four or more as positive. Two thousand of them were sampled, and "
      "twenty per cent of each user's positives held out. The factorisation "
      "was then retrained from scratch on the remaining interactions, so that "
      "no held-out interaction contributed to the model that ranks it; this "
      "retraining is the reason the model in this experiment reports a "
      "validation error of 1.1958 rather than the 1.1826 of the model "
      "trained on everything. Candidates are ranked over the whole corpus of "
      "141,744 recipes rather than against sampled negatives, and recipes the "
      "user rated in the training split are excluded from their own ranking."),

# ---------------------------------------------------------------------------
("h2", "5.2  Rating prediction"),

("p", "Table 5.1 reports the root mean squared error of the collaborative "
      "component against three baselines on 65,596 held-out ratings. Each "
      "baseline is fitted on the training split alone, as the model is."),

("tablecaption", "Table 5.1  Rating prediction error on 65,596 held-out "
                 "ratings. Lower is better."),
("table", [
    ["Method", "RMSE"],
    ["Matrix factorisation (this system)", "1.1826"],
    ["User mean", "1.2217"],
    ["Global mean", "1.2306"],
    ["Item mean", "1.2816"],
]),

("p", "The model improves on the strongest trivial baseline by 0.039 of a "
      "rating point, or 3.2 per cent. That is a modest margin, and it is the "
      "margin the corpus allows: with a mean rating of 4.41 and most of the "
      "mass at five, predicting the mean is already close to correct, and "
      "there is little variance left for a model to explain. The item mean "
      "performing worst of the three is itself informative, and Section 5.3 "
      "returns to it, because the same property that makes the item mean a "
      "poor predictor made an item-based term actively harmful for ranking."),

# ---------------------------------------------------------------------------
("h2", "5.3  Top-N ranking, and a defect the evaluation found"),

("p", "Ranking was evaluated first with the component exactly as Chapter 3 "
      "specified it, ordering recipes by predicted rating. The result was "
      "that the collaborative component ranked no better than chance: an "
      "NDCG@10 of 0.0001 against 0.0000 for a random ordering, on a model "
      "whose rating error beats every baseline in Table 5.1. A model that "
      "predicts well and ranks at chance is not a result to report and move "
      "on from; it is a symptom."),

("p", "The diagnosis is arithmetic. A predicted rating is a global mean plus "
      "a user bias plus an item bias plus the latent inner product. For a "
      "fixed user the first two are constant across recipes and cannot affect "
      "an ordering, so ranking by the prediction ranks by the item bias plus "
      "the latent term. The item bias is estimated per recipe, and 76.9 per "
      "cent of recipes in this corpus carry fewer than five ratings while "
      "88.9 per cent of all ratings are four or five. A recipe rated once, at "
      "five stars, therefore acquires a large positive bias from a single "
      "observation, and outranks every recipe the model has genuinely "
      "learned about. Scoring the same model by its latent term alone, "
      "measured over 300 held-out users, raised NDCG@10 from 0.0000 to "
      "0.0028: the factorisation was never the problem, and the bias term "
      "was. The effect is visible in what the two orderings select. The top "
      "ten recipes ranked by predicted rating have a median of six ratings "
      "between them; ranked by the latent term, the median is 92."),

("p", "The component was therefore changed to expose its rating prediction "
      "and its ranking signal separately, as Section 3.4.2 now specifies, and "
      "the whole experiment repeated. Table 5.2 reports the result. The "
      "correction raises the collaborative component from 0.0001 to 0.0025 "
      "and the deployed hybrid from 0.0004 to 0.0026, and leaves the rating "
      "error of Table 5.1 untouched, since rating prediction still uses the "
      "full expression. Figure 5.1 shows the corrected picture."),

("tablecaption", "Table 5.2  Top-N ranking over 2,000 held-out users, before "
                 "and after the correction described above. Higher is better."),
("table", [
    ["System", "P@10", "NDCG@10 before", "NDCG@10 after"],
    ["Random", "0.0001", "0.0000", "0.0000"],
    ["Popularity", "0.0138", "0.0231", "0.0231"],
    ["Content-based", "0.0009", "0.0017", "0.0017"],
    ["Collaborative", "0.0014", "0.0001", "0.0025"],
    ["Switching hybrid (deployed)", "0.0015", "0.0004", "0.0026"],
]),

("image", "fig51_ranking.png", 6.1),
("figurecaption", "Figure 5.1  Ranking quality after the correction. The two "
                  "baselines are shown in grey, the two components in blue, "
                  "and the hybrid the system deploys in the darker shade."),

("p", "The correction also makes the switching policy of Section 3.4.3 "
      "testable, because it gives the collaborative branch something to be "
      "better at. Figure 5.2 separates the evaluated users into those with "
      "fewer than ten ratings after the holdout, whom the controller routes "
      "to the content-based branch, and those with ten or more, whom it "
      "routes to the collaborative branch. On the first group the "
      "content-based component scores 0.0020 against the collaborative "
      "component's 0.0017; on the second the collaborative component scores "
      "0.0027 against the content-based component's 0.0017. The controller "
      "selects the stronger component in both regimes, which is the claim "
      "Section 3.4.3 makes and the reason the hybrid slightly exceeds either "
      "component alone. Of the 2,000 users, it routed 1,697 to the "
      "collaborative branch and 303 to the content-based one."),

("image", "fig52_switching.png", 6.1),
("figurecaption", "Figure 5.2  The switching policy selects the stronger "
                  "component in each regime. Left, users with too little "
                  "history for the collaborative branch; right, users with "
                  "enough."),

("p", "The popularity baseline nevertheless outranks every personalised "
      "method by roughly a factor of nine, and reporting that is more useful "
      "than explaining it away. Two things account for it. The first is a "
      "known property of offline evaluation on this kind of data: the "
      "held-out items are recipes the user chose to rate, people "
      "disproportionately rate recipes that are already popular, and a "
      "popularity ranking therefore predicts the test set partly by "
      "predicting the sampling process that produced it. The second is more "
      "fundamental and is taken up in Section 5.10: ranking individual recipes "
      "is not the task this system performs."),

# ---------------------------------------------------------------------------
("h2", "5.4  What each layer of the design contributes"),

("p", "The popularity baseline of Section 5.3 outranks every personalised "
      "method on held-out ratings. That result invites an obvious question, "
      "which this section answers directly: if a popularity ranker is the "
      "best recommender here, what happens when it is asked to do the job "
      "this system exists to do? Three arms were compared over the same "
      "twelve profiles. The first fills each slot with the most popular "
      "recipe for that meal, applying no restriction and optimising no "
      "nutrient. The second adds the hard filter of Section 3.5.1 and nothing "
      "else. The third is the complete system. Both baselines are given the "
      "meal-slot structure at no cost, since without it they would serve "
      "dessert for breakfast and the comparison would be with a straw man. "
      "Table 5.3 reports the three arms."),

("tablecaption", "Table 5.3  Three ways of producing a week, over twelve "
                 "profiles and 252 meals. Violations are totals; energy and "
                 "compliant days are means."),
("table", [
    ["", "Meals with a declared allergen", "Meals breaking the dietary regime",
     "Mean energy attainment", "Days all four ceilings met"],
    ["Popularity, unfiltered", "44", "65", "58.1%", "1.1 of 7"],
    ["Popularity with the hard filter", "0", "0", "54.0%", "2.6 of 7"],
    ["The complete system", "0", "0", "92.2%", "4.1 of 7"],
]),

("p", "The first row is the answer. A popularity ranker, left to plan a week, "
      "put a declared allergen on the plate 44 times in 252 meals and broke "
      "the user's dietary regime 65 times, while reaching 58 per cent of "
      "their energy target. It is the strongest ranker in Section 5.3 and it "
      "is unusable, because ranking well and planning safely are not the same "
      "capability. The second row isolates the hard filter: it removes every "
      "violation, which is what it exists to do, and it improves nothing "
      "nutritionally -- energy attainment in fact falls, because excluding "
      "recipes without replacing the scoring leaves a smaller pool ranked by "
      "the same popularity that ignored nutrition in the first place. The "
      "third row is what the nutritional scoring adds on top: energy from 54 "
      "to 92 per cent of target, and compliant days from 2.6 to 4.1. Each "
      "layer of the design is doing work that the layer below it does not."),

("p", "One column of this comparison went against the system and is reported "
      "with the rest. Counting meals whose preparation time exceeds the "
      "user's stated budget for that day, the complete system produces more "
      "of them than either baseline. Part of that is not comparable: a "
      "baseline week serves one dish per meal while the system serves a main "
      "dish and up to two accompaniments, so more cooking is being counted. "
      "The rest is a genuine defect. The time budget is applied when the main "
      "dish is chosen and is not applied again when accompaniments are added, "
      "so a twenty-five minute main can acquire two twenty-minute sides "
      "against a thirty-minute budget. It is the same error as the clinical "
      "ceiling described in Section 4.5, which bound the quantity in one "
      "serving rather than the quantity on the plate, and it survived because "
      "no assertion checked the plate's total time. Section 6.2 lists the "
      "correction."),

# ---------------------------------------------------------------------------
("h2", "5.5  Nutritional attainment"),

("p", "Twelve profiles were constructed to span sex, age, body mass, activity "
      "level, dietary regime, declared allergens, clinical limits and stated "
      "ingredient preferences, and a week was generated for each. Every one "
      "returned a complete plan of twenty-one meals. Figure 5.3 sets the "
      "result against the targets derived in Section 3.3.2."),

("image", "fig53_nutrition.png", 6.1),
("figurecaption", "Figure 5.3  Nutritional attainment for twelve profiles. "
                  "Energy is the mean across the seven days; fat and sodium "
                  "are the worst single day, since a ceiling is a claim about "
                  "every day rather than about an average."),

("p", "Energy attainment ranges from 76 to 99 per cent of target, with a mean "
      "of 92 per cent, and is an undershoot in every profile. The ceilings "
      "hold rather better: worst-day sodium ranges from 81 to 102 per cent of "
      "the guideline and worst-day fat from 96 to 116 per cent. The number of "
      "days on which all four ceilings are respected simultaneously ranges "
      "from one to six out of seven, which is the figure to quote when asked "
      "whether the system produces compliant weeks: it produces weeks that "
      "are close on every measure and exactly compliant on all four at once "
      "only some of the time. Section 3.5.2 predicted this, since only 4.1 "
      "per cent of the main-dish corpus satisfies all four ceilings at once, "
      "and a planner restricted to that subset could not also match "
      "preferences."),

("p", "The undershoot in energy is the price of preference matching, and it "
      "is instructive that it is visible at all. An earlier version of this "
      "experiment used profiles with no stated ingredient preferences; energy "
      "attainment was then 95 to 99 per cent, because with no preference "
      "signal the relevance term is constant and the planner is free to "
      "optimise energy alone. Adding preferences puts relevance into "
      "competition with the nutritional terms, and the profile with the "
      "highest energy target and the most specific tastes falls furthest "
      "short. The earlier figure measured a recommender with nothing to "
      "recommend, and is reported here only to make the trade-off visible."),

# ---------------------------------------------------------------------------
("h2", "5.6  Diversity and coverage"),

("p", "Within-week diversity was measured as the mean pairwise dissimilarity "
      "of the ingredient sets of the main dishes, on which the twelve plans "
      "score 0.925 out of a possible 1.0, and every plan used twenty-one "
      "distinct main dishes. Catalogue coverage was measured separately over "
      "thirty randomly varied profiles, since twelve plans cannot cover a "
      "corpus of 141,744 recipes and a figure from them would describe the "
      "number of plans rather than the recommender. Those thirty plans drew "
      "on 688 distinct recipes across 1,349 slots, or 0.49 per cent of the "
      "corpus. The more informative figure is the concentration: the single "
      "most frequently selected recipe accounts for 1.04 per cent of all "
      "slots, so the planner is not falling back on a small set of "
      "favourites."),

# ---------------------------------------------------------------------------
("h2", "5.7  Parameter sensitivity"),

("p", "The weight given to exceeding a guideline ceiling is the parameter the "
      "design is most sensitive to, and Figure 5.4 shows why it exists. With "
      "the ceilings unscored, worst-day free sugars reach 578 per cent of the "
      "guideline; at a weight of four they reach 103 per cent. Saturated fat "
      "falls from 192 to 100 per cent and sodium from 152 to 99 per cent over "
      "the same range. The adopted value of four is the smallest that brings "
      "all four nutrients to within a few per cent of their ceilings."),

("image", "fig54_ceiling_weight.png", 6.1),
("figurecaption", "Figure 5.4  Worst-day nutrient totals against the weight "
                  "given to exceeding a ceiling. The vertical scale is "
                  "logarithmic."),

("p", "The share of a slot's target assigned to the main dish proved almost "
      "immaterial: mean absolute energy deviation is 6.5, 6.2 and 6.0 per "
      "cent at shares of 0.55, 0.65 and 0.75, while the worst single day is "
      "best at 0.55, at 15.9 per cent against 21.9 and 19.2. The adopted "
      "value of 0.55 is therefore not optimal on the mean and is optimal on "
      "the worst case, which is the criterion that matters for a nutritional "
      "tool."),

("p", "The bound on how often a main dish may recur produced no effect at "
      "all. Section 3.6.5 introduced it after a user objected that a dish "
      "they liked should be allowed to return within a week, and undertook to "
      "quantify the resulting trade-off between variety and preference "
      "matching. At bounds of one, two and three the measured plans are "
      "identical: twenty-one distinct main dishes, the same diversity, the "
      "same mean relevance. Setting the repetition penalty of Section 3.5.2 "
      "to zero does not change this either, which rules out the obvious "
      "explanation. The cause is that each slot is scored against what "
      "remains of that day's nutritional allowance, so no two slots present "
      "the same problem and the recipe that wins one rarely wins another. "
      "The bound is therefore inert: the feature a user asked for is "
      "implemented and never fires. It is reported here as a negative result "
      "rather than omitted, and Section 6.2 proposes what would be needed to "
      "make it active."),

# ---------------------------------------------------------------------------
("h2", "5.8  Allergen screening"),

("p", "The rate at which the screening misses an allergen that is genuinely "
      "present is the one measurement in this chapter with a safety "
      "consequence, and it requires data the rules were not built from. The "
      "lexicon was revised using the errors found on the sample of 160 "
      "recipes described in Section 4.2, so its recall on that sample "
      "measures how thoroughly the repair was applied rather than how well "
      "the rules generalise. A second sample of 104 recipes was therefore "
      "drawn with a different seed, excluding every recipe in the first, and "
      "labelled by hand under the same policy: where a product's composition "
      "varies between brands the allergen is recorded as absent, which makes "
      "the resulting recall a lower bound rather than an optimistic figure. "
      "Table 5.4 reports the outcome."),

("tablecaption", "Table 5.4  Allergen screening against manual labels on 104 "
                 "recipes the lexicon was not built from."),
("table", [
    ["Class", "Truly present", "Missed", "Recall", "Precision"],
    ["Cereals containing gluten", "52", "3", "0.942", "1.000"],
    ["Milk", "58", "1", "0.983", "0.950"],
    ["Eggs", "36", "0", "1.000", "1.000"],
    ["Fish", "17", "0", "1.000", "0.944"],
    ["All four combined", "163", "4", "0.975", "0.975"],
]),

("p", "The false-negative rate is 2.5 per cent, against 5.7 per cent measured "
      "for the first version of the lexicon in Section 4.2. The four misses "
      "are a brownie mix and a cake using corn flakes, both sources of gluten "
      "the composite layer does not name; a baguette, which the layer simply "
      "lacks; and queso fresco, a cheese absent from the milk rules. None is "
      "subtle, and all four could be closed by adding four phrases. They have "
      "deliberately not been added. Repairing the lexicon using this sample "
      "would make it an in-sample measurement exactly as the first one was, "
      "and the figure in this table would stop meaning what it says. The "
      "value of an unbiased estimate lies in leaving it alone."),

("p", "Precision of 0.975 reflects the fail-closed policy working as "
      "intended. Three of the four false positives are milk rules firing on "
      "products whose composition varies, and the fourth is the fish rule "
      "firing on a dish containing shrimp paste and oyster sauce, which are "
      "crustacean and mollusc rather than fish under the regulation the "
      "classes follow. Each costs the user one option out of a hundred "
      "thousand; the errors in the other column could cost considerably more."),

# ---------------------------------------------------------------------------
("h2", "5.9  Limitations"),

("p", "No independent user evaluation was carried out, and this is the "
      "principal limitation of the work. A usability study with three to five "
      "participants was planned and its materials prepared, but such a study "
      "requires ethical approval, and on the supervisor's advice an "
      "application at this stage of the project was not a sound use of the "
      "time remaining. The study was therefore not run. That is the reason, "
      "and it is given plainly because the alternative -- presenting the "
      "absence of user evaluation as a considered methodological choice -- "
      "would be untrue. Chapter 4 reports defects found by "
      "using the running system, but that use was by the author, who cannot "
      "be surprised by an interface he designed and who knows what every "
      "control is for. Those observations are formative rather than "
      "evaluative, and no claim about usability in this dissertation rests on "
      "anything stronger. What can be said is bounded accordingly: the "
      "system produces complete plans for every profile tested, respects "
      "every declared restriction, and presents its reasoning in named terms, "
      "but whether a person unfamiliar with it can use it to plan a week is "
      "not established here."),

("p", "The ranking results are bounded in two further ways. They describe the "
      "5.6 per cent of users with enough history to hold data out, which is "
      "the population least representative of the cold-start majority the "
      "system is designed around. And they are measured against what those "
      "users happened to rate, which is not the same as what they would have "
      "cooked: a recipe absent from a user's history may be one they would "
      "have liked and never saw. Both are properties of offline evaluation "
      "rather than of this system, and neither is remedied by a larger "
      "sample."),

("p", "Finally, the nutritional results are computed from the corpus's own "
      "declared values. Section 3.2.3 establishes that those values are "
      "internally consistent to within a median of 2.86 per cent, but they "
      "are user-contributed and no independent verification of them was "
      "possible."),

# ---------------------------------------------------------------------------
("h2", "5.10  Discussion"),

("p", "The most useful thing this evaluation did was not to score the system "
      "but to find a fault in it. The collaborative component satisfied every "
      "assertion in the verification suite, predicted ratings better than any "
      "baseline, and ranked at chance, and none of the thirteen groups of "
      "checks in Chapter 4 could have detected that, because each tested a "
      "property the component genuinely had. It took an experiment measuring "
      "the quantity the component exists to produce. That is an argument for "
      "treating evaluation as part of development rather than as a report "
      "written after it, and this project can make the argument from its own "
      "record."),

("p", "The popularity baseline's advantage deserves the same treatment. It is "
      "tempting to read it as showing that personalisation does not work "
      "here, and on this metric it does show that. But the metric asks which "
      "individual recipes a user would have rated, and the system does not "
      "answer that question. It answers a different one: which twenty-one "
      "meals, taken together, respect a person's allergies and dietary "
      "regime, approach their nutritional targets, fit the time they have on "
      "each day, and do not repeat. A popularity ranking cannot answer that "
      "at all, because it has no mechanism for excluding an allergen or for "
      "balancing a day. The ranking experiment measures one input to the "
      "planner rather than the planner's output, and the results in Sections "
      "5.4 to 5.7 measure the output. Both belong in an evaluation, and "
      "confusing the first for the second would misrepresent what was built."),

("p", "Read together, the results support the design's central claims with "
      "one clear exception. The hard filter never admitted a declared "
      "allergen in any generated plan; the screening behind it misses 2.5 per "
      "cent of the allergens genuinely present, measured rather than assumed, "
      "and errs towards exclusion when it errs; the planner reaches 92 per "
      "cent of energy target while holding four guideline ceilings close; "
      "and the switching policy selects the better component in each regime. "
      "The exception is the repetition bound of Section 3.6.5, which is "
      "implemented, exposed to the user, and inert. It is the one place where "
      "the system does something other than what its documentation claims, "
      "and it was the evaluation that established this."),
]
