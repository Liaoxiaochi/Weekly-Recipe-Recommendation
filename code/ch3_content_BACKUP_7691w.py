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
("h1", "Chapter 3 System Design"),

("p", "This chapter sets out the design of the system. It describes what the "
      "system has to produce, how it is put together, and how each part of "
      "it works. The sections that follow take the design in the order the "
      "system itself runs, from the data it starts with through to what the "
      "user finally sees."),

# ---------------------------------------------------------------------------
("h2", "3.1  Design Overview"),

("p", "The system takes a user profile describing preferences, dietary "
      "restrictions and body data, and returns a seven-day menu of "
      "twenty-one meals. That menu must respect every declared restriction, "
      "move the user towards their daily nutritional targets, distinguish "
      "weekdays from weekends, and remain adjustable once presented. The "
      "objectives in Section 1.2 set these obligations; the sections below "
      "state how each is met."),

("p", "Three principles govern the design. Safety takes precedence over "
      "preference: an allergen, religious or clinical constraint removes a "
      "recipe entirely, and no preference score can reinstate it. The system "
      "must be interpretable, so the scoring function is a weighted sum of "
      "named terms rather than a single opaque prediction. And the prototype "
      "must run unaided on a standard laptop, which rules out the graph and "
      "multimodal methods reviewed in Section 2.2.3 and favours models whose "
      "expensive components can be computed once, offline, and reused."),

("p", "These principles produce the four-layer architecture shown in "
      "Figure 3.1. The data layer holds the cleaned corpus, the derived "
      "nutrition and allergen attributes, and the interaction matrix. The "
      "model layer holds the two recommenders, the switching controller and "
      "the user model. The application layer holds the weekly planner and the "
      "constraint engine, which cooperate: the planner requests candidates "
      "for a slot and the constraint engine decides which are admissible and "
      "how they should be penalised. The presentation layer is a single-page "
      "Streamlit application. Each layer depends only on the layer beneath "
      "it, so the recommenders can be replaced during evaluation without "
      "disturbing the planner or the interface."),

("image", "fig31_architecture.png", 6.1),
("figurecaption", "Figure 3.1  Layered architecture of the proposed system."),

# ---------------------------------------------------------------------------
("h2", "3.2  Data Pipeline Design"),

("p", "The recommendation engine cannot be designed independently of the "
      "corpus it ranks. This section specifies the pipeline that turns the "
      "raw Food.com export into a corpus with per-serving nutrition in "
      "grams, ingredient-level allergen tags and a meal slot for every "
      "recipe. Figure 3.3 shows the six stages and the quantities that "
      "survive each of them."),

("h3", "3.2.1  Source corpus"),

("p", "The system is built on the Food.com dataset released by Majumder et "
      "al. [28], which collects recipes and user interactions spanning "
      "eighteen years of the site. The two raw files used here are "
      "RAW_recipes.csv, containing 231,637 recipes, and "
      "RAW_interactions.csv, containing 1,132,367 ratings from 226,570 "
      "users. The figures of roughly 180,000 recipes and 700,000 "
      "interactions usually quoted for this dataset refer to the filtered "
      "subset the original authors prepared for their generation "
      "experiments; the present work starts from the unfiltered files and "
      "applies its own cleaning rules, so the corpus sizes reported here are "
      "not directly comparable with those in [28]."),

("p", "Each recipe record carries a name, a preparation time in minutes, an "
      "ingredient list, user-contributed free-text tags, preparation steps "
      "and a seven-element nutrition tuple; each interaction record is a "
      "user, a recipe, a date and an integer rating. The pipeline retains "
      "all of these and derives four further attributes from them: "
      "normalised ingredient identifiers, per-serving nutrition in grams, a "
      "set of allergen labels, and a meal slot. Two things the corpus does "
      "not carry shape the interface design in Section 3.7.2. The first is "
      "any image of the finished dish. The second is any quantity: an "
      "ingredient list is a list of names, so a record states that a recipe "
      "uses honey and butter but not how much of either, and no quantity "
      "information exists elsewhere in the release either. A recipe in this "
      "corpus can therefore be screened, scored and scheduled, which is what "
      "this system does with it, but it cannot be cooked from. The interface "
      "links each dish to its page on the source site, which supplies the "
      "quantities and is also the attribution the dataset's terms deserve. "
      "Using the nutrition values already "
      "present in the corpus, rather than joining to an external "
      "food-composition database, is a recorded design decision: the "
      "per-serving values are complete for every recipe, and "
      "ingredient-level matching to an external source would consume effort "
      "better spent on the recommendation and evaluation objectives."),

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
      "are expressed as percentages of a daily value, the reference "
      "quantities used on United States nutrition labels [29]. This is how "
      "the figures are presented on the site itself, as Figure 3.2 shows. A "
      "percentage cannot be aggregated across a day's meals or compared "
      "against a personalised target, so the six percentage fields are "
      "converted to mass using the reference values in Table 3.1."),

