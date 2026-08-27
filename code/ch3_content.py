"""Chapter 3 text, tables and figure placement.

Kept separate from the docx builder so the prose can be revised without
touching the formatting code.  Block types:

    ("h1"|"h2"|"h3", text)      headings, styles 1 / 2 / 3 in the Leeds template
    ("p", text)                 body paragraph
    ("tablecaption", text)      caption, placed ABOVE its table
    ("table", [[...], ...])     first row is the header row
    ("image", filename, width)  width in inches
    ("figurecaption", text)     caption, placed BELOW its image
    ("algo", title, [lines])    pseudocode block
    ("eq", text)                displayed formula, centred italic

British English throughout.  Citation numbers continue from [27] in Chapter 2
and are assigned in order of first appearance.
"""

BLOCKS = [

# ===========================================================================
("h1", "Chapter 3 Software Requirements and System Design"),

("p", "This chapter sets out what the system has to do and how it is built "
      "to do it. Section 3.1 states the requirements and gives an overview "
      "of the design that follows from them. The remaining sections take "
      "the design in the order the system itself runs, from the data it "
      "starts with through to what the user finally sees."),

# ---------------------------------------------------------------------------
("h2", "3.1  Requirements and Design Overview"),

("h3", "3.1.1  Software Requirements"),

("p", "The system takes a user profile describing preferences, dietary "
      "restrictions and body data, and returns a seven-day menu of "
      "twenty-one meals. The objectives in Section 1.2 set four functional "
      "requirements on that menu, each of which is the obligation of a "
      "later section of this chapter:"),

("p", "FR1  Every declared restriction must be respected. An allergen, a "
      "religious rule or a clinical exclusion removes a recipe from "
      "consideration entirely (Section 3.5)."),

("p", "FR2  The menu must move the user towards their daily nutritional "
      "targets, which are derived from the anthropometric data in the "
      "profile rather than fixed in advance (Sections 3.3 and 3.5)."),

("p", "FR3  Weekdays must be distinguished from weekends, because "
      "preparation time available on the two differs (Section 3.6.4)."),

("p", "FR4  The menu must remain adjustable once presented. A user who "
      "rejects a dish must be able to replace it without discarding the "
      "rest of the week (Section 3.6.3)."),

("p", "Three non-functional requirements constrain how those four may be "
      "met, and they govern the design as a whole:"),

("p", "NFR1  Safety takes precedence over preference. No preference score "
      "may reinstate a recipe that a hard constraint has removed, and the "
      "filter errs towards exclusion where the data is ambiguous."),

("p", "NFR2  The system must be interpretable. The scoring function is a "
      "weighted sum of named terms rather than a single opaque prediction, "
      "so that the reason for placing or withholding a dish can be shown "
      "to the user."),

("p", "NFR3  The prototype must run unaided on a standard laptop. This "
      "rules out the graph and multimodal methods reviewed in Section "
      "2.2.3 and favours models whose expensive components can be computed "
      "once, offline, and reused."),

("h3", "3.1.2  Design overview"),

("p", "These requirements produce the four-layer architecture shown in "
      "Figure 3.1: a data layer holding the cleaned corpus and its derived "
      "attributes, a model layer holding the two recommenders and the "
      "switching controller, an application layer in which the weekly planner "
      "requests candidates and the constraint engine decides which are "
      "admissible and how they are penalised, and a single-page presentation "
      "layer. Each layer depends only on the one beneath it, so the "
      "recommenders can be replaced during evaluation without disturbing the "
      "planner or the interface."),

("image", "fig31_architecture.png", 4.5),
("figurecaption", "Figure 3.1  Layered architecture of the proposed system."),

# ---------------------------------------------------------------------------
("h2", "3.2  Data Pipeline Design"),

("p", "The recommendation engine cannot be designed independently of the "
      "corpus it ranks. This section specifies the pipeline that turns the "
      "raw Food.com export into a corpus with per-serving nutrition in "
      "grams, ingredient-level allergen tags and a meal slot for every "
      "recipe. Figure 3.2 shows the six stages and the quantities that "
      "survive each of them."),

("h3", "3.2.1  Source corpus"),

("p", "The system is built on the Food.com dataset released by Majumder et "
      "al. [41], spanning eighteen years of the site. The raw files used are "
      "RAW_recipes.csv, with 231,637 recipes, and RAW_interactions.csv, with "
      "1,132,367 ratings from 226,570 users. The figures usually quoted "
      "for this dataset refer to the filtered subset its authors prepared "
      "for their generation experiments; this work starts from the "
      "unfiltered files, so the corpus sizes here are not directly "
      "comparable with those in [41]."),

("p", "Each recipe record carries a name, a preparation time, an ingredient "
      "list, tags, preparation steps and a seven-element nutrition tuple; "
      "each interaction is a user, a recipe, a date and a rating. The "
      "pipeline retains these and derives four attributes: normalised "
      "ingredient identifiers, per-serving nutrition in grams, allergen "
      "labels, and a meal slot. Two absences shape the interface of Section "
      "3.7.2: the corpus holds no image of the finished dish, and no "
      "quantities. An ingredient list is a list of names, so a record states "
      "that a recipe uses honey and butter but not how much of either. A "
      "recipe here can be screened, scored and scheduled, which is what this "
      "system does, but not cooked from; the interface links each dish to "
      "its source page, which supplies the quantities and is also the "
      "attribution the dataset's terms deserve. Using the corpus's own "
      "nutrition values rather than joining to an external food-composition "
      "database is a recorded design decision: they are complete for every "
      "recipe, and ingredient-level matching would cost effort better spent "
      "on the recommendation and evaluation objectives."),

("h3", "3.2.2  Cleaning rules"),

("p", "Because the corpus is user-generated, a minority of records carry "
      "values that no downstream component can use: the most extreme "
      "recorded energy value is 434,360 kcal per serving, and 1,094 recipes "
      "declare a preparation time of zero minutes. Records are therefore "
      "removed if the name is missing, if the nutrition tuple is malformed, "
      "if declared energy is zero or exceeds 2,000 kcal per serving, if "
      "preparation time is zero or exceeds twenty-four hours, if fewer than "
      "two ingredients are listed, or if no preparation step is recorded. A "
      "final rule removes recipes that cannot be assigned to a meal slot, "
      "discussed in Section 3.6.1."),

("p", "The energy threshold is the only rule that discards a substantial "
      "number of otherwise plausible records, 6,072 of them. It is set at a "
      "whole adult daily requirement because a single serving at that level "
      "cannot participate in a balanced day, so such recipes are useless to "
      "the planner even where the figure is accurate. Applied in sequence, "
      "the rules retain 128,403 of the 231,637 raw recipes, or 55.43 per "
      "cent, on which 655,954 interactions fall. By far the largest "
      "reduction is the meal-slot rule, which alone accounts for 94,256 "
      "removals."),

("h3", "3.2.3  Nutritional normalisation"),

("p", "The nutrition tuple requires care, because only its first element is "
      "an absolute quantity. Energy is given in kilocalories per serving, "
      "but total fat, sugar, sodium, protein, saturated fat and carbohydrate "
      "are each expressed as a percentage of a daily value, the reference "
      "quantities used on United States nutrition labels [42]. A percentage "
      "cannot be added across a day's meals, nor compared against a target "
      "derived from a particular person's body, so all six fields must be "
      "converted to mass before anything else in this system can use them."),

("p", "That the corpus stores the percentage rather than the mass has to be "
      "established rather than assumed, because the originating site "
      "publishes both and the dataset documentation does not say which was "
      "captured. For recipe 61040 the stored tuple gives 24.0, 24.0, 33.0, "
      "66.0, 36.0 and 6.0 for fat, sugars, sodium, protein, saturated fat "
      "and carbohydrate, while the panel published for it reports those same "
      "six as 15.8 g, 6 g, 807.8 mg, 33.5 g, 7.4 g and 18.7 g, and as 24, "
      "24, 33, 66, 36 and 6 per cent of a daily value (food.com, accessed 14 "
      "August 2026). Every stored value matches the percentage and none the "
      "mass. Sodium settles it without the panel at all: a stored 33 cannot "
      "be grams, since that quantity of sodium would be fatal, whereas 33 "
      "per cent of a 2,400 mg reference is 792 mg."),

("p", "Conversion is therefore a multiplication by the reference quantity "
      "for each nutrient: 65 g of total fat, 25 g of sugars, 2,400 mg of "
      "sodium, 50 g of protein, 20 g of saturated fat and 300 g of "
      "carbohydrate. Energy is carried through unchanged. Five of those "
      "six are the values in force before the 2016 revision of the United "
      "States labelling rules, which is consistent with the period over "
      "which the corpus was collected, and dividing each published mass by "
      "its published percentage recovers them to within the rounding of the "
      "printed figures."),

("p", "Sugars are the exception and needed separate treatment, because the "
      "pre-2016 label carried no reference quantity for them at all. The "
      "site must therefore apply a figure of its own, and that figure can be "
      "recovered from the data rather than guessed. Sugars are a component "
      "of total carbohydrate and cannot exceed it in mass, which gives a "
      "test that every recipe in the corpus must pass. At a reference of "
      "25 g the constraint is violated by 6.1 per cent of recipes and never "
      "by more than 6 g, which is the scale of the rounding in the source "
      "data. At 50 g it is violated by 40.1 per cent of recipes and by as "
      "much as 479 g, which is not credible. The 25 g value is adopted. "
      "Section 4.2 reports an independent check of the conversion as a "
      "whole."),

("h3", "3.2.4  Allergen and dietary tagging"),

("p", "Allergen tagging is the part of the pipeline where a mistake can do "
      "real harm, and the part the source data supports least well. The "
      "corpus records ingredient names, not brands or sub-ingredients, so an "
      "allergen present only inside a composite product is invisible to any "
      "method matching the allergen's own name: Worcestershire sauce contains "
      "anchovy, pesto contains pine nuts, and most soy sauce contains wheat, "
      "yet none of those strings contains the words fish, nut or wheat."),

("p", "The design responds with a lexicon of three layers, applied over the "
      "fourteen classes European food information law requires to be "
      "declared [43]. The first matches the allergen itself; the second "
      "matches synonyms and derivatives sharing no substring with the class "
      "name, such as groundnut for peanut, casein and whey for milk, "
      "semolina for gluten and tahini for sesame; the third matches named "
      "foods that reliably contain the allergen without naming it. The "
      "ingredient map distributed with the corpus resolves 99.81 per cent of "
      "ingredient occurrences to a canonical form, supplying the vocabulary "
      "of Section 3.4.1, while the residue it cannot resolve is excluded "
      "rather than admitted. That is the fail-closed rule of Section 3.5.1: "
      "where the evidence is insufficient to decide, the recipe is "
      "removed. It is deliberately not applied "
      "before allergen matching, for a reason given in Section 4.2."),

("p", "Appendix A.2 lists the fourteen classes with a representative "
      "composite rule and the number of recipes each flags. The third layer is not a refinement but "
      "the substance of the method: of the 121,830 recipes flagged for "
      "gluten, 102,939 are flagged only by a composite rule, as are every "
      "one of the 41,737 sulphite flags. A lexicon restricted to direct and "
      "derived terms would miss those recipes entirely. Lupin does not occur "
      "in this corpus at all, which is unsurprising in a predominantly North "
      "American collection; the class is retained so that the rule set "
      "matches the legal list."),

("p", "A fourth element counteracts the cost of substring matching. Several "
      "phrases contain an allergen term while containing no allergen: "
      "coconut milk and soy milk are not dairy, butter beans and butternut "
      "squash are not butter, and an aubergine is not an egg. Such exempt "
      "phrases are blanked out of the ingredient text before matching. A "
      "phrase qualifies only if it never carries the allergen; one that "
      "merely usually lacks it is excluded, because the fail-closed policy "
      "prefers an unnecessary exclusion to a missed one. The counts reported "
      "are those of the revised lexicon, whose derivation is described in "
      "Section 4.2 and whose error rate is measured in Chapter 5."),


("p", "Two limits of the method shape the interface design in Section 3.7.2 "
      "and the evaluation in Chapter 5. First, the composite layer is "
      "deliberately over-inclusive: a rule flagging any flour as a source of "
      "gluten also flags almond flour. This costs precision, and it is the "
      "intended direction of error, since excluding an acceptable recipe "
      "deprives the user of one option among many whereas admitting an "
      "unacceptable one may cause harm. Second, some ingredient strings are "
      "undecidable from the data: an entry reading one package of cake mix "
      "cannot be resolved by any lexicon, because the information is not "
      "present. That is a limitation of the source data rather than a failure "
      "of the rules, and Section 3.5.1 specifies how such recipes are "
      "treated. The rate at which tagging misses allergens genuinely present "
      "is measured against a manually labelled sample in Chapter 5; it is not "
      "assumed to be zero, and the system is not presented to the user as "
      "though it were."),

("p", "The corpus also carries user tags asserting the absence of an "
      "allergen, such as gluten-free. These are never treated as evidence of "
      "safety, because they are unverified: 1,077 recipes tagged gluten-free "
      "and 926 tagged dairy-free contain an ingredient the lexicon flags. "
      "Where tag and rule disagree the rule prevails. Tags are used "
      "positively only for dietary preferences carrying no safety "
      "consequence, such as identifying the 35,651 vegetarian and 10,012 "
      "vegan recipes."),

("image", "fig33_data_pipeline.png", 4.3),
("figurecaption", "Figure 3.2  The data preparation pipeline, with the "
                  "quantity of data surviving each stage. Counts are "
                  "produced by the profiling script described in Section "
                  "4.2 and are reproducible from the raw files."),

# ---------------------------------------------------------------------------
("h2", "3.3  User Model Design"),

("h3", "3.3.1  Profile representation"),

("p", "A user profile has three parts. Restrictions are the hard part: "
      "allergen classes drawn from the fourteen of Annex II, an optional "
      "dietary regime such as vegetarian, vegan or halal, and a free list of "
      "ingredients the user will not eat. Preferences are the soft part: "
      "liked and disliked ingredients and cuisines, plus any ratings given "
      "during a session. Body data comprises age, sex, height, weight and an "
      "activity level. The separation matters because the three parts enter "
      "the pipeline at different points: restrictions are consumed by the "
      "filter, preferences by the ranker, and body data by the target "
      "calculation. None of it is persisted beyond the session, in line with "
      "Section 1.4."),

("h3", "3.3.2  Deriving daily nutritional targets"),

("p", "Daily energy requirement is estimated in two steps. Basal metabolic "
      "rate is computed with the Mifflin-St Jeor equation [44], which was "
      "derived on a healthy adult sample and is the predictive equation most "
      "commonly recommended for adults without a clinical condition. Writing "
      "w for body mass in kilograms, h for height in centimetres and a for "
      "age in years, it takes one of two forms according to sex:"),

("eq", "BMR = 10w + 6.25h - 5a + 5      (men)"),
("eq", "BMR = 10w + 6.25h - 5a - 161      (women)"),

("p", "Total energy expenditure is then obtained by scaling that quantity by "
      "a physical activity level, following the factorial approach used to "
      "set the United Kingdom dietary reference values for energy [45], so "
      "that TEE = BMR x PAL. The interface offers four bands: 1.4 for "
      "inactive, 1.6 for lightly active, 1.75 for active and 1.9 for very "
      "active. The band structure follows [45], but the choice of four is a "
      "design decision: it spans the range of ordinary adult activity while "
      "keeping the question simple enough that a user can answer it "
      "honestly, which matters more here than a finer gradation would, since "
      "the input is self-reported."),

("p", "Macronutrient targets are then expressed as proportions of that daily "
      "food energy, following the United Kingdom government dietary "
      "recommendations [46]: at most 35 per cent from total fat, at most 11 "
      "per cent from saturated fat, approximately 50 per cent from "
      "carbohydrate and at most 5 per cent from free sugars, with salt held "
      "at or below 6 g per day, equivalent to 2.4 g of sodium. Protein is "
      "the exception, specified in the same source as 0.75 g per kilogram of "
      "body weight per day rather than as a share of energy, and is "
      "converted to a daily mass before use."),

("p", "These are British reference values, whereas the figures used to "
      "decode the corpus in Section 3.2.3 are American. The distinction is "
      "deliberate rather than an inconsistency. The American values are a "
      "decoding key, needed only because that is how the source data was "
      "encoded; the British values define what the system steers a user "
      "towards, and are the appropriate standard for the population this "
      "work is written for."),

("h3", "3.3.3  Cold start"),

("p", "A new user of the prototype has no interaction history, so every "
      "preference signal must come from the profile form. Nutritional "
      "targets are unaffected, depending only on body data. Preference is "
      "initially represented by a pseudo-profile assembled from the liked "
      "ingredients and cuisines the user declares, treated exactly as though "
      "it were the aggregate of a short interaction history. Ratings "
      "collected during the session are appended to it, so the profile "
      "strengthens as the user interacts with the plan. The point at which "
      "that history becomes sufficient to switch recommenders is the subject "
      "of Section 3.4.3."),

# ---------------------------------------------------------------------------
("h2", "3.4  Recommendation Engine Design"),

("h3", "3.4.1  Content-based component"),

("p", "The content-based recommender represents each recipe as a sparse "
      "vector over a vocabulary of normalised ingredients and corpus tags, "
      "weighted by term frequency-inverse document frequency [47]. The "
      "inverse document frequency term is what makes this useful: salt and "
      "butter appear in much of the corpus and carry almost no preference "
      "information, whereas a distinctive ingredient identifies a style of "
      "cooking efficiently. A user is represented in the same space "
      "by the rating-weighted mean of their history, and candidates ranked "
      "by cosine similarity to it. Weights are taken relative to the "
      "midpoint of the rating scale rather than raw, so a rating below the "
      "midpoint moves the user vector away from that recipe; raw weights "
      "would make every rating positive, pulling the vector towards a dish "
      "just marked one star. Two properties matter for the design: the "
      "component scores recipes nobody has rated, and it composes cleanly "
      "with the hard filter, since removing candidates does not alter the "
      "scores of those that remain."),

("h3", "3.4.2  Collaborative component"),

("p", "The collaborative recommender factorises the user-recipe rating "
      "matrix into latent factors using truncated singular value "
      "decomposition with stochastic gradient descent, in the form that has "
      "become the standard baseline for rating prediction [48]. It "
      "predicts a rating as the sum of a global mean, a user bias, an item "
      "bias and the inner product of the user and item factor vectors. "
      "Its attraction is that it can capture preference structure that no "
      "ingredient-level representation exposes."),

("p", "The corpus, however, sets a hard limit on what this component can "
      "contribute. The matrix formed by 226,570 users and 231,637 recipes "
      "holds 1,132,367 ratings, a density of 0.0022 per cent. The median "
      "user has rated exactly one recipe; only 26.6 per cent have rated two "
      "or more, 10.2 per cent five or more and 5.5 per cent ten or more. On "
      "the item side, 76.9 per cent of recipes carry fewer than five "
      "ratings. Ratings are also skewed towards the top of the scale, with a "
      "mean of 4.41 and 72.1 per cent of them equal to five, which "
      "compresses the range over which the model can discriminate. A "
      "collaborative model estimated on this matrix will be reliable for a "
      "small minority of users and unreliable for the rest, which is "
      "precisely the situation a switching hybrid exists to manage."),

("p", "One consequence of that skew shapes how the model is used, and is "
      "stated here rather than left to the implementation. Predicting a "
      "rating and ordering a list of recommendations are different tasks, and "
      "this model serves them with different parts of itself. A predicted "
      "rating is the sum of the four terms above, but for one user only the "
      "item bias and the latent inner product vary across recipes, so ranking "
      "by the prediction is ranking by their sum. The item bias is exactly "
      "what a rating prediction needs and is unsuitable for ranking on a "
      "corpus this sparse, because a recipe rated once at five stars acquires "
      "a large bias estimated from that single observation and would be "
      "offered ahead of every recipe the model has genuinely learned "
      "something about. Recommendations are therefore ordered by the latent "
      "inner product alone, while the full expression is retained wherever a "
      "rating itself is wanted. Section 5.3 reports the measurement that "
      "established this, which was not anticipated when the component was "
      "first specified."),

("h3", "3.4.3  Contextual switching policy"),

("p", "Switching is the hybrid strategy in which a single recommender is "
      "selected per request according to a criterion evaluated at that "
      "moment, rather than combining several recommenders' outputs [49]. "
      "The criterion adopted here is the size of the user's interaction "
      "history: the collaborative component is used when the user has at "
      "least N interactions and the content-based component otherwise, as "
      "shown in Figure 3.3. Both branches then pass through a context "
      "adjustment for the day being planned before the result reaches the "
      "constraint engine."),

("p", "The threshold N is a design parameter, and the interaction "
      "distribution above determines the range in which it can sensibly lie. "
      "Setting it high enough for a well-estimated factor vector would "
      "exclude almost everyone: at N = 20 only 2.9 per cent of users would "
      "ever reach the collaborative branch. Setting it very low would route "
      "users to a model estimated from one or two observations. An initial "
      "value of N = 10 is adopted, admitting the 5.5 per cent of users with "
      "the densest histories while keeping at least ten observations behind "
      "every factor estimate. The consequence is stated rather than "
      "concealed: under this policy the system operates in content-based "
      "mode for the large majority of users, and for every new user of the "
      "prototype. That argues for the design rather than against it, since a "
      "pure collaborative system would have nothing to offer those users at "
      "all. The sensitivity of the results to N is examined in Chapter 5."),

("image", "fig34_interactions.png", 4.4),
("figurecaption", "Figure 3.3  Proportion of Food.com users with at least N "
                  "rated recipes. The curve collapses immediately: whatever "
                  "threshold is chosen, the collaborative branch serves a "
                  "small minority."),

# ---------------------------------------------------------------------------
("h2", "3.5  Constraint Handling Design"),

("h3", "3.5.1  Hard constraints as a pre-ranking filter"),

("p", "Hard constraints are applied as a filter over the candidate set "
      "before any preference score is computed, the arrangement formalised "
      "in the Diet4You menu planner [16] and adopted here for the reasons "
      "given in Section 2.2.4. Four categories are treated as hard, and are "
      "distinguished from the soft categories of Section 3.5.2. Three of "
      "them are "
      "familiar: declared allergens, religious or ethical rules, and "
      "clinical exclusions. The fourth is a consequence of the tagging "
      "limits described in Section 3.2.4."),

("p", "That fourth category implements the fail-closed principle. Where a "
      "user declares an allergy and a candidate contains an ingredient that "
      "could not be resolved to a canonical form, the system cannot "
      "establish that the recipe is free of the allergen, and so excludes it "
      "rather than admitting it. The asymmetry is deliberate: wrongly "
      "excluding a recipe removes one option from a corpus of over a hundred "
      "thousand, whereas wrongly admitting one may cause harm. Measurement "
      "makes the policy affordable, since only 1.47 per cent of the cleaned "
      "corpus contains an unresolvable ingredient, so the strictest available "
      "rule costs a negligible part of it. Had that proportion been "
      "large, a weaker policy of demoting rather than excluding such recipes "
      "would have been necessary, and the design would have had to say so."),

("p", "A fifth rule removes recipes using ingredients the user has typed "
      "into a free-text exclusion list. It is a hard rule in the same sense "
      "as the others, but it carries no safety claim: it expresses a "
      "preference, and it is matched by a different and weaker mechanism "
      "than declared allergens, which are matched by the three-layer lexicon "
      "of Section 3.2.4. The distinction matters enough to state plainly, "
      "because nothing said about preference matching extends to allergens. "
      "Where the two disagree the stricter applies. Section 4.5 gives the "
      "matching rule and the error it is designed to make."),

("h3", "3.5.2  Soft constraints as ranking penalties"),

("p", "Soft constraints reduce a recipe's score without removing it. For a "
      "candidate recipe r offered to user u for slot s on day d, given the "
      "partial plan P built so far, the score is"),

("eq", "score(r) = a . rel(r, u) - b . E(r, s) - c . M(r, s) "
       "- d . D(r, P) - e . T(r, d)"),

("p", "where rel is the relevance returned by whichever recommender the "
      "controller selected, normalised to the unit interval; E is the "
      "absolute relative deviation of the recipe's energy from the slot "
      "allowance; M is the nutritional error, defined below; D is the "
      "proportion of the recipe's ingredients already appearing in the "
      "partial plan; and T is the amount by which preparation time exceeds "
      "the day's budget, as a proportion of that budget and floored at zero. "
      "The weights a to e are set initially to 1.0, 0.4, 0.3, 0.2 and 0.1, "
      "giving preference the largest single influence while allowing the "
      "nutritional terms to dominate in combination when a candidate is "
      "badly matched. These are starting values, tuned in Chapter 5. Because "
      "the function is an additive sum of named terms, each contribution can "
      "be displayed alongside a recommendation, which is what requirement N2 "
      "asks for."),

("p", "The M term distinguishes between the two kinds of quantity Section "
      "3.3.2 sets out, because the guidance does. Protein and carbohydrate are "
      "amounts to reach and are penalised for deviation in either direction; "
      "fat, saturated fat, free sugars and salt are ceilings not to exceed and "
      "are penalised only for exceedance, so nothing pushes a plan to eat up "
      "to a limit. The two groups are averaged separately and then combined, "
      "rather than pooled, so that a ceiling which is being violated is not "
      "diluted by three which are being respected."),

("p", "Both E and M are measured against what the day has left rather than "
      "against a fixed share of it. The allowance for a slot is the daily "
      "figure less what the earlier meals of that day actually supplied, "
      "divided among the slots still to be filled in the proportions of "
      "Section 3.6.1. A heavy breakfast therefore tightens lunch and dinner "
      "automatically, where a fixed share would let the day's errors "
      "accumulate unchecked."),

("p", "One consequence constrains what the system can achieve rather than "
      "how well it is built, and is stated plainly. Only 4.1 per cent of the "
      "main-dish corpus, and 414 of the 19,919 breakfast candidates, satisfy "
      "all four guideline ceilings simultaneously when scaled to the energy "
      "they supply. Food.com is a collection of what people cook, not a "
      "curated database, and a planner restricted to fully compliant recipes "
      "would choose from a twenty-fifth of the corpus, defeating both "
      "preference matching and variety. The ceilings are therefore soft "
      "constraints the score genuinely minimises rather than hard filters, "
      "and Chapter 5 reports how closely plans hold to them."),

("h3", "3.5.3  Adaptive relaxation"),

("p", "Each soft term additionally carries a tolerance beyond which a "
      "candidate is not acceptable for the slot at all, rather than merely "
      "ranked below its rivals. The tolerances exist because relaxation "
      "otherwise has nothing to act on: a ranking always returns a winner "
      "from a non-empty candidate set, so a system whose soft stage only "
      "ranked could never reach the situation this section describes. They "
      "also govern how far the ranker may trade nutritional accuracy for "
      "preference, since relevance carries the largest weight in the scoring "
      "function; the energy tolerance is set at 15 per cent of the slot "
      "target for that reason, a value chosen by measurement and reported in "
      "Chapter 5."),

("p", "A user with several restrictions and a demanding energy target can "
      "leave a slot with no acceptable candidate. The system responds by "
      "relaxing soft constraints in a fixed order, following the pattern "
      "described by Zhang et al. [11]: the preparation-time budget is "
      "loosened first, then the repetition penalty, then the macronutrient "
      "deviation, and finally the energy deviation. Each step widens the "
      "admissible set without touching the filter."),

("p", "Hard constraints are never relaxed, and allergen filters in "
      "particular are never relaxed under any circumstance, including the "
      "case where relaxing them is the only way to return a complete plan. "
      "If a slot cannot be filled after all soft relaxations are exhausted, "
      "the system returns an incomplete week and reports which slots it "
      "could not fill and why. Returning a plan with a gap in it is a worse "
      "user experience than returning a full one, and it is the correct "
      "behaviour: the alternative is to present the user with a meal the "
      "system has reason to believe they cannot safely eat."),


# ---------------------------------------------------------------------------
("h2", "3.6  Weekly Plan Generation"),

("h3", "3.6.1  Problem formulation"),

("p", "A weekly plan is an assignment of one recipe to each of twenty-one "
      "slots, a slot being one meal on one day: breakfast, lunch or dinner "
      "on each of the seven days. The word is used in that sense "
      "throughout. Two things must hold "
      "for a slot to be fillable: the corpus must contain recipes "
      "appropriate to that meal, and each slot must carry its own share of "
      "the daily energy target. Neither is given by the source data, so both "
      "are constructed."),

("p", "Meal appropriateness is derived from the course tags contributed by "
      "the site's users. Desserts, beverages, condiments, sauces and "
      "preserves are excluded as accompaniments rather than meals; of the "
      "remainder, breakfast and brunch map to breakfast, sandwiches and soups "
      "to lunch, and main-dish, meat and seafood to dinner. This resolves "
      "56.75 per cent of the raw corpus to at least one slot, leaving 19,919 "
      "breakfast, 40,779 lunch and 103,389 dinner recipes after the other "
      "cleaning rules. Breakfast is much the thinnest, which constrains how "
      "much variety the planner can offer there relative to dinner. Recipes "
      "with no usable course tag are removed by the last cleaning rule of "
      "Section 3.2.2, the largest single reduction in the pipeline, but not "
      "all of them leave the system: 13,341 of the 94,256 removed are tagged "
      "as something served beside a meal, and these form the accompaniment "
      "pool. The pool is disjoint from the main corpus, so no dish can be "
      "served as its own accompaniment."),

("p", "The daily energy target is divided between the three slots in the "
      "proportions 25, 35 and 40 per cent for breakfast, lunch and dinner. "
      "This split is a design choice rather than a derived quantity, "
      "intended to place the largest meal in the evening in line with common "
      "practice in the United Kingdom; it is exposed as a parameter so that "
      "the effect of alternative splits can be examined."),

("p", "A slot is therefore an energy quantity as well as a category, and the "
      "corpus does not supply single recipes at that scale: the median dinner "
      "candidate provides 381 kcal per serving where the dinner slot of a "
      "2,440 kcal day asks for 976. A slot is consequently filled by a main "
      "dish together with the accompaniments needed to reach its target, at "
      "most two of them, drawn from the pool identified above, with the "
      "serving count capped at one and a half, which is a larger helping "
      "rather than a second dinner. Section 4.6 reports the measurement that settled this "
      "choice against the alternative of repeated servings, and fixed the "
      "share of the slot target the main dish is ranked against."),

("p", "An accompaniment is admitted only if it brings the plate closer to the "
      "target and only if it is substantial enough to be worth cooking, so a "
      "slot whose main dish already meets its target is served alone. Every "
      "constraint of Section 3.5 applies to an accompaniment exactly as it "
      "does to a main dish: an allergen on a side dish is as dangerous as one "
      "on a main. Ceilings arising from a clinical restriction are applied to "
      "the whole plate, since it is the plate the user eats, and where such a "
      "ceiling conflicts with the energy target the plate is left short "
      "rather than taken over the limit, the hard constraint prevailing over "
      "the soft one."),

("h3", "3.6.2  Plan construction"),

("p", "Slots are filled greedily in day order, but a purely greedy rule has a "
      "defect that matters here: the highest-scoring breakfast may consume "
      "so much of the day's energy allowance that no acceptable lunch or "
      "dinner remains. A look-ahead term corrects this, estimating for each "
      "candidate whether the day's remaining slots can still be filled "
      "within the residual budget and penalising those that would leave the "
      "remainder infeasible."),

("p", "The procedure works through the week one meal at a time, taking the "
      "days from Monday and, within each day, breakfast then lunch then "
      "dinner. At each of the twenty-one positions the candidate set is "
      "narrowed to recipes tagged for that position, and the hard filter of "
      "Section 3.5.1 then removes everything the user must not be offered. "
      "That step is never skipped and never relaxed; if it empties the "
      "candidate set, the position is recorded as unfilled rather than "
      "filled with something inadmissible. Each survivor is scored as its "
      "relevance to the user less the soft penalties of Section 3.5.2, whose "
      "nutritional part is measured against the main dish's share of the "
      "position's target rather than the whole of it, because accompaniments "
      "supply the remainder."),

("p", "Only the fifty highest-scoring candidates go forward to the "
      "look-ahead, which adds to each an estimate of whether the positions "
      "still to be filled that day could be filled within the energy the "
      "choice would leave behind. Restricting it this way keeps the cost of "
      "each position linear in the size of the filtered candidate set, since "
      "the expensive feasibility estimate is computed a fixed number of "
      "times rather than once per candidate. The best candidate after that "
      "adjustment becomes the main dish, and at most two accompaniments are "
      "added one at a time, each chosen against the energy still outstanding "
      "on the plate and stopping when the plate is close enough to target or "
      "no admissible accompaniment would improve it. The same hard filter "
      "applies to them as to the main dish."),

("p", "Once all twenty-one positions have been attempted, any left unfilled "
      "trigger the adaptive relaxation of Section 3.5.3, which loosens soft "
      "constraints in a fixed order and retries; hard constraints take no "
      "part in it. The planner returns the plan together with any positions "
      "it could not fill, rather than silently returning a shorter week."),

("p", "The procedure is deterministic given a profile: the same inputs "
      "produce the same week every time, with no random tie-breaking "
      "anywhere. That matters for the evaluation in Chapter 5, where a "
      "difference between two configurations has to be attributable to the "
      "configuration rather than to chance."),

("h3", "3.6.3  Replacing a meal"),

("p", "A plan the user cannot change is of little use, because no model of "
      "preference will be right about all twenty-one slots. The planner "
      "therefore keeps the whole ranked candidate list for each slot rather "
      "than discarding everything except the chosen recipe, and the "
      "interface offers a single control that swaps the current recipe for "
      "the next candidate in that list."),

("p", "A replacement is not simply the next-highest score. The candidate "
      "must still pass the hard filter, which is re-applied rather than "
      "assumed, and it must still leave the remaining slots of that day "
      "feasible under the look-ahead test of Section 3.6.2. Without the "
      "second check a user could exhaust the day's energy budget by "
      "repeatedly replacing breakfast, leaving the planner unable to fill "
      "the evening. If no candidate satisfies both conditions the slot is "
      "left unchanged and the user is told why. The accompaniments are chosen "
      "afresh for the new main dish rather than carried across, since they "
      "exist to close the gap between that dish and the slot target and a "
      "different dish leaves a different gap."),

("p", "Each rejection is also information. The replaced recipe is recorded "
      "as a negative preference signal and fed back into the user model, so "
      "that a user who rejects three fish dishes stops being offered them. "
      "This gives the system a source of feedback that does not require the "
      "user to rate anything explicitly, which matters given how few "
      "explicit ratings the corpus shows a typical user producing. It also "
      "yields a directly observable usability measure: the number of "
      "replacements a participant needs before accepting a week is a "
      "behavioural quantity rather than a self-reported one, and Chapter 5 "
      "reports it alongside the questionnaire results."),

("h3", "3.6.4  Weekday and weekend differentiation"),

("p", "Section 2.1.3 reported evidence that weekdays and weekends differ "
      "systematically in energy intake, macronutrient distribution and meal "
      "timing [14]. The system expresses this through the preparation-time "
      "budget rather than the nutritional target. The user supplies two "
      "budgets, a shorter one for weekdays and a longer one for weekends, "
      "and the penalty term T of Section 3.5.2 is evaluated against "
      "whichever applies to the day being planned, so that quick recipes "
      "dominate Monday to Friday while longer preparations become "
      "competitive at the weekend. Energy and macronutrient targets are held "
      "constant across the week: the evidence describes what people do "
      "rather than what a recommender should encourage, and a system whose "
      "purpose is nutritional balance should not build a weekend excess into "
      "its own targets."),

("h3", "3.6.5  Diversity control"),

("p", "A plan satisfying every constraint can still be unusable if it repeats "
      "the same few recipes, and an accuracy-optimal ranker tends to produce "
      "exactly that, since the recipes closest to a profile resemble one "
      "another. The repetition term D of Section 3.5.2 penalises ingredient "
      "overlap with the partial plan, a within-list application of the topic "
      "diversification of Ziegler et al. [50]. The same measure, intra-list "
      "dissimilarity over ingredient sets, is reported in Chapter 5, so the "
      "cost of diversity is quantified rather than assumed."),

("p", "How often a dish may reappear is a second question. Repetition is "
      "bounded rather than forbidden: a main dish may appear up to a stated "
      "number of times across the week, two by default, while accompaniments "
      "never repeat, so a dish that comes round twice arrives in different "
      "company. The bound is exposed to the user because how much variety a "
      "week should carry is a preference, not a property of the corpus. An "
      "earlier version barred a recipe outright once placed, assuming nobody "
      "would regard the same dish twice in a week as a recommendation; "
      "Section 4.6 records how that was tested and withdrawn. Exposing the "
      "bound has a second use: it is the parameter along which the accuracy "
      "cost of diversity is measured in Chapter 5, so the trade-off this "
      "section describes is instrumented by the same control the user "
      "operates."),

# ---------------------------------------------------------------------------
("h2", "3.7  System Architecture and Interface"),

("h3", "3.7.1  Module decomposition"),

("p", "The layers of Figure 3.1 map onto six Python modules, one for each "
      "concern the chapter has described: the data pipeline of Section 3.2, "
      "the user model of Section 3.3, the two recommenders and their "
      "switching controller, the constraint engine, the weekly planner, and "
      "the interface. The boundaries follow the layering, so no module calls "
      "upward, and the two recommenders share an interface so that either, "
      "or one of the baselines used in the evaluation, can be substituted "
      "without changing the planner. The module-by-module breakdown belongs "
      "with the code itself and is given in Chapter 4."),

("h3", "3.7.2  Interface design"),

("p", "The interface is a single page; Figure 4.1 shows it as built. A "
      "sidebar "
      "collects the profile: body data and activity level, the two "
      "preparation-time budgets, and the restriction controls. The main pane "
      "presents the week at two scales, because one layout cannot serve both "
      "purposes the user has. A compact strip shows seven days across, giving "
      "the shape of the week and the weekday-weekend difference at a glance; "
      "below it the same week is laid out a day at a time, at a width that "
      "accommodates the ingredient lists the screening policy requires to be "
      "open."),

("p", "A card is the unit the user acts on. Each carries the meal slot, the "
      "main dish, its accompaniments, the total for the plate, the "
      "preparation time, any allergen class flagged anywhere on the plate "
      "rather than on the main dish alone, the full ingredient list of every "
      "dish, and a control that replaces the recipe under the rules of "
      "Section 3.6.3. What a card cannot show is a photograph, because the "
      "corpus holds no images: a real limitation for an interface whose "
      "subject is food, and the reason a card leads with the name and the "
      "figures a user judges a meal by. Beneath the week, each day's totals "
      "are set against the targets of Section 3.3.2, so the nutritional "
      "attainment measured in Chapter 5 is visible to the user rather than "
      "confined to the evaluation."),

("p", "Three features follow from the limits established in Section 3.2.4. "
      "Ingredient lists are expanded by default rather than hidden behind a "
      "control, so a user with an allergy can check without further "
      "interaction. A persistent notice states that screening is automated "
      "and is not a safety guarantee, which describes what the system does: "
      "it screens, and screening has a false-negative rate that Chapter 5 "
      "quantifies. Presenting that as a guarantee would misrepresent the "
      "method and encourage the reliance the fail-closed filter exists to "
      "make unnecessary."),

("p", "The third is less obvious. A plan is built when the user asks for one, "
      "so a restriction edited in the sidebar does not by itself change what "
      "is on screen. For a preference that is merely stale; for a restriction "
      "it is unsafe, because the user has just declared an exclusion and the "
      "system appears to have accepted it while still displaying meals chosen "
      "before it. The interface therefore compares the sidebar against the "
      "profile the displayed plan was built from, and where any restriction "
      "differs it labels the plan out of date and withholds every action "
      "until the week is rebuilt. A screening rule applied to a plan the user "
      "is no longer looking at provides no protection."),

("p", "Selecting a dish opens a detail view, the finest unit the interface "
      "presents, carrying the recipe's own description and method, its "
      "ingredient list, what it supplies against what the slot allows, its "
      "place in the week, and the named score terms that selected it. It also "
      "carries a short written note, whose position bounds what the system "
      "claims to do and so is stated here: the note is generated after "
      "planning from figures the planner has already computed, contributes "
      "nothing to filtering, scoring or ranking, and may make no assertion "
      "about allergens, safety or medical suitability. It is a "
      "presentation-layer aid, not a component of the recommender. Section "
      "4.6 describes how both properties are enforced."),


# ---------------------------------------------------------------------------
]

