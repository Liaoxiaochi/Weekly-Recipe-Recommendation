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
("h1", "Chapter 5 Software Testing and Evaluation"),

("p", "This chapter evaluates the system against the objectives of Section "
      "1.2. Testing of the software itself is reported where it was carried "
      "out, in Section 4.7: thirteen groups of assertions covering the "
      "corpus contract, the safety properties and the plan invariants, and "
      "a second suite that drives the interface in a browser. This chapter "
      "measures what the tested system then achieves. It reports rating "
      "prediction accuracy, top-N ranking quality "
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

("p", "Two properties of the corpus govern how the results should be read. "
      "The first is sparsity: the median user has rated exactly one recipe, "
      "and only 5.6 per cent have rated ten or more, so a held-out ranking "
      "experiment is possible only for the minority with enough history to "
      "hold anything out and describes that minority rather than users in "
      "general. The second is skew: 88.9 per cent of ratings are four or "
      "five stars, so precision is a weak discriminator and an absolute "
      "value of it carries no information without a baseline beside it. "
      "Every ranking result below is reported against a random and a "
      "popularity baseline."),

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
      "rating point, or 3.2 per cent. That is a modest margin, and it is "
      "the margin the corpus allows: with a mean rating of 4.41 and most "
      "of the mass at five, predicting the mean is already close to "
      "correct, and there is little variance left for a model to explain. "
      "This is the sparsity Section 2.2.2 identifies as the standing "
      "weakness of collaborative filtering, measured here on the corpus "
      "this system actually uses. The item mean "
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
      "fixed user the first two are constant and cannot affect an ordering, "
      "so ranking by the prediction ranks by item bias plus latent term. The "
      "item bias is estimated per recipe, and 76.9 per cent of recipes carry "
      "fewer than five ratings while 88.9 per cent of all ratings are four "
      "or five. A recipe rated once at five stars therefore acquires a large "
      "positive bias from a single observation and outranks every recipe the "
      "model has genuinely learned about. Scoring by the latent term alone, "
      "over the same 2,000 users, raised NDCG@10 from 0.0001 to 0.0025: the "
      "factorisation was never the problem, the bias term was. The two "
      "orderings also select differently: the top ten by predicted rating "
      "carry a median of three ratings each, against 53.5 by the latent "
      "term. The first was selecting recipes about which almost nothing is "
      "known."),

("p", "The component was therefore changed to expose its rating prediction "
      "and ranking signal separately, as Section 3.4.2 now specifies, and "
      "the experiment repeated. Table 5.2 reports the result: the correction "
      "raises the collaborative component from 0.0001 to 0.0025 and the "
      "deployed hybrid from 0.0004 to 0.0026, leaving the rating error of "
      "Table 5.1 untouched, since prediction still uses the full expression. "
      "Figure 5.1 shows the corrected picture."),

("tablecaption", "Table 5.2  Top-N ranking over 2,000 held-out users, before "
                 "and after the correction described above. Both columns come "
                 "from the same experiment run under the two orderings on the "
                 "same seed and the same split, so they are directly "
                 "comparable. Higher is better."),
("table", [
    ["System", "P@10", "NDCG@10 before", "NDCG@10 after"],
    ["Random", "0.0001", "0.0000", "0.0000"],
    ["Popularity", "0.0138", "0.0231", "0.0231"],
    ["Content-based", "0.0009", "0.0017", "0.0017"],
    ["Collaborative", "0.0014", "0.0001", "0.0025"],
    ["Switching hybrid (deployed)", "0.0015", "0.0004", "0.0026"],
]),

("image", "fig51_ranking.png", 4.6),
("figurecaption", "Figure 5.1  Ranking quality after the correction. The two "
                  "baselines are shown in grey, the two components in blue, "
                  "and the hybrid the system deploys in the darker shade."),