("image", "fig32_foodcom_nutrition.png", 2.9),
("figurecaption", "Figure 3.2  Nutrition panel published for recipe 61040, "
                  "20 Minute Chicken Parmesan, which is a member of the "
                  "corpus used here. Every nutrient except energy is "
                  "reported as a percentage of a daily value alongside its "
                  "mass, and it is the percentage that the dataset records. "
                  "Source: food.com, accessed 14 August 2026."),

("tablecaption", "Table 3.1  Conversion of the nutrition tuple to absolute "
                 "quantities per serving."),
("table", [
    ["Element", "Encoding in the corpus", "Reference value [29]", "Conversion"],
    ["Energy", "kcal per serving", "not applicable", "used unchanged"],
    ["Total fat", "per cent of daily value", "65 g", "g = pdv / 100 x 65"],
    ["Sugar", "per cent of daily value", "25 g", "g = pdv / 100 x 25"],
    ["Sodium", "per cent of daily value", "2,400 mg", "mg = pdv / 100 x 2400"],
    ["Protein", "per cent of daily value", "50 g", "g = pdv / 100 x 50"],
    ["Saturated fat", "per cent of daily value", "20 g", "g = pdv / 100 x 20"],
    ["Carbohydrate", "per cent of daily value", "300 g", "g = pdv / 100 x 300"],
]),

("p", "Five of the six reference values in Table 3.1 are those in force "
      "before the 2016 revision of the United States labelling rules, "
      "consistent with the period over which the corpus was collected. They "
      "were confirmed directly rather than assumed: the recipe shown in "
      "Figure 3.2 is itself a member of the corpus, and dividing each "
      "published mass by its published percentage recovers 65.8 g of fat, "
      "20.6 g of saturated fat, 2,448 mg of sodium, 50.8 g of protein and "
      "311.7 g of carbohydrate, matching the table to within rounding. The "
      "sixth value is a different case. The pre-2016 label carried no "
      "reference quantity for sugars at all, so the site must apply one of "
      "its own; the same division gives 25 g. That figure was then checked "
      "across the whole corpus using the fact that sugars are a component of "
      "total carbohydrate and so cannot exceed it in mass. At 25 g the "
      "constraint is violated by 6.1 per cent of recipes and never by more "
      "than 6 g, which is the scale of the rounding in the source data; at "
      "50 g it is violated by 40.1 per cent of recipes and by as much as "
      "479 g, which is not credible. The 25 g value is therefore adopted."),

("p", "The conversion as a whole was verified a second way, independently of "
      "any single page. If it is correct, then reconstructing energy from "
      "the converted macronutrients using the Atwater factors of 4 kcal per "
      "gram of protein and carbohydrate and 9 kcal per gram of fat should "
      "reproduce the energy field. Across the 225,512 recipes with a usable "
      "energy value the reconstruction has a median absolute relative error "
      "of 2.86 per cent, with 71.1 per cent of recipes within 5 per cent. "
      "The post-2016 values agree markedly less well, a carbohydrate "
      "reference of 275 g raising the median error to 5.34 per cent and a "
      "fat reference of 78 g to 7.29 per cent. The residual disagreement is "
      "attributed to rounding in the source data and to energy from "
      "components outside the three macronutrients."),

("h3", "3.2.4  Allergen and dietary tagging"),

("p", "Allergen tagging is the part of the pipeline where a mistake can do "
      "real harm, and it is also the part that the source data supports "
      "least well. The corpus records ingredient names, not brands or "
      "sub-ingredients, so an allergen that is present only inside a "
      "composite product is invisible to any method that matches the "
      "allergen's own name. Worcestershire sauce contains anchovy, pesto "
      "contains pine nuts and hard cheese, and most soy sauce contains "
      "wheat, yet none of those ingredient strings contains the words fish, "
      "nut or wheat."),

("p", "The design responds with a lexicon organised in three layers, applied "
      "over the fourteen classes that European food information law requires "
      "to be declared [30]. The first layer matches the allergen itself. The "
      "second matches synonyms and derivatives sharing no substring with the "
      "class name, such as groundnut for peanut, casein and whey for milk, "
      "semolina and spelt for gluten, and tahini for sesame. The third "
      "matches named foods that reliably contain the allergen without naming "
      "it. Matching runs against the ingredient strings as the corpus records "
      "them, not against a normalised form of them, because the third layer "
      "depends on complete multi-word phrases: the ingredient map distributed "
      "with the corpus resolves worcestershire sauce and similar entries to a "
      "short canonical head word, which is exactly the information a "
      "composite rule needs. That map is used elsewhere in the pipeline, "
      "where it resolves 99.81 per cent of ingredient occurrences to a "
      "canonical form: it supplies the vocabulary of the content-based "
      "representation in Section 3.4.1, and the residue it cannot resolve "
      "defines the fail-closed exclusion of Section 3.5.1."),

