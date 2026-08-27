"""Appendices A and B, replacing the template placeholder text.

WHY THIS EXISTS.  Both appendices in the source document still carry the Leeds
template's filler ("Text under appendix heading. Text under appendix
heading."). That is a problem beyond untidiness: Section 1.4 already tells the
reader that "Appendix A records how the corpus can instead be obtained and
reproduced from its original source", so the dissertation currently makes a
forward reference to a page that says nothing. verify_thesis.py cannot detect
this, because its placeholder check looks for "[[" markers and template filler
contains none.

WHAT GOES IN THEM.  The marking guidance asks for "relevant discussion of
legal, social, ethical and professional issues" under the same criterion as the
literature review, and separately for effective use of appendices. Appendix A
therefore carries the external-materials declaration -- what was used, under
what terms, and why none of it is redistributed with the submission. Appendix B
carries the ethical position, including the two matters a reader most needs to
be able to check: that no user data is stored at all, and that the allergen
screening has a measured failure rate and is not a safety guarantee.

ONE INCONSISTENCY IS CORRECTED HERE.  The Scope and Planning form undertook
that user data would be "stored securely and anonymised". The system as built
stores no user data whatsoever, which is a stronger position than the one
promised. Appendix B says so explicitly, because a reader comparing the two
documents would otherwise be left to work out whether the change was an
improvement or a lapse.
"""

# Everything from the "Appendix A" heading up to but excluding the "Appendix B"
# heading is discarded, and likewise from "Appendix B" to the end of the body;
# the blocks below are inserted in their place.
REPLACE_FROM_HEADING = ["Appendix A", "Appendix B"]

APPENDIX_A = [

("p", "This appendix declares the external material used in the project, the "
      "terms under which it was used, and the reasons it is not redistributed "
      "with the submitted software."),

("h2", "A.1  Recipe corpus"),

("p", "The recipe and interaction data are the Food.com Recipes and User "
      "Interactions dataset, published on Kaggle by Shuyang Li and derived "
      "from the work of Majumder et al. [41]. Two files were used: "
      "RAW_recipes.csv, containing 231,637 recipes with ingredient lists, "
      "tags, preparation times and a seven-element nutrition tuple, and "
      "RAW_interactions.csv, containing 1,132,367 user ratings. The dataset "
      "is available at https://www.kaggle.com/datasets/shuyangli94/"
      "food-com-recipes-and-user-interactions."),

("p", "The licensing position requires care because it is more restrictive "
      "than a public dataset might be assumed to be. The Kaggle release "
      "states its terms as “Data files © Original Authors”, "
      "which reserves copyright to the individual contributors and grants no "
      "licence to redistribute. The corpus is used here for non-commercial "
      "research and private study under the exceptions in sections 29 and 29A "
      "of the Copyright, Designs and Patents Act 1988, which permit "
      "text and data mining for non-commercial research on material to which "
      "lawful access has been obtained."),

("p", "Accordingly, neither the raw data files nor any derived copy of them "
      "is included with the submitted software. This applies to the CSV files "
      "themselves and equally to the processed artefacts built from them: "
      "the corpus, interaction and recipe-detail pickles, and the fitted "
      "content and factorisation models. Those contain recipe text and "
      "ratings in a rearranged form rather than a transformed one. The "
      "README distributed with the code gives the download location and the "
      "single command that rebuilds every artefact from it, and states the "
      "counts that a correct rebuild must reproduce, so that the results in "
      "Chapters 3 to 5 can be verified without the data being passed on. The "
      "interface links each dish to its page on the originating site rather "
      "than reproducing the recipe wholesale, for the same reason."),

("h2", "A.2  Standards and reference data"),

("p", "Allergen classes follow Annex II to Regulation (EU) No 1169/2011 [43], "
      "which enumerates the fourteen substances requiring declaration; the "
      "lexicon that detects them in ingredient text is the author's own work "
      "and is not derived from any external list. Conversion of the corpus's "
      "percentage nutrition figures to absolute quantities uses the daily "
      "values in 21 CFR 101.9 [42]. Energy and macronutrient targets follow "
      "the Mifflin-St Jeor equation [44] with activity factors from the "
      "Scientific Advisory Committee on Nutrition [45], and guideline "
      "ceilings follow Public Health England's dietary recommendations [46]."),

("p", "Table A.1 lists the fourteen classes with a representative "
      "composite rule from the third layer of the lexicon and the "
      "number of recipes each flags in the raw corpus. The rightmost "
      "column is the reason the composite layer exists rather than "
      "being a refinement of the other two."),

("tablecaption", "Table A.1  Allergen classes of Annex II to Regulation (EU) No "
                 "1169/2011 [43], with a representative composite rule and "
                 "the number of recipes flagged in the raw corpus of 231,637."),
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

("h2", "A.3  Software"),

("p", "The system is written in Python 3.11 and uses pandas and NumPy for "
      "data preparation, scikit-learn for term weighting, Streamlit for the "
      "interface, Matplotlib for the figures, python-docx to assemble this "
      "document and Playwright to capture the interface screenshots. All are "
      "open-source libraries used under their own licences and none is "
      "redistributed here. The matrix factorisation was implemented directly "
      "rather than taken from a library, as Section 4.4 explains."),

("p", "One external service is used. The per-dish commentary described in "
      "Section 4.6 calls the DeepSeek chat completion API. Its role is "
      "confined to the presentation layer: it runs after planning is "
      "complete, restates quantities the system has already computed, and has "
      "no influence on filtering, scoring or selection, so no result in "
      "Chapter 5 depends on it. Its output is additionally filtered to remove "
      "any statement about allergens, safety or medical suitability, and the "
      "interface falls back to text generated from the computed figures when "
      "the service is unavailable. The API key is held in a local "
      "configuration file that is excluded from version control and from the "
      "submission."),

]

