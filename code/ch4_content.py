"""Chapter 4 text, tables and figure placement.

Same block vocabulary as ch3_content.py, so build_docx.py emits both with one
code path:

    ("h1"|"h2"|"h3", text)      headings
    ("p", text)                 body paragraph
    ("tablecaption", text)      caption, placed ABOVE its table
    ("table", [[...], ...])     first row is the header row
    ("image", filename, width)  width in inches; filename may name a
                                subdirectory of figures/
    ("figurecaption", text)     caption, placed BELOW its image

WHAT THIS CHAPTER IS FOR, and why it does not walk through the code.

Chapter 3 states the design: the algorithms, the scoring function, the
constraint policy.  Repeating that here in the form of class and function
descriptions would fill the chapter without adding to it.  What Chapter 3
cannot contain is what happened when the design was built -- which assumptions
the corpus refused to support, which defects the tests caught, which they
missed, and what the numbers turned out to be.  That is the material of this
chapter, and it is the material the project actually generated: forty recorded
design decisions across eight iterations, most of them prompted by working with
a running prototype rather than by reasoning about a specification.

British English throughout.  No new citations are introduced: this chapter
reports the author's own implementation, and the external references it needs
are already established in Chapters 2 and 3.
"""

BLOCKS = [

# ===========================================================================
("h1", "Chapter 4 Implementation"),

# ---------------------------------------------------------------------------
("h2", "4.1  Development environment"),

("p", "The system is written in Python 3.11 and runs on a single laptop with "
      "no specialised hardware, using pandas and NumPy for data "
      "preparation, scikit-learn for term weighting and vectorisation, and "
      "Streamlit for the interface. Two libraries a recommender project "
      "would ordinarily reach for, Surprise and implicit, were rejected: "
      "both need a C toolchain at installation time, which on Windows risks "
      "losing a day to an environment failure rather than to the project, "
      "and since Section 3.4.2 specifies a truncated factorisation trained "
      "by stochastic gradient descent, which is roughly sixty lines of "
      "NumPy, the dependency bought nothing. The only package needing installation "
      "beyond a standard scientific distribution is Streamlit itself."),

("p", "The two expensive artefacts, the term-document matrix and the latent "
      "factor matrices, are computed once offline and stored on disk. The "
      "interface loads them at start-up, so serving a request costs a filter "
      "over the candidate set and a scoring pass rather than any "
      "retraining. Recipe methods and descriptions are stored separately: "
      "the planner never reads them, and carrying eighty-five megabytes of "
      "prose through every scoring pass would cost load time for nothing. "
      "The interface reads that file only when a user opens a recipe."),

("p", "The source is kept in a Git repository laid out along the module "
      "decomposition of Section 3.7.1: the five modules in a source "
      "package, the interface and the supporting scripts above it, and the "
      "precomputed artefacts in a directory of their own. What is excluded "
      "from that repository matters as much as what is tracked, and the "
      "exclusions are a control rather than housekeeping. The recipe "
      "corpus and every "
      "artefact derived from it are excluded, because the dataset grants "
      "no redistribution licence, as Appendix A sets out; the credentials "
      "file for the external service of Section 4.6 is excluded for the "
      "obvious reason. The submitted archive is therefore built by a "
      "script rather than by compressing the working directory, and that "
      "script refuses to write an archive containing either. Each change "
      "is checked by the suites of Section 4.7 before it is kept."),

# ---------------------------------------------------------------------------
("h2", "4.2  Data pipeline"),

("p", "The pipeline implements the six stages of Section 3.2 and reconciles "
      "its own output against the figures that chapter quotes. It reproduces "
      "128,403 retained recipes, 655,954 interactions, and 19,919 breakfast, "
      "40,779 lunch and 103,389 dinner candidates, and exits with an error if "
      "any of them disagrees. Treating those numbers as a contract rather "
      "than as a report was worth the small effort it cost: they are quoted "
      "in a chapter written before the code existed, and a silent divergence "
      "between the two would not have been noticed by reading either."),

("p", "The conversion from percentages to masses was checked independently of "
      "the published panel used to establish the reference values. If it is "
      "correct, reconstructing energy from the converted macronutrients by "
      "the Atwater factors of 4 kcal per gram of protein and carbohydrate "
      "and 9 for fat should reproduce the recorded energy. Across the 225,512 "
      "recipes with a usable energy value the reconstruction has a median "
      "absolute relative error of 2.86 per cent, with 71.1 per cent within 5 "
      "per cent. The values introduced by the 2016 revision agree markedly "
      "less well: a carbohydrate reference of 275 g raises the median error "
      "to 5.34 per cent and a fat reference of 78 g to 7.29. The pre-2016 "
      "values were adopted on that evidence rather than on the collection "
      "date alone."),

("p", "Allergen tagging produced the most consequential finding in the "
      "pipeline, and it contradicted the design. Chapter 3 originally "
      "specified that matching run on ingredient strings after normalisation "
      "through the ingredient map. Implementing it that way destroys the "
      "composite layer: the map resolves multi-word entries to a canonical "
      "head word, so Worcestershire sauce becomes sauce, while the composite "
      "layer exists precisely because the complete phrase is the only "
      "evidence the allergen is present. Of the 121,830 recipes flagged for "
      "gluten, 102,939 are flagged only by a composite rule, as are all "
      "41,737 sulphite flags. Matching therefore runs on the raw strings, and "
      "Section 3.2.4 was corrected to say so. The map remains in use for what "
      "it is good at: supplying the content-based vocabulary, and identifying "
      "the 1.47 per cent of the corpus whose ingredients it cannot resolve, "
      "the residue the fail-closed rule excludes."),

("p", "The rate at which the lexicon misses allergens genuinely present was "
      "measured rather than assumed. A sample of 160 recipes was labelled by "
      "hand and compared against the rules, giving a false-negative rate of "
      "5.7 per cent for the first version of the lexicon. Inspecting the "
      "fourteen misses produced a second version: the misses fell to zero on "
      "that sample and, because several new exempt phrases were added at the "
      "same time, false positives fell from thirteen to seven. Chapter 5 "
      "reports the re-measurement of the revised lexicon on an independent "
      "sample, because a rate measured on the sample used to build a rule set "
      "is an optimistic estimate of that rule set and cannot honestly be "
      "quoted as its error rate."),

# ---------------------------------------------------------------------------
("h2", "4.3  User model"),

("p", "The user model implements the Mifflin-St Jeor equation, scales it by a "
      "physical activity level, and divides the result into macronutrient "
      "targets by the proportions of Section 3.3.2. The implementation is "
      "direct and required no revision. What did require revision is how a "
      "slot's share of those targets is computed."),

("p", "The first implementation gave each slot a fixed share of the daily "
      "figures, twenty-five, thirty-five and forty per cent, regardless "
      "of what the earlier meals of the day had actually supplied. Under that "
      "arrangement an excess at breakfast is never recovered, because lunch "
      "and dinner are scored against a target that does not know about it, so "
      "a day's errors accumulate in one direction. The allowance is now "
      "computed as the daily figure less what the day has already been given, "
      "divided among the slots still to be filled in the same proportions. A "
      "heavy breakfast tightens lunch and dinner automatically. The change is "
      "small in code and substantial in effect, and it is the reason the "
      "scoring terms in Section 3.5.2 are defined against a remaining "
      "allowance rather than against a fixed share."),

# ---------------------------------------------------------------------------
("h2", "4.4  Recommendation engine"),

("p", "The content-based component vectorises each recipe as its normalised "
      "ingredients and course tags under term-frequency-inverse-document "
      "weighting, and scores candidates by cosine similarity against a "
      "profile vector. The collaborative component is a truncated matrix "
      "factorisation with a global mean, user and item biases and twenty "
      "latent factors, trained by stochastic gradient descent over 590,358 "
      "ratings with 65,596 held out for validation. It reaches a validation "
      "root mean squared error of 1.1826, against 1.2306 for predicting the "
      "global mean, 1.2217 for the user mean and 1.2816 for the item mean, "
      "each baseline being fitted on the training split alone. Section 5.2 "
      "develops this into a full comparison; it is quoted here because it "
      "establishes that the component works at all, which is a precondition "
      "for the switching policy having anything to switch to."),

("p", "A user of the running interface is not in the training matrix, and "
      "the system deliberately has no account and no database in which to put "
      "them. Their ratings are instead folded into the existing latent space "
      "by least squares against the fitted item factors, which yields a user "
      "vector without retraining and without persisting anything. The choice "
      "is a design decision as much as an implementation one: it means the "
      "collaborative component requires neither registration nor storage of "
      "personal data, and that a user's ratings exist only for the duration "
      "of their session."),

("p", "The component exposes its rating prediction and its ranking signal "
      "separately, for the reason given in Section 3.4.2: the item bias "
      "belongs in the first and ruins the second. That separation was not in "
      "the original implementation. It was introduced after the evaluation of "
      "Section 5.3 measured the ranking produced by the full prediction and "
      "found it indistinguishable from random, and it is the only change to "
      "the recommender that the evaluation itself prompted."),

("p", "One defect in this component surfaced very late. The profile vector was formed by weighting each rated "
      "recipe's vector by its rating, which is wrong in a way that is "
      "invisible until negative ratings exist: a one-star rating multiplies "
      "the disliked recipe's vector by one and adds it, moving the profile "
      "towards the thing the user has just rejected. The component behaved "
      "correctly for months of development because nothing had yet supplied a "
      "low rating. Weighting by the rating's distance from the midpoint of "
      "the scale corrects it. Measured on one recipe, its own score rises "
      "from 0.319 to 0.534 when rated five and falls to 0.042 when rated one; "
      "before the correction, one star raised it as well. The defect became "
      "reachable only when the interface gained an explicit rating control, "
      "which is a general point about this kind of system: a component can be "
      "wrong in a direction no test exercises until a feature elsewhere makes "
      "that direction possible."),

# ---------------------------------------------------------------------------
("h2", "4.5  Constraints and scoring"),

("p", "The hard filter is implemented in two parts. The user-dependent rules "
      "are computed once per plan, being the expensive part and invariant "
      "across the twenty-one slots; the slot-dependent rules are applied per "
      "slot. Clinical ceilings began in the first group and had to be moved "
      "to the second, for a reason found by an assertion rather than by "
      "inspection: the filter tested sodium per serving while the planner "
      "served up to three servings, so a plan could satisfy an 800 mg ceiling "
      "recipe by recipe and still place 2,400 mg on the plate. A clinical "
      "limit constrains what is eaten, so it binds on the quantity served, "
      "which is knowable only once the slot is known."),

("p", "Adaptive relaxation, specified in Section 3.5.3, could not fire as "
      "first implemented. The relaxation step of Section 3.6.2 is reached "
      "when no candidate is admissible, but after hard filtering the score is "
      "an argmax over a non-empty set, which always returns a winner. The "
      "step was therefore unreachable code that the chapter described as a "
      "feature. The resolution was to give the soft constraints "
      "admissibility gates, so that a slot rejects a candidate whose "
      "energy or nutritional error exceeds a tolerance. A genuinely poor "
      "fit then leaves the admissible set empty and relaxation has "
      "something to relax. Hard "
      "constraints take no part in this: they read none of the relaxation "
      "parameters, so the guarantee that relaxation cannot reach an allergen "
      "rule is structural rather than a matter of the order in which the "
      "rules were written."),

("p", "The energy tolerance was set by measurement. Sweeping it across four "
      "profiles gave worst-day energy deviations of 12 to 20 per cent at 0.50, "
      "11 to 18 at 0.35, 5 to 18 at 0.25 and 8 to 9 at 0.15, with all "
      "twenty-one slots filled at every setting; 0.15 was adopted. The "
      "scoring weights were deliberately left alone: Section 3.5.2 states "
      "they are initial values to be tuned in Chapter 5, and adjusting them "
      "to make a smoke test pass would have pre-empted that experiment. A "
      "tolerance decides which candidates are eligible for a slot; a weight "
      "decides how the eligible ones are ranked."),

("p", "The nutritional term needed the most correction, and the defect was "
      "found by reading the interface rather than by any test. Energy was "
      "within about one per cent of target every day, which looked like "
      "success until the other nutrients were examined: sodium stood at 245 "
      "to 390 per cent of its ceiling, free sugars at 208 to 473 and fat at "
      "126 to 171. Three causes compounded: the term covered only protein, "
      "fat and carbohydrate and treated fat as a target rather than a "
      "ceiling, leaving sodium, sugars and saturated fat unscored; "
      "accompaniments were chosen on energy alone; and each slot was "
      "scored independently, so an early excess was never recovered. The "
      "term now separates quantities to reach from ceilings not to exceed "
      "and averages the two groups separately, pooling having allowed one "
      "violated ceiling to be diluted by three satisfied ones, from a "
      "penalty of 1.0 to 0.17. The weight given to exceedance was then set "
      "by measurement, reported in Section 5.7."),

("p", "The correction is paid for in energy, which now sits below target "
      "rather than on it: Section 5.5 measures a mean daily attainment of 92 "
      "per cent across twelve profiles, and an undershoot in every one of "
      "them. That is the right direction for the error to fall. For a tool "
      "whose purpose is nutritional balance, falling short of an energy "
      "target while holding four guideline ceilings is a more defensible "
      "failure than meeting the energy target by exceeding the ceiling for "
      "salt fourfold."),

("p", "The exclusion list is matched by a rule rewritten after excluding oats "
      "produced a plan containing oatmeal. Testing whether the typed term "
      "occurs as a substring of the ingredient text is wrong in both "
      "directions at once, as Table 4.1 shows: too permissive, because oat "
      "occurs inside goat, and too strict, because oats does not occur "
      "inside oatmeal. Matching is now anchored at a word boundary and "
      "applied to the term's stem. The residual error is over-exclusion, "
      "since a stem also prefixes unrelated foods: excluding peas removes "
      "peaches. For a preference list that is the tolerable direction, and "
      "it is tolerable only because it is visible: the interface lists the "
      "ingredients each term matched, so an over-broad term can be reworded. None of this applies to declared allergens, matched by the "
      "lexicon of Section 3.2.4, which flags every oat form as gluten."),

("tablecaption", "Table 4.1  Behaviour of the exclusion rule before and after "
                 "revision. Survivors are recipes remaining in the cleaned "
                 "corpus of 128,403 after the term is excluded."),
("table", [
    ["Term typed", "Substring rule", "Word-stem rule (adopted)"],
    ["oats", "778 oat ingredients survive, including oatmeal, oat bran and "
             "oat flour", "no oat ingredient survives"],
    ["oat", "goat's cheese removed from a user who said nothing about goats",
     "830 goat recipes retained"],
    ["oats vs oat", "different results for the same intention",
     "identical results"],
]),

# ---------------------------------------------------------------------------
("h2", "4.6  Weekly planner and interface"),

("p", "The planner fills slots in the order set out in Section 3.6.2. Its "
      "first implementation gave each slot a single recipe, and all four test "
      "profiles came out 35 to 45 per cent below their daily energy target. "
      "The cause was not in the code: a serving in this corpus is much "
      "smaller than a meal. The median dinner candidate supplies 381 kcal "
      "where the dinner slot of a 2,440 kcal day asks for 976, and only 5.5 "
      "per cent of dinner candidates reach that in one serving. The design "
      "had assumed something the data does not support."),

("p", "Serving multiple portions of the chosen recipe fixed the arithmetic "
      "and was abandoned on seeing a plan it produced: nobody follows an "
      "instruction to eat the same dish three times, and a person facing a "
      "small plate adds a side. Measurement agreed. Against the 976 kcal "
      "dinner target, a main dish with up to two accompaniments brings 95.9 "
      "per cent of dinner candidates within ten per cent of target, against "
      "49.8 per cent for repeated servings of the main alone; more than one "
      "serving of the main added nothing once accompaniments existed. The "
      "pool of 13,341 accompaniments is drawn from recipes the meal-slot rule "
      "had discarded and is disjoint from the main corpus, so admitting it "
      "leaves the figures of Section 3.2.2 unchanged. Daily energy deviation "
      "fell from 35-45 per cent, through 8-9 per cent with portion scaling, "
      "to between 0.6 and 1.6 per cent."),

("p", "A working plan overturned a second assumption. Section 3.6.5 had "
      "barred a recipe from reappearing once placed, on the grounds that "
      "nobody would regard the same dish twice in a week as a recommendation. "
      "Seen in a produced plan that does not hold: a dish that is liked, "
      "quick and within target is welcome more than once provided what is "
      "served beside it changes. The premise was an assumption about users "
      "that no user had been asked about. Repetition is now bounded rather "
      "than forbidden, the bound is exposed as a control, and accompaniments "
      "never repeat."),

("p", "Retaining a meal across a rebuild introduced a subtler defect. The "
      "look-ahead penalty compares what remains of the day's energy against "
      "the slots still to come. A retained meal has its energy counted in "
      "what the day has consumed, while the slot it occupies was still "
      "counted among those to be filled, so its energy was charged twice and "
      "the following slots were starved. Counting only unfilled slots "
      "corrects it."),

("image", "screenshots/01_form_and_week.png", 4.6),
("figurecaption", "Figure 4.1  The profile sidebar and the compact view of "
                  "the week. The notice that allergen screening is automated "
                  "and is not a safety guarantee is present on every screen."),

("image", "screenshots/02_day_by_day_crop.png", 4.5),
("figurecaption", "Figure 4.2  One day of the plan. Each card carries the "
                  "main dish, its accompaniments, the totals for the plate, "
                  "the allergen classes flagged anywhere on it, and the "
                  "complete ingredient list, expanded by default."),

("p", "The interface produced two defects no automated check in this project "
      "could have found. The first was a crash: every card failed to render "
      "but one, and that one card was the diagnosis. Ingredient names were "
      "being interpolated into raw markup, and 5,982 ingredient names in the "
      "corpus contain a bare ampersand, which is not a valid entity; the "
      "surviving card happened to contain none. The rule adopted is stronger "
      "than escaping: corpus text does not enter raw markup at all. The check "
      "that guards it renders the interface and asserts that no recipe or "
      "ingredient name appears in any raw markup block, a static scan being "
      "unable to tell whether a variable holds corpus text. An earlier "
      "static version produced two false positives and was replaced."),

("p", "The second defect was purely visual and therefore invisible to every "
      "assertion in the project. The week was first laid out as seven columns "
      "of full cards, each about 130 pixels on a wide display, which is "
      "narrower than the words that must go in it: recipe names wrapped to "
      "four lines and the controls degraded to vertical stacks of single "
      "letters. The automated suite passed in full while this was on screen, "
      "because it runs against a harness that builds the element tree and "
      "never renders it. The defect became visible the first time the "
      "interface was photographed in a browser. The layout was restructured "
      "into the two scales of Section 3.7.2, shown in Figure 4.1 and "
      "Figure 4.2, "
      "and the screenshot script was kept as a routine check rather than only "
      "as a means of producing figures."),


("image", "screenshots/03_nutrition_crop.png", 4.5),
("figurecaption", "Figure 4.3  The nutritional panel, separating quantities "
                  "to reach from limits not to exceed and stating how the "
                  "targets were derived from the user's own body data."),

("p", "The nutritional panel of Figure 4.3 was rewritten because its first "
      "version could not be read. The original wording described totals as "
      "covering every dish on the plate and distinguished guideline ceilings "
      "from targets: accurate, and not English a non-specialist reads. It now "
      "states plainly where the numbers come from, separates quantities to "
      "reach from limits not to exceed, and reports what the week achieved "
      "against each. The requirement is unchanged; only its legibility to the "
      "person it is for was at fault, and no assertion can detect that."),


("image", "screenshots/06_restriction_changed_crop.png", 4.7),
("figurecaption", "Figure 4.4  A restriction changed and the plan not yet "
                  "rebuilt. The plan is labelled as out of date and every "
                  "card is withheld until it is rebuilt."),

("p", "The state shown in Figure 4.4 was originally rendered as an error "
      "message. A user reported it as the application having crashed, which "
      "it had not: a red panel is what this framework shows when a script "
      "fails, so a safety notice wearing that appearance is read as a fault. "
      "A notice mistaken for a fault teaches the user to dismiss it, which is "
      "the opposite of its purpose. It is now styled as part of the page and "
      "opens by saying that nothing has gone wrong."),

("p", "The generated note in the detail view is a separate module, and the "
      "separation is the point rather than a convenience: it is called after "
      "planning, receives only figures the planner has already computed, and "
      "nothing it returns is read by any filter, score or ranking. Its "
      "instruction forbids any statement about allergens, safety or medical "
      "suitability, and its output passes through a filter that discards such "
      "a response in favour of an arithmetically derived note. The filter "
      "rejects rather than edits, because repairing a partially unsafe "
      "sentence would leave the judgement of what is safe to keep with the "
      "component that has just demonstrated it does not know. Where no model "
      "is configured, the network is unavailable or a response is rejected, "
      "the derived note is shown and no functionality is lost."),

# ---------------------------------------------------------------------------
("h2", "4.7  Verification"),

("p", "The system is checked by two complementary suites, neither of which "
      "replaces the other. The first is thirteen groups of assertions "
      "covering four things: that the corpus reproduces the contract of "
      "Section 4.2; that every safety property holds, meaning the "
      "fail-closed filter, the independence of hard constraints from "
      "relaxation, the withholding of a plan whose restrictions have changed "
      "and the safety filter on generated text; that a complete plan "
      "satisfies its invariants and responds to a rating in the right "
      "direction; and that no corpus text reaches raw markup. Where a defect "
      "described earlier was found by an assertion, that assertion remains "
      "in the suite."),

("p", "The second suite drives the interface in a real browser and "
      "photographs it. Its immediate purpose is to produce this chapter's "
      "figures reproducibly rather than by hand, but its value proved "
      "diagnostic: the first suite inspects the element tree without laying "
      "it out, so it cannot see a column too narrow for its contents. Every "
      "visual defect in this project was found by the second suite or by "
      "looking at the running interface."),

("p", "The screenshot script starts and stops its own server, because "
      "the framework re-executes the main script on every "
      "interaction but retains imported modules, so a server started before a "
      "stylesheet change keeps serving the previous one, photographing "
      "whatever was loaded at start-up while reporting no errors. A round of "
      "interface changes was reviewed that way before the cause was found. "
      "The script also asserts the state it is about to photograph: when the "
      "interaction that changes a restriction failed silently, the resulting "
      "figure showed an unlocked plan and would have documented the opposite "
      "of what it was taken to show."),

("p", "The exclusion defect of Section 4.5 shows where this strategy fails. "
      "It survived a suite passing in full, and survived "
      "an assertion written specifically to guard it: that assertion checked "
      "that no surviving recipe contained the string oats, which is true of "
      "a plan containing oatmeal, so it passed. It tested the "
      "implementation's own notion of matching rather than the user's notion "
      "of an oat, and an assertion protects only the property it states. A "
      "wrong assertion is worse than a missing one, because it is counted as "
      "coverage. This is the second defect found by using the running system "
      "while the suite reported success, the first being the nutritional "
      "term of Section 4.5. Both point the same way: automated checks defend "
      "against the failures their author has already imagined. That is the "
      "argument for evaluating a system by using it, and for the independent "
      "user evaluation Section 5.9 identifies as this work's principal "
      "limitation."),

# ---------------------------------------------------------------------------
("h2", "4.8  Summary of defects and their origins"),

("p", "Table 4.2 collects the defects discussed above with the means by "
      "which each was found. Assertions caught the arithmetic errors, "
      "users caught the errors of "
      "assumption, rendering caught what neither could see, and no single "
      "method found more than half."),

("tablecaption", "Table 4.2  Defects found during implementation, how each "
                 "was discovered, and its effect."),
("table", [
    ["Defect", "Found by", "Effect once corrected"],
    ["Clinical ceiling tested per serving, not per plate", "Assertion",
     "Sodium ceiling respected for the quantity actually served"],
    ["Relaxation step unreachable", "Implementation",
     "Soft admissibility gates added; relaxation reachable"],
    ["Look-ahead double-charging a retained meal", "Assertion",
     "Following slots no longer starved"],
    ["Profile vector moved towards disliked recipes", "Assertion",
     "0.319 to 0.534 when rated five, 0.042 when rated one"],
    ["Single recipe cannot fill a meal slot", "Smoke test",
     "Daily energy deviation 35-45% to 0.6-1.6%"],
    ["Ceilings absent from the scoring function", "Use of the system",
     "Sodium 390% to 88-100% of ceiling"],
    ["Allergen matching specified after normalisation", "Implementation",
     "102,939 composite gluten flags retained"],
    ["Ingredient names interpolated into raw markup", "Use of the system",
     "No corpus text in raw markup; behavioural check added"],
    ["Seven-column layout unusably narrow", "Rendering",
     "Two-scale layout of Section 3.7.2"],
    ["Exclusion matched as a substring", "Use of the system",
     "No oat product survives; goat recipes retained"],
    ["Safety notice styled as a crash", "Use of the system",
     "Notice restyled; states that nothing has gone wrong"],
    ["Nutritional panel unreadable to a non-specialist", "Use of the system",
     "Panel rewritten in plain terms"],
    ["Ranking by predicted rating ranks by the item bias", "Evaluation",
     "NDCG@10 0.0001 to 0.0025; the switching policy becomes justified"],
]),

("p", "Thirteen defects are listed and five of them were found by using the "
      "running system rather than by any automated check. Several of the "
      "five could not have been found any other way: they are errors of "
      "assumption about what a person wants or can read, and no assertion "
      "written by the author of an assumption will contradict it."),
]