("p", "Table 3.2 reports how many recipes each class flags and how the flags "
      "distribute across the layers. The third layer is not a refinement but "
      "the substance of the method: of the 121,830 recipes flagged for "
      "gluten, 102,939 are flagged only by a composite rule, as are 37,995 "
      "of the 40,724 soya flags and every one of the 41,737 sulphite flags. "
      "A lexicon restricted to direct and derived terms would miss those "
      "recipes entirely. Lupin does not occur in this corpus at all, which "
      "is unsurprising in a predominantly North American collection; the "
      "class is retained so that the rule set matches the legal list."),

("p", "A fourth element of the design counteracts the cost of substring "
      "matching. Several phrases contain an allergen term while containing "
      "no allergen: coconut milk and soy milk are not dairy, butter beans "
      "and butternut squash are not butter, and an aubergine is not an egg. "
      "A list of such exempt phrases is blanked out of the ingredient text "
      "before matching, so they cannot fire a rule. A phrase qualifies only "
      "if it never carries the allergen; one that merely usually lacks it is "
      "excluded from the list, because the fail-closed policy prefers an "
      "unnecessary exclusion to a missed allergen. The counts in Table 3.2 "
      "are those of the revised lexicon, which was extended and corrected "
      "after the measurement reported in Chapter 5."),

("tablecaption", "Table 3.2  Allergen classes of Annex II to Regulation (EU) "
                 "No 1169/2011 [30], with a representative composite rule "
                 "and the number of recipes flagged in the raw corpus of "
                 "231,637."),
("table", [
    ["Class", "Representative composite rule", "Recipes flagged",
     "Flagged only by a composite rule"],
    ["Cereals containing gluten", "bread, pasta, soy sauce, beer", "121,830", "102,939"],
    ["Milk", "parmesan, chocolate, pesto, ranch dressing", "144,197", "55,772"],
    ["Eggs", "mayonnaise, hollandaise, custard, brioche", "74,751", "19,043"],
    ["Soybeans", "soy sauce, teriyaki, margarine, lecithin", "40,724", "37,995"],
    ["Sulphur dioxide and sulphites", "wine, vinegar, dried fruit", "41,737", "41,737"],
    ["Celery", "stock cube, bouillon, mirepoix", "35,151", "22,442"],
    ["Mustard", "salad dressing, barbecue sauce, curry powder", "31,829", "18,931"],
    ["Tree nuts", "pesto, baklava, granola, marzipan", "31,647", "1,322"],
    ["Fish", "Worcestershire sauce, Caesar dressing, tapenade", "17,911", "10,073"],
    ["Sesame seeds", "hummus, halva, za'atar", "15,278", "1,239"],
    ["Peanuts", "satay sauce, kung pao", "7,530", "25"],
    ["Crustaceans", "seafood mix, shrimp paste, surimi", "6,938", "296"],
    ["Molluscs", "oyster sauce, seafood mix", "2,861", "1,083"],
    ["Lupin", "none observed", "0", "0"],
]),

("p", "Two limits of the method shape the interface design in Section 3.7.2 "
      "and the evaluation in Chapter 5, and are stated plainly here. First, "
      "the composite layer is deliberately over-inclusive: a rule flagging "
      "any flour as a source of gluten also flags almond flour, and one "
      "flagging vinegar as a source of sulphites flags varieties containing "
      "none. This costs precision, and it is the intended direction of "
      "error, since excluding an acceptable recipe deprives the user of one "
      "option among many whereas admitting an unacceptable one may cause "
      "harm. Second, some ingredient strings are undecidable from the data: "
      "an entry reading one package of cake mix cannot be resolved by any "
      "lexicon, because the information is not present. That is a limitation "
      "of the source data rather than a failure of the rules, and Section "
      "3.5.1 specifies how such recipes are treated. The rate at which the "
      "tagging misses allergens that are genuinely present is measured "
      "against a manually labelled sample in Chapter 5; it is not assumed to "
      "be zero, and the system is not presented to the user as though it "
      "were."),

("p", "The corpus also carries user-contributed tags asserting the absence "
      "of an allergen, such as gluten-free and dairy-free. These are used "
      "only as corroboration and never as evidence of safety, because they "
      "are unverified: 1,077 recipes tagged gluten-free and 926 tagged "
      "dairy-free contain an ingredient the lexicon flags. Where tag and "
      "rule disagree, the rule prevails and the recipe is excluded. Tags are "
      "used positively only for dietary preferences carrying no safety "
      "consequence, such as identifying the 35,651 vegetarian and 10,012 "
      "vegan recipes."),

("image", "fig33_data_pipeline.png", 5.6),
("figurecaption", "Figure 3.3  The data preparation pipeline, with the "
                  "quantity of data surviving each stage. Counts are "
                  "produced by the profiling script described in Section "
                  "4.2 and are reproducible from the raw files."),

# ---------------------------------------------------------------------------
("h2", "3.3  User Model Design"),

("h3", "3.3.1  Profile representation"),