("p", "The correction also makes the switching policy of Section 3.4.3 "
      "testable, because it gives the collaborative branch something to be "
      "better at. The evaluated users separate into those with "
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

("p", "The popularity baseline's advantage is not an artefact of the cut-off "
      "chosen. Measured by recall, it retrieves 6.8 times as many held-out "
      "items as the deployed hybrid at K=5, 9.4 times as many at K=10 and 9.3 "
      "times at K=20: the gap widens as the list lengthens and then settles, "
      "rather than closing. This matters for how the result should be read. "
      "Were the advantage to narrow with K, it could be attributed to the "
      "hybrid ordering the right items slightly too low, which better tuning "
      "might fix. It does not narrow, which points instead at the sampling "
      "property described in Section 2.2.4: the held-out set is drawn from "
      "what users chose to rate, and popular items are over-represented in it "
      "at every depth."),


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
      "the dietary regime 65 times, while reaching 58 per cent of the energy "
      "target. It is the strongest ranker in Section 5.3 and it is "
      "unusable, because ranking well and planning safely are not the same "
      "capability. The second row isolates the hard filter: it removes every "
      "violation and improves nothing nutritionally, energy attainment "
      "falling because excluding recipes without replacing the scoring "
      "leaves a smaller pool ranked by the same popularity that ignored "
      "nutrition in the first place. The third row is what nutritional "
      "scoring adds: energy from 54 to 92 per cent of target, compliant days "
      "from 2.6 to 4.1. Each layer does work the layer below it does not."),

("p", "One column went against the system and is reported with the rest. "
      "Counting meals whose preparation time exceeds the stated budget for "
      "that day, the complete system produces more than either baseline. "
      "Part of that is not comparable: a baseline week serves one dish per "
      "meal while the system serves a main and up to two accompaniments. The "
      "rest is a genuine defect. The time budget is applied when the main "
      "dish is chosen and not re-applied when accompaniments are added, so a "
      "twenty-five minute main can acquire two twenty-minute sides against a "
      "thirty-minute budget. It is the same error as the clinical ceiling of "
      "Section 4.5, which bound one serving rather than the plate, and it "
      "survived because no assertion checked the plate's total time. Section "
      "6.5 lists the correction."),

("p", "A second effect is visible only per profile, and it shows the "
      "layers interacting rather than simply adding up. Averaged over "
      "twelve profiles the middle arm produces 18.9 distinct main dishes "
      "against the complete system's 21, but the difference is not spread "
      "evenly. On the vegetarian and vegan profiles the filtered baseline "
      "produces 16 distinct dishes in a week of 21 meals, and 17 on the "
      "vegetarian profile with an egg allergy, against 20 on the six "
      "unrestricted or mildly restricted ones. Filtering alone therefore "
      "concentrates the plans of exactly those users whose choices are "
      "already narrowest: the smaller the surviving pool, the more often "
      "the same popular survivor wins. The complete system returns all "
      "twelve to 21 distinct dishes, because scoring each slot against "
      "what remains of that day's allowance makes consecutive slots pose "
      "different problems. Exclusion and variety are not independent, and "
      "measuring them on separate plans would have hidden this."),

# ---------------------------------------------------------------------------
("h2", "5.5  Nutritional attainment"),

("p", "Twelve profiles spanning sex, age, body mass, activity level, dietary "
      "regime, declared allergens, clinical limits and stated ingredient "
      "preferences were each given a week, and every one returned a complete "
      "plan of twenty-one meals. Figure 5.2 sets the result against the "
      "targets of Section 3.3.2."),

("image", "fig53_nutrition.png", 4.6),
("figurecaption", "Figure 5.2  Nutritional attainment for twelve profiles. "
                  "Energy is the mean across the seven days; fat and sodium "
                  "are the worst single day, since a ceiling is a claim about "
                  "every day rather than about an average."),

("p", "The claim being tested here is the one Section 2.2.2 raises: fewer "
      "than 40 per cent of the recipes in a corpus of this kind meet World "
      "Health Organization criteria [31], so a plan drawn from it is "
      "nutritionally sound only if the system makes it so. Energy "
      "attainment ranges from 76 to 99 per cent of target, mean 92, and "
      "is an undershoot in every profile. The ceilings hold better: worst-day "
      "sodium from 81 to 102 per cent of the guideline, worst-day fat from 96 "
      "to 116. The number of days on which all four ceilings hold at once "
      "ranges from one to six of seven, which is the figure to quote when "
      "asked whether the system produces compliant weeks: it produces weeks "
      "close on every measure and exactly compliant on all four only some of "
      "the time. Section 3.5.2 predicted this, since only 4.1 per cent of the "
      "main-dish corpus satisfies all four at once, and a planner restricted "
      "to that subset could not also match preferences."),

("p", "The undershoot is the price of preference matching. An earlier "
      "version of this experiment used profiles with no stated preferences "
      "and reached 95 to 99 per cent, because with no preference signal "
      "the relevance term is constant and the planner may optimise energy "
      "alone. That figure measured a recommender with nothing to "
      "recommend; it is given only to make the trade-off visible."),