# ---------------------------------------------------------------------------
# New references, numbered by order of first appearance in Chapter 3.
# Every entry was verified online against the publisher or issuing body
# before being written into the text.
# ---------------------------------------------------------------------------
NEW_REFERENCES = [
    (41, "Majumder, B.P., Li, S., Ni, J. and McAuley, J. 2019. Generating "
         "Personalized Recipes from Historical User Preferences. In: "
         "Proceedings of the 2019 Conference on Empirical Methods in Natural "
         "Language Processing and the 9th International Joint Conference on "
         "Natural Language Processing (EMNLP-IJCNLP). Hong Kong: Association "
         "for Computational Linguistics, pp.5976-5982."),
    (42, "US Food and Drug Administration. Nutrition labeling of food. Code "
         "of Federal Regulations, Title 21, Part 101, Section 101.9. "
         "Washington, DC: Office of the Federal Register."),
    (43, "European Parliament and Council of the European Union. 2011. "
         "Regulation (EU) No 1169/2011 on the provision of food information "
         "to consumers, Annex II. Official Journal of the European Union, "
         "L304, pp.18-63."),
    (44, "Mifflin, M.D., St Jeor, S.T., Hill, L.A., Scott, B.J., Daugherty, "
         "S.A. and Koh, Y.O. 1990. A new predictive equation for resting "
         "energy expenditure in healthy individuals. The American Journal of "
         "Clinical Nutrition, 51(2), pp.241-247."),
    (45, "Scientific Advisory Committee on Nutrition. 2011. Dietary "
         "Reference Values for Energy. London: The Stationery Office."),
    (46, "Public Health England. 2016. Government Dietary Recommendations: "
         "Government recommendations for energy and nutrients for males and "
         "females aged 1-18 years and 19+ years. London: Public Health "
         "England."),
    (47, "Salton, G. and Buckley, C. 1988. Term-weighting approaches in "
         "automatic text retrieval. Information Processing & Management, "
         "24(5), pp.513-523."),
    (48, "Koren, Y., Bell, R. and Volinsky, C. 2009. Matrix factorization "
         "techniques for recommender systems. Computer, 42(8), pp.30-37."),
    (49, "Burke, R. 2002. Hybrid recommender systems: survey and "
         "experiments. User Modeling and User-Adapted Interaction, 12(4), "
         "pp.331-370."),
    (50, "Ziegler, C.-N., McNee, S.M., Konstan, J.A. and Lausen, G. 2005. "
         "Improving recommendation lists through topic diversification. In: "
         "Proceedings of the 14th International Conference on World Wide Web "
         "(WWW '05). New York: ACM, pp.22-32."),
]