("p", "A user profile has three parts. Restrictions are the hard part: "
      "allergen classes drawn from the fourteen in Table 3.2, an optional "
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
      "rate is computed with the Mifflin-St Jeor equation [31], which was "
      "derived on a healthy adult sample and is the predictive equation most "
      "commonly recommended for adults without a clinical condition. Total "
      "energy expenditure is then obtained by scaling basal metabolic rate "
      "by a physical activity level, following the factorial approach used "
      "to set the United Kingdom dietary reference values for energy [32]. "
      "The equations and the activity bands offered by the interface are "
      "given in Table 3.3; the four bands are a design choice, chosen to "
      "span the range of ordinary adult activity while keeping the form "
      "simple enough for a user to answer honestly."),

("tablecaption", "Table 3.3  Derivation of daily energy and macronutrient "
                 "targets from profile data."),
("table", [
    ["Quantity", "Definition", "Source"],
    ["Basal metabolic rate, men",
     "BMR = 10w + 6.25h - 5a + 5   (w in kg, h in cm, a in years)", "[31]"],
    ["Basal metabolic rate, women", "BMR = 10w + 6.25h - 5a - 161", "[31]"],
    ["Total energy expenditure", "TEE = BMR x PAL", "[32]"],
    ["Physical activity level",
     "1.4 inactive, 1.6 lightly active, 1.75 active, 1.9 very active",
     "Design choice, band structure after [32]"],
    ["Total fat", "at most 35 per cent of food energy", "[33]"],
    ["Saturated fat", "at most 11 per cent of food energy", "[33]"],
    ["Carbohydrate", "approximately 50 per cent of food energy", "[33]"],
    ["Free sugars", "at most 5 per cent of food energy", "[33]"],
    ["Protein", "0.75 g per kg of body weight per day", "[33]"],
    ["Salt", "at most 6 g per day, equivalent to 2.4 g sodium", "[33]"],
]),

("p", "Macronutrient targets are expressed as proportions of food energy "
      "following the United Kingdom government dietary recommendations [33], "
      "not the United States reference values used to decode the corpus in "
      "Section 3.2.3. The distinction is deliberate: the American values are "
      "a decoding key, needed because that is how the source data was "
      "encoded, whereas the British values define what the system steers the "
      "user towards. Protein is the exception, specified per kilogram of "
      "body weight rather than as a share of energy, and is converted to a "
      "daily mass before use."),

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
      "weighted by term frequency-inverse document frequency [34]. The "
      "inverse document frequency term is what makes the representation "
      "useful here: salt, water and butter appear in a large fraction of the "
      "corpus and carry almost no preference information, whereas a "
      "distinctive ingredient identifies a style of cooking efficiently. A "
      "user is represented in the same space by the rating-weighted mean of "
      "the recipes in their history, and candidates are ranked by cosine "
      "similarity to that vector. The weights are taken relative to the "
      "midpoint of the rating scale rather than raw, so that a rating below "
      "the midpoint moves the user vector away from that recipe. Raw weights "
      "would make every rating positive, and a recipe the user had just "
      "marked one star would still be pulled towards, which is the opposite "
      "of what the rating expresses. Two properties matter for the design: the "
      "component scores recipes that no one has ever rated, and it composes "
      "cleanly with the hard filter, since removing recipes from the "
      "candidate set does not alter the scores of those that remain."),

("h3", "3.4.2  Collaborative component"),