("p", "The shortfall is not spread evenly across the macronutrients, and "
      "where it falls says something about what the planner protects. "
      "Protein attainment is at or above target in all twelve profiles, "
      "ranging from 100.4 to 112.3 per cent, while carbohydrate tracks the "
      "energy shortfall closely at 76.6 to 100.7 per cent. The energy that is "
      "missing is therefore almost entirely missing carbohydrate. This was "
      "not designed for: the scoring function of Section 3.5.2 weights the "
      "macronutrients equally and carries no instruction to favour protein. "
      "It follows instead from the corpus, in which dishes dense in protein "
      "are common while dishes supplying carbohydrate without also supplying "
      "fat or sugar are not, so the planner meets the protein target early in "
      "each day and then finds the remaining allowance hard to fill without "
      "breaching a ceiling. The behaviour is defensible, but it is a property "
      "of the data rather than a decision, and it would need to be made "
      "explicit before the system were used by anyone whose carbohydrate "
      "intake mattered clinically."),

("p", "Restriction turns out to help rather than hinder on one measure. The "
      "two profiles furthest below the saturated-fat ceiling are the vegan "
      "profile at 45.3 per cent of the guideline and the milk-allergy profile "
      "at 62.6 per cent, against a range of 87.9 to 102.0 per cent across the "
      "remaining ten. Excluding dairy and meat removes the corpus's densest "
      "sources of saturated fat, so a constraint imposed for one reason "
      "relieves an unrelated nutritional pressure. This runs opposite to "
      "the intuition that restricted diets are harder to plan for, and because Section 5.6 finds the same "
      "direction of effect on diversity."),

# ---------------------------------------------------------------------------
("h2", "5.6  Diversity and coverage"),

("p", "Diversity within a week was measured as intra-list dissimilarity "
      "over the ingredient sets of the main dishes, the measure Section "
      "2.2.4 introduces from Ziegler et al. [50] and Section 3.6.5 "
      "adopts. The twelve plans score 0.925 out of a possible 1.0, "
      "and every plan used twenty-one distinct main dishes. Catalogue coverage was measured separately over "
      "thirty randomly varied profiles, since twelve plans cannot cover a "
      "corpus of 141,744 recipes and a figure from them would describe the "
      "number of plans rather than the recommender. Those thirty plans drew "
      "on 688 distinct recipes across 1,349 slots, or 0.49 per cent of the "
      "corpus. The more informative figure is the concentration: the single "
      "most frequently selected recipe accounts for 1.04 per cent of all "
      "slots, so the planner is not falling back on a small set of "
      "favourites. A blunter version of the same figure makes the point "
      "better: 411 of the 688 recipes selected, or 59.7 per cent, were used "
      "exactly once across all thirty plans."),

("p", "Diversity is also higher, not lower, for users with dietary "
      "restrictions. The two unrestricted profiles score 0.888 and 0.899 on "
      "intra-list dissimilarity, the lowest two of the twelve, while the "
      "milk-allergy and vegan profiles score 0.953 and 0.952, the highest; "
      "the mean over the ten restricted profiles is 0.932 against 0.893 for "
      "the two unrestricted ones. The explanation is a property of the "
      "measure rather than a merit of the system: dissimilarity is computed "
      "over ingredient sets, and excluding a widely used ingredient class "
      "removes the dishes that share it, so what survives is more spread out "
      "in ingredient space. Read together with Section 5.4, the two results "
      "bound each other. Filtering alone reduces the number of distinct "
      "dishes offered to restricted users, while the dishes that are offered "
      "are more different from one another. Neither figure means much without "
      "the other, and quoting only the favourable one would misrepresent the "
      "system."),

# ---------------------------------------------------------------------------
("h2", "5.7  Parameter sensitivity"),

("p", "The weight given to exceeding a guideline ceiling is the parameter the "
      "design is most sensitive to, and Figure 5.3 shows why it exists. With "
      "the ceilings unscored, worst-day free sugars reach 578 per cent of the "
      "guideline; at a weight of four they reach 103 per cent. Saturated fat "
      "falls from 192 to 100 per cent and sodium from 152 to 99 per cent over "
      "the same range. The adopted value of four is the smallest that brings "
      "sugar, saturated fat and sodium to within a few per cent of their "
      "ceilings."),