APPENDIX_B = [

("p", "This appendix records the ethical issues the project raises and how "
      "each was handled. Section 1.4 discusses them as they bear on the "
      "design; what follows states the position as implemented."),

("h2", "B.1  Personal data"),

("p", "The system stores no user data. Height, weight, age, activity level, "
      "dietary restrictions and ratings are held for the duration of a "
      "browser session and are discarded when it ends. Nothing is written to "
      "a database, no account exists to be created, and the ratings a user "
      "supplies during a session are folded into the factorisation's latent "
      "space at request time rather than added to the trained model. No "
      "personal data therefore leaves the user's session, and there is no "
      "stored record to be disclosed, breached or subject to a deletion "
      "request."),

("p", "This is a departure from the Scope and Planning form, which undertook "
      "that user data would be stored securely and anonymised, and the "
      "direction of the departure should be stated plainly rather than left "
      "to inference. Storing nothing is a stronger guarantee than storing "
      "securely, because it removes the risk rather than managing it. The "
      "change was possible because nothing in the design turned out to "
      "require persistence: the collaborative model is trained offline on the "
      "public interaction data, and a returning user's preferences can be "
      "re-entered in less time than an account would take to create. The one "
      "cost is that preferences are not remembered between sessions, which is "
      "a usability cost and not an ethical one."),

("h2", "B.2  Allergen screening is not a safety guarantee"),

("p", "The system filters out recipes whose ingredients match a user's "
      "declared allergens, and the filter is fail-closed: a recipe whose "
      "ingredient text cannot be parsed is excluded rather than admitted, and "
      "the exclusion is never relaxed by the adaptive mechanism of Section "
      "3.5.3. That design reduces the risk of a false negative but does not "
      "eliminate it. Section 5.8 reports the measured rate: on 104 recipes "
      "labelled by hand and not used to build the lexicon, 2.5 per cent of "
      "the allergens genuinely present were missed. The four failures were "
      "composite foods: baguette, corn flakes, brownie mix and queso "
      "fresco, whose constituent allergens the ingredient text does not "
      "name."),

("p", "The ethical obligation that follows is to be explicit rather than "
      "reassuring. The interface states at the point of use that screening is "
      "automated and is not a safety guarantee, and repeats it in the "
      "nutritional panel; the wording is deliberately plain and is not "
      "reduced to a footnote. A person with a clinically significant allergy "
      "should read the ingredient list on the originating recipe page, to "
      "which every dish links, before cooking. Reporting the failure rate "
      "rather than omitting it is part of the same obligation: a reader "
      "cannot calibrate their reliance on a filter whose error rate is "
      "unstated."),

("h2", "B.3  Nutritional advice and professional competence"),

("p", "The author is a computer scientist and not a registered dietitian, and "
      "a system that appears to give dietary advice while being built by "
      "someone unqualified to give it raises a professional issue before an "
      "ethical one. The response is a set of constraints on what the system "
      "is permitted to claim rather than a disclaimer alone. It presents "
      "suggestions and not prescriptions; it derives targets from published "
      "national guidance [45, 46] rather than from any judgement of its own; "
      "it shows the reasoning behind each choice as a sum of named terms "
      "rather than issuing a verdict; and it makes no statement anywhere "
      "about medical suitability, a restriction enforced in code over the "
      "generated commentary rather than left to the wording of individual "
      "messages. Users with clinical dietary requirements are directed to "
      "their clinician, and the system is not represented as a substitute for "
      "that advice."),

("h2", "B.4  User evaluation and informed consent"),

("p", "A usability study with three to five participants was planned, and "
      "recruitment materials, an information sheet and a consent form were "
      "prepared covering the purpose of the study, the voluntary nature of "
      "participation, the right to withdraw, and what would be recorded. The "
      "study was not run. Such a study requires ethical approval, and the "
      "supervisor advised on 18 August 2026 that beginning an application at "
      "that stage of the project would not be a sound use of the time "
      "remaining. No participant was approached and no participant data of "
      "any kind was collected, so no consent was required and none was "
      "obtained. The consequence for what this dissertation may claim is "
      "recorded as its principal limitation in Section 5.9, and the timing "
      "lesson is drawn out in Section 6.5."),

("h2", "B.5  Where the recipe data came from, and how it is credited"),

("p", "The recipes were written by individual contributors to a public "
      "website who did not consent to their use in research, and the dataset "
      "grants no redistribution licence. The project's response is set out in "
      "Appendix A: the data is used under the non-commercial research "
      "exception, is not redistributed in raw or derived form, and every dish "
      "shown in the interface links to its original page rather than "
      "reproducing it. The interaction data is pseudonymous as published, "
      "containing numeric user identifiers rather than names, and no attempt "
      "was made to re-identify any user or to characterise any individual "
      "beyond fitting the aggregate factorisation described in Section 3.4.2."),

]