("p", "The collaborative recommender factorises the user-recipe rating "
      "matrix into latent factors using truncated singular value "
      "decomposition with stochastic gradient descent, in the form that has "
      "become the standard baseline for rating prediction [35]. It "
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

("h3", "3.4.3  Contextual switching policy"),

("p", "Switching is the hybrid strategy in which a single recommender is "
      "selected per request according to a criterion evaluated at that "
      "moment, rather than combining several recommenders' outputs [36]. "
      "The criterion adopted here is the size of the user's interaction "
      "history: the collaborative component is used when the user has at "
      "least N interactions and the content-based component otherwise, as "
      "shown in Figure 3.4. Both branches then pass through a context "
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

("image", "fig34_interactions.png", 5.8),
("figurecaption", "Figure 3.4  Proportion of Food.com users with at least N "
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
      "shown against the soft categories in Figure 3.5. Three of them are "
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

("p", "The user's own list of ingredients to avoid is a fifth hard rule, "
      "and one whose matching deserves a note because the obvious "
      "implementation is wrong in both directions at once. Testing whether "
      "the typed term occurs as a substring of the ingredient text is "
      "simultaneously too permissive and too strict: it removes goat's "
      "cheese from a user who excluded oats, since ‘oat’ occurs "
      "inside ‘goat’, while failing to remove oatmeal from that "
      "same user, since ‘oats’ does not occur inside "
      "‘oatmeal’. Matching is therefore anchored at a word "
      "boundary and applied to the stem of the term, so that it catches the "
      "word and its compounds but not words that merely contain it. The "
      "residual error is over-exclusion, since a stem also prefixes "
      "unrelated foods: excluding peas removes peaches. For a preference "
      "list that is the tolerable direction, because the cost of removing "
      "too much is lost variety while the cost of removing too little is a "
      "meal the user has said they do not want. It is tolerable only because "
      "it is visible: the interface names the ingredients each term matched, "
      "so an over-broad term is apparent and can be reworded. This rule "
      "governs preference exclusions alone. Declared allergens are matched "
      "by the three-layer lexicon of Section 3.2.4, which is a different and "
      "stricter mechanism, and no claim made here about preference matching "
      "extends to them."),

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
      "proportion of the "
      "recipe's ingredients already appearing in the partial plan, which "
      "suppresses repetition; and T is the amount by which preparation time "
      "exceeds the day's budget, expressed as a proportion of that budget "
      "and floored at zero so quick recipes are not rewarded without limit. "
      "The weights a to e are set initially to 1.0, 0.4, 0.3, 0.2 and 0.1, "
      "giving preference the largest single influence while allowing the "
      "nutritional terms to dominate in combination when a candidate is "
      "badly matched. These are starting values, tuned on a validation split "
      "in Chapter 5. Because the function is an additive sum of named terms, "
      "each contribution can be displayed alongside a recommendation, which "
      "is what requirement N2 asks for."),

("p", "The M term distinguishes between the two kinds of quantity Table 3.3 "
      "sets out, because the guidance does. Protein and carbohydrate are "
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

("p", "One consequence has to be stated plainly, because it constrains what "
      "the system can achieve rather than how well it is built. Only 4.1 per "
      "cent of the main-dish corpus, and 414 of the 19,919 breakfast "
      "candidates, satisfy all four guideline ceilings simultaneously when "
      "scaled to the energy they supply. Food.com is a collection of what "
      "people cook, not a nutritionally curated database, and a planner "
      "restricted to fully compliant recipes would be choosing from a "
      "twenty-fifth of the corpus, which would defeat both preference "
      "matching and variety. The ceilings are therefore soft constraints that "
      "the score genuinely minimises rather than hard filters, and Chapter 5 "
      "reports how closely the resulting plans hold to them."),

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
      "system has reason to believe they cannot safely eat. The whole "
      "arrangement is shown in Figure 3.5."),

("image", "fig35_constraints.png", 6.0),
("figurecaption", "Figure 3.5  Constraint handling in three stages. Hard "
                  "constraints filter the candidate set, soft constraints "
                  "penalise within it, and relaxation loosens only the soft "
                  "stage. The allergen filter lies outside the scope of "
                  "relaxation entirely."),

# ---------------------------------------------------------------------------
("h2", "3.6  Weekly Plan Generation"),

("h3", "3.6.1  Problem formulation"),

("p", "A weekly plan is an assignment of one recipe to each of twenty-one "
      "slots, being three meals on each of seven days. Two things must hold "
      "for a slot to be fillable: the corpus must contain recipes "
      "appropriate to that meal, and each slot must carry its own share of "
      "the daily energy target. Neither is given by the source data, so both "
      "are constructed."),

("p", "Meal appropriateness is derived from the course tags contributed by "
      "the site's users. Recipes tagged as desserts, beverages, condiments, "
      "sauces, dips, dressings, spreads or preserves are excluded as "
      "accompaniments rather than meals. Of the remainder, tags such as "
      "breakfast, brunch and oatmeal map to breakfast; lunch, sandwiches, "
      "salads and soups to lunch; and main-dish, meat, poultry, seafood and "
      "casseroles to dinner. This resolves 56.75 per cent of the raw corpus "
      "to at least one slot, leaving the planner 19,919 breakfast, 40,779 "
      "lunch and 103,389 dinner recipes after the other cleaning rules. "
      "Breakfast is much the thinnest, but 19,919 candidates is ample for a "
      "seven-day plan; the imbalance is reported because it constrains how "
      "much variety the planner can offer at breakfast relative to dinner. "
      "Recipes with no usable course tag are removed as main dishes by the "
      "last cleaning rule of Section 3.2.2, the largest single reduction in "
      "the pipeline. Not all of them leave the system: 13,341 of the 94,256 "
      "removed carry a tag marking them as something served beside a meal "
      "rather than as one, such as a vegetable dish, a potato dish or a salad "
      "of pulses, and these form the accompaniment pool the next section "
      "draws on. The pool is defined to be disjoint from the main corpus, so "
      "no dish can be served as its own accompaniment and none of the corpus "
      "figures above is altered by admitting it."),

("p", "The daily energy target is divided between the three slots in the "
      "proportions 25, 35 and 40 per cent for breakfast, lunch and dinner. "
      "This split is a design choice rather than a derived quantity, "
      "intended to place the largest meal in the evening in line with common "
      "practice in the United Kingdom; it is exposed as a parameter so that "
      "the effect of alternative splits can be examined."),

("p", "A slot is therefore an energy quantity as well as a category, and the "
      "corpus does not supply single recipes at that scale. The median dinner "
      "candidate provides 381 kcal per serving where the dinner slot of a "
      "2,440 kcal day asks for 976, and only 5.5 per cent of dinner "
      "candidates reach that figure in a single serving. A slot filled by one "
      "dish would leave every day far short of its target whichever dishes "
      "were chosen, which would defeat the nutritional objective outright."),

("p", "A slot is consequently filled by a main dish together with the "
      "accompaniments needed to reach its target, at most two of them, drawn "
      "from the pool identified in Section 3.2.2. This is how the shortfall is "
      "made up at a table, and the alternative of serving the main dish "
      "several times over was rejected on both grounds that matter here. It "
      "is not what a person does: told to eat three portions of one dish, a "
      "user simply would not. And it is measurably worse. Against a 976 kcal "
      "dinner target, one serving of a main dish with up to two "
      "accompaniments brings 95.9 per cent of dinner candidates within ten "
      "per cent of the target, where repeated servings of the main dish alone "
      "reached 49.8 per cent. The same measurement showed that allowing more "
      "than one serving of the main added nothing once accompaniments were "
      "available, so the serving count is capped at one and a half: a larger "
      "helping, not a second dinner."),

("p", "The main dish is ranked against a fixed share of the slot target rather "
      "than against the whole of it, the remainder being left for the "
      "accompaniments to supply; a share of 0.55 is adopted, chosen by "
      "measurement over the same profiles. An accompaniment is admitted only "
      "if it brings the plate closer to the target and only if it is "
      "substantial enough to be worth cooking, so a slot whose main dish "
      "already meets its target is served alone. Every constraint of Section "
      "3.5 applies to an accompaniment exactly as it does to a main dish: an "
      "allergen on a side dish is as dangerous as one on a main. Ceilings "
      "arising from a clinical restriction are applied to the whole plate, "
      "since it is the plate the user eats, and where such a ceiling conflicts "
      "with the energy target the plate is left short rather than taken over "
      "the limit, the hard constraint prevailing over the soft one."),

("h3", "3.6.2  Plan construction"),

("p", "Slots are filled greedily in day order, but a purely greedy rule has "
      "a defect that matters here: choosing the highest-scoring breakfast "
      "may consume so much of the day's energy allowance that no acceptable "
      "lunch or dinner remains. A look-ahead term corrects this by "
      "estimating, for each candidate, whether the slots remaining in that "
      "day can still be filled within the residual energy budget, and "
      "penalising candidates that would leave the remainder infeasible. "
      "Algorithm 3.1 states the procedure."),

("algo", "Algorithm 3.1  Weekly plan construction", [
    "Input:  profile u, cleaned corpus R, accompaniment pool A, daily targets T",
    "Output: plan P over 21 slots, plus any unfilled slots",
    "",
    " 1  P <- empty plan",
    " 2  for each day d in Monday .. Sunday do",
    " 3      for each slot s in (breakfast, lunch, dinner) do",
    " 4          C <- { r in R : mealslot(r) = s }",
    " 5          C <- HardFilter(C, u, P)       // allergens never relaxed",
    " 6          if C is empty then",
    " 7              record (d, s) as unfilled; continue",
    " 8          for each r in C do",
    " 9              base(r) <- Relevance(r, u) - SoftPenalty(r, s, d, P, wT)",
    "10          K <- the k highest-scoring recipes in C by base",
    "11          r* <- argmax over r in K of ( base(r) + LookAhead(r, d, s, P, T) )",
    "12          S <- ChooseSides(r*, A, u, s, d, P, T)   // at most two",
    "13          P <- P + (d, s, r*, S)",
    "14  if P has unfilled slots then",
    "15      P <- AdaptiveRelax(P, u, R, A, T)  // soft constraints only",
    "16  return P and the list of slots still unfilled",
]),

("p", "Line 9 scores the main dish against w.T, its share of the slot target, "
      "rather than against T itself, since line 12 supplies the remainder. "
      "ChooseSides adds accompaniments one at a time, each selected against the "
      "energy still outstanding, and stops as soon as the plate is close enough "
      "to the target or no admissible accompaniment would improve it. The hard "
      "filter at line 5 is applied within ChooseSides as well; it is written "
      "once here for brevity but is not skipped there."),

("p", "Restricting the look-ahead to the k highest-scoring candidates keeps "
      "the cost of each slot linear in the size of the filtered candidate "
      "set, since the expensive feasibility estimate is evaluated only k "
      "times. The procedure is deterministic given a profile, which matters "
      "for the evaluation in Chapter 5."),

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

("p", "A plan satisfying every constraint can still be unusable if it "
      "repeats the same few recipes, and an accuracy-optimal ranker tends to "
      "produce exactly that, since the recipes closest to a user's profile "
      "resemble one another. The repetition term D of Section 3.5.2 "
      "penalises ingredient overlap with the partial plan, a within-list "
      "application of the topic diversification idea introduced by Ziegler "
      "et al. [37]. The same measure, intra-list dissimilarity over "
      "ingredient sets, is reported as an evaluation metric in Chapter 5, so "
      "that the cost of diversity in accuracy terms is quantified rather "
      "than assumed."),

("p", "How often a dish may reappear is a second question, and one where an "
      "earlier version of this design was wrong. That version barred a recipe "
      "outright once it had been placed, on the stated grounds that no user "
      "would regard the same dish twice in a week as a recommendation. Shown a "
      "working prototype, a user contradicted it directly: a dish they like, "
      "which is quick to prepare and fits their targets, is welcome more than "
      "once in a week provided what is served beside it changes. The premise "
      "was an assumption about users that had never been put to one, and it "
      "did not survive contact."),

("p", "Repetition is therefore bounded rather than forbidden. A main dish may "
      "appear up to a stated number of times across the seven days, two by "
      "default, and the bound is exposed to the user because how much variety "
      "a week should carry is a preference and not a property of the corpus. "
      "Accompaniments never repeat, so a main dish that comes round twice "
      "arrives in different company each time, which is the arrangement the "
      "user described. Exposing the bound has a second use: it is the "
      "parameter along which the accuracy cost of diversity is measured in "
      "Chapter 5, so the trade-off this section describes is instrumented by "
      "the same control the user operates."),

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

("p", "The interface is a single page, sketched in Figure 3.6. A sidebar "
      "collects the profile: body data and activity level, the two "
      "preparation-time budgets, and the restriction controls. The main pane "
      "presents the week twice, at two scales. A compact strip shows seven "
      "days across, giving the shape of the week and the contextual "
      "difference between weekdays and weekends at a glance; below it the "
      "same week is laid out a day at a time, three meals across, at a width "
      "that accommodates the full ingredient list the screening policy "
      "requires to be open. The two scales exist because one layout cannot "
      "serve both purposes: seven columns is the right shape for seeing a "
      "week and the wrong shape for working on a meal."),

("p", "A card is the unit the user acts on. Each carries the day and meal "
      "slot, the name of the main dish, the accompaniments served beside it "
      "with their energy, the total for the plate, the preparation time, and "
      "any allergen class flagged anywhere on the plate rather than on the "
      "main dish alone; expanding a card reveals the complete ingredient list "
      "of every dish, grouped by dish because they are cooked separately, and "
      "a single control replaces the recipe under the rules of Section 3.6.3. What a card cannot show is a "
      "photograph of the dish, because the corpus contains no images. This "
      "is a real limitation for an interface whose subject is food, and it "
      "is the reason the card leads with the recipe name and the two figures "
      "a user is most likely to judge a meal by rather than with a visual "
      "element it cannot fill. Beneath the grid the interface sets each day's "
      "energy and macronutrient totals against the targets derived in Section "
      "3.3.2, so that the nutritional attainment measured in Chapter 5 is "
      "visible to the user rather than confined to the evaluation."),

("p", "Two features of the interface follow directly from the limits "
      "established in Section 3.2.4. The ingredient list of a selected "
      "recipe is shown in full and expanded by default, rather than hidden "
      "behind a control, so that a user with an allergy can perform their "
      "own check without additional interaction. A persistent notice reads "
      "that the screening is automated and is not a safety guarantee, and "
      "that the full ingredient list should always be checked. The wording "
      "describes what the system actually does: it screens, and screening "
      "has a false-negative rate that Chapter 5 quantifies. Presenting the "
      "output as a safety guarantee would misrepresent the method and "
      "encourage exactly the unwarranted reliance the fail-closed filter "
      "exists to make unnecessary. The position is consistent with the "
      "ethical stance of Section 1.4, that the system offers suggestions "
      "and not clinical advice."),

("p", "A third feature follows from the same commitment, and is less "
      "obvious than the other two. A plan is built when the user asks for "
      "one, not on every keystroke, so a restriction edited in the sidebar "
      "does not by itself change what is on screen. For a preference this is "
      "merely stale; for a restriction it is unsafe, because the user has "
      "just declared an exclusion and the system appears to have accepted it "
      "while continuing to display meals chosen before it. The interface "
      "therefore compares the sidebar against the profile the displayed plan "
      "was built from, and when any of the allergen, dietary-regime, "
      "clinical or excluded-ingredient fields differ it states that the plan "
      "predates the change and disables every action on every card until the "
      "week is rebuilt. The plan is not silently regenerated instead, which "
      "would discard the user's pinned meals and ratings without asking; it "
      "is frozen and labelled. A screening rule that is correct but applied "
      "to a plan the user is no longer looking at provides no protection, "
      "and this is the case in which that gap arises."),

("p", "Selecting a dish opens a detail view, which is the finest unit the "
      "interface presents. It carries the recipe's own description and "
      "method, its full ingredient list, what the dish supplies against what "
      "the slot allows, its share of the day's energy and protein, how many "
      "times it recurs in the week, the accompaniments served with it, and "
      "the named score terms that placed it there. It also carries a short "
      "written note. Two properties of that note are stated here because "
      "they bound what the system claims to do. It is generated after "
      "planning, from figures the planner has already computed, and "
      "contributes nothing to filtering, scoring or ranking: it is a "
      "presentation-layer aid and not a component of the recommender. And it "
      "may make no assertion about allergens, safety or medical "
      "suitability, a rule enforced both in the instruction given to the "
      "language model and by a filter applied to its output, with an "
      "arithmetically derived note shown whenever the model is unavailable "
      "or its response is rejected. A generated sentence claiming a dish was "
      "safe would contradict the standing notice in the one place a user is "
      "most likely to believe it, so the constraint is enforced twice and "
      "the degraded path is the ordinary one rather than an error state."),

("image", "fig36_cards.png", 6.1),
("figurecaption", "Figure 3.6  The weekly plan presented as replaceable "
                  "cards, with one card enlarged to show what it carries."),

("h3", "3.7.3  Technology choices"),

("p", "The prototype is written in Python 3.11 with pandas and NumPy for "
      "data preparation, scikit-learn for the term-weighting and "
      "decomposition components, and Streamlit for the interface. Streamlit "
      "is chosen over a conventional web framework because it renders forms "
      "and tabular output from ordinary Python with no separate front-end "
      "codebase, which suits a prototype whose purpose is to support "
      "evaluation rather than deployment. The two computationally expensive "
      "artefacts, the term-document matrix and the latent factor matrices, "
      "are computed once offline and loaded at start-up, so that a request "
      "costs only a filter over the candidate set and a scoring pass. This "
      "keeps the system within requirements N3 and N4 without specialised "
      "hardware."),

# ---------------------------------------------------------------------------
("h2", "3.8  Summary"),

("p", "This chapter has specified a system in four layers: a pipeline "
      "reducing 231,637 raw recipes to a corpus of 128,403 with per-serving "
      "nutrition in grams, allergen tags over the fourteen classes of "
      "European food law and a meal slot for every recipe; a user model "
      "converting body data into daily and per-slot targets; a switching "
      "hybrid selecting between a content-based and a collaborative "
      "recommender on the size of the user's history; a constraint module "
      "filtering on hard restrictions and penalising on soft ones; and a "
      "planner filling twenty-one slots greedily with look-ahead and "
      "presenting them as cards the user can replace one at a time. Two "
      "decisions run through the whole design. The first is that the corpus "
      "determines what the recommender can do: a rating matrix 99.998 per "
      "cent empty, with a median of one rating per user, is why the system "
      "is content-based for most users and why a switching hybrid was chosen "
      "at all. The second is that allergen screening errs towards exclusion, "
      "never relaxes, and is not presented as a safety guarantee, because "
      "rule-based tagging of user-generated ingredient text has a "
      "false-negative rate that cannot be driven to zero."),
]

# ---------------------------------------------------------------------------
# New references, numbered by order of first appearance in Chapter 3.
# Every entry was verified online against the publisher or issuing body
# before being written into the text.
# ---------------------------------------------------------------------------
NEW_REFERENCES = [
    (28, "Majumder, B.P., Li, S., Ni, J. and McAuley, J. 2019. Generating "
         "Personalized Recipes from Historical User Preferences. In: "
         "Proceedings of the 2019 Conference on Empirical Methods in Natural "
         "Language Processing and the 9th International Joint Conference on "
         "Natural Language Processing (EMNLP-IJCNLP). Hong Kong: Association "
         "for Computational Linguistics, pp.5976-5982."),
    (29, "US Food and Drug Administration. Nutrition labeling of food. Code "
         "of Federal Regulations, Title 21, Part 101, Section 101.9. "
         "Washington, DC: Office of the Federal Register."),
    (30, "European Parliament and Council of the European Union. 2011. "
         "Regulation (EU) No 1169/2011 on the provision of food information "
         "to consumers, Annex II. Official Journal of the European Union, "
         "L304, pp.18-63."),
    (31, "Mifflin, M.D., St Jeor, S.T., Hill, L.A., Scott, B.J., Daugherty, "
         "S.A. and Koh, Y.O. 1990. A new predictive equation for resting "
         "energy expenditure in healthy individuals. The American Journal of "
         "Clinical Nutrition, 51(2), pp.241-247."),
    (32, "Scientific Advisory Committee on Nutrition. 2011. Dietary "
         "Reference Values for Energy. London: The Stationery Office."),
    (33, "Public Health England. 2016. Government Dietary Recommendations: "
         "Government recommendations for energy and nutrients for males and "
         "females aged 1-18 years and 19+ years. London: Public Health "
         "England."),
    (34, "Salton, G. and Buckley, C. 1988. Term-weighting approaches in "
         "automatic text retrieval. Information Processing & Management, "
         "24(5), pp.513-523."),
    (35, "Koren, Y., Bell, R. and Volinsky, C. 2009. Matrix factorization "
         "techniques for recommender systems. Computer, 42(8), pp.30-37."),
    (36, "Burke, R. 2002. Hybrid recommender systems: survey and "
         "experiments. User Modeling and User-Adapted Interaction, 12(4), "
         "pp.331-370."),
    (37, "Ziegler, C.-N., McNee, S.M., Konstan, J.A. and Lausen, G. 2005. "
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
    ("Recipe recommendation has matured from a sub-task",
     " Figure 2.1 sets out the resulting taxonomy of approaches and marks "
     "those combined in this project."),
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