("p", "Total fat is the exception, and it is stated rather than passed over. "
      "It falls from 144 per cent of the guideline at a weight of zero to "
      "116 at a weight of four, a reduction of 28 points against the 475 "
      "removed from free sugars over the same range. It is the only one "
      "of the four that the parameter does not bring under control. Raising the weight "
      "further does not resolve it: between two and four the figure moves by "
      "14 points while the other three are already at their ceilings. The "
      "cause is that fat is present in almost every candidate rather than "
      "concentrated in a subset the way free sugars are, so penalising it "
      "does not point towards a different dish. This matches the worst-day "
      "range of 96 to 116 per cent in Section 5.5, and means the fat ceiling "
      "is the one guideline this system should not be described as holding."),

("image", "fig54_ceiling_weight.png", 4.6),
("figurecaption", "Figure 5.3  Worst-day nutrient totals against the weight "
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
      "they liked should be allowed to return within a week. At bounds of "
      "one, two and three the measured plans are identical: twenty-one "
      "distinct main dishes, the same diversity, the same mean relevance. "
      "Setting the repetition penalty of Section 3.5.2 to zero does not "
      "change this either, which rules out the obvious explanation. The "
      "cause is that each slot is scored against what remains of that day's "
      "nutritional allowance, so no two slots present the same problem and "
      "the recipe that wins one rarely wins another. The feature a user "
      "asked for is implemented and never fires. It is reported as a "
      "negative result rather than omitted, and Section 6.5 proposes what "
      "would make it active."),

# ---------------------------------------------------------------------------
("h2", "5.8  Allergen screening"),

("p", "The rate at which the screening misses an allergen that is "
      "genuinely present is the one measurement in this chapter with a "
      "safety consequence, and it requires data the rules were not built "
      "from. It also fills the gap Section 2.3 identifies, where systems "
      "that enforce exclusion describe the mechanism without reporting "
      "how often it fails. The "
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
      "principal limitation of the work. A usability study with three to "
      "five participants was planned and its materials prepared, but such a "
      "study requires ethical approval, and the supervisor, asked on 18 "
      "August 2026, advised that approval would in general be needed and "
      "that beginning an application at that late stage would not be a good "
      "idea. The study was therefore not run. Chapter 4 reports defects "
      "found by using the "
      "running system, but that use was by the author, who cannot be "
      "surprised by an interface he designed. Those observations are "
      "formative rather than evaluative, and no claim about usability "
      "rests on "
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
      "but to find a fault in it. The collaborative component satisfied "
      "every assertion in the verification suite, predicted ratings better "
      "than any baseline, and ranked at chance; none of the thirteen groups "
      "of checks in Chapter 4 could have detected that, because each tested "
      "a property the component genuinely had. It took an experiment "
      "measuring the quantity the component exists to produce. Evaluation "
      "therefore belongs inside development rather than in a report "
      "written after it."),

("p", "The popularity baseline's advantage needs the same care. It is "
      "tempting to read it as showing that personalisation does not work "
      "here, and on this metric it does. But the metric asks which individual "
      "recipes a user would have rated, and the system answers a different "
      "question: which twenty-one meals, taken together, respect a person's "
      "restrictions and approach their nutritional targets. A popularity "
      "ranking has no mechanism for excluding an allergen or balancing a day. "
      "The ranking experiment measures one input to the planner rather than "
      "its output, and Sections 5.4 to 5.7 measure the output."),

("p", "Neither finding is peculiar to this system. Cremonesi et al. [37] "
      "reported the first: models tuned to minimise rating-prediction error "
      "lost their advantage when ranked on a top-N task, where an "
      "unpersonalised popularity ranking was a strong competitor. That is "
      "precisely the pattern of Table 5.1 against Table 5.2, arrived at here "
      "independently. Herlocker et al. [36] gave the general "
      "form of the second: an accuracy measure is meaningful only relative "
      "to the task it is chosen for, and the task this system performs is "
      "not the one a top-N metric scores. Ferrari Dacrema et al. [35] add a "
      "caution that cuts the other way: well-tuned conventional baselines "
      "often survive comparison with far more elaborate methods, so the "
      "modest ranking figures here are not on their own evidence that a more "
      "sophisticated model would have done better."),


("p", "One boundary applies to all of it, and Section 2.2.4 anticipated it. "
      "Knijnenburg et al. [38] show that objective accuracy explains only "
      "part of what a person experiences when using a recommender. Every "
      "result in this chapter is an offline measurement: together they "
      "establish that the system produces plans with the properties it was "
      "designed to give them, and they cannot establish that a person offered "
      "such a plan would cook from it. That is the limitation recorded in "
      "Section 5.9."),

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