# ---------------------------------------------------------------------------
# Chapter 2 corrections (see the plan, Step 6a).
# The two tables were numbered in the wrong order, and neither they nor
# Figure 2.1 were referred to anywhere in the body text.
# ---------------------------------------------------------------------------
CH2_CAPTION_FIXES = [
    ("Table 2.2  Summary of representative prior recipe-recommendation "
     "systems reviewed, grouped by method family.",
     "Table 2.1  Summary of representative prior recipe-recommendation "
     "systems reviewed, grouped by method family."),
    ("Table 2.1  Comparison of the main recipe-recommendation method "
     "families and their role in this project.",
     "Table 2.2  Comparison of the main recipe-recommendation method "
     "families and their role in this project."),
]

# (unique text fragment to locate the paragraph, sentence to append)
CH2_CROSSREF_FIXES = [
    # The supervisor struck "and marks those combined in this project" on
    # 20 August 2026: the caption of Figure 2.1 already says it.
    ("Recipe recommendation has matured from a sub-task",
     " Figure 2.1 sets out the resulting taxonomy of approaches."),
    ("Two features distinguish recipe recommendation from canonical product",
     " Representative systems from each method family are summarised in "
     "Table 2.1."),
    ("Evaluation of recipe recommenders typically combines three orthogonal",
     " Table 2.2 compares the method families discussed in this section and "
     "states the role each plays in the present work."),
]

# Chapter 1 wording: the objective still promised USDA FoodData Central,
# which design decision DD-2 replaced with the corpus's own nutrition field.
CH1_USDA_FIXES = [
    ("USDA FoodData Central", "the corpus's own per-serving nutrition fields"),
]
