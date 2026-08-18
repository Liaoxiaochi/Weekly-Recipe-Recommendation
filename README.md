# Personalized Weekly Recipe Recommendation

A recommender that produces a seven-day meal plan for one user, balancing what
they like against what they can eat and what they should eat.

MSc Advanced Computer Science, University of Leeds.
Xiaochi Liao, supervised by Dr Kelvin Lau.

This repository accompanies the dissertation *Personalized Weekly Recipe
Recommendation Based on User Preferences and Nutritional Balance*. Chapter 3
specifies the design; Chapter 4 describes this implementation.

---

## What is not in this repository, and why

**The dataset is not included.** Food.com's data is published on Kaggle under
"Data files (c) Original Authors", which grants no redistribution licence, so
neither the raw files nor the derived corpus (`code/outputs/*.pkl`) are shipped
here. Everything needed to *reproduce* them is, and the pipeline is
deterministic: the numbers in Section 3.2 are reproduced exactly by the steps
below, and the verification suite fails if they are not.

**No API key is included.** `.streamlit/secrets.toml` is git-ignored. The
system runs fully without one; see "Optional: generated notes" below.

---

## Requirements

Python 3.11. Only one package is not in a standard scientific install:

```bash
pip install streamlit          # the interface
pip install openai             # optional, for generated notes only
pip install playwright && playwright install chromium   # optional, screenshots
```

`pandas`, `numpy`, `scikit-learn`, `pillow` and `python-docx` are also used.
Neither Surprise nor implicit is required: the matrix factorisation is
implemented directly in numpy (`src/recommenders.py`), which avoids a C
toolchain dependency on Windows.

## 1. Get the data

Download `archive.zip` from
<https://www.kaggle.com/datasets/shuyangli94/food-com-recipes-and-user-interactions>
and place these two files in `data/`:

```
data/RAW_recipes.csv          231,637 recipes
data/RAW_interactions.csv     1,132,367 interactions
```

## 2. Build the corpus

```bash
python code/src/preprocessing.py
```

Cleans, converts the percentage-of-daily-value nutrition fields to grams,
normalises ingredients, tags allergens and assigns meal slots. It writes
`code/outputs/` and reconciles its own results against
`code/outputs/dataset_profile.json`, exiting non-zero on any mismatch.

It must reproduce exactly:

| quantity | value |
|---|---|
| recipes retained | 128,403 |
| interactions retained | 655,954 |
| breakfast / lunch / dinner candidates | 19,919 / 40,779 / 103,389 |

These figures are quoted in Chapter 3. If a run disagrees, the code is wrong,
not the chapter.

## 3. Train the collaborative model

```bash
python code/src/recommenders.py
```

Truncated SVD trained by stochastic gradient descent over 590,358 ratings,
validated on 65,596 held out. Writes `code/outputs/mf.pkl`.

## 4. Run the interface

```bash
streamlit run code/app.py
```

Enter body data, cooking-time budgets and any restrictions in the sidebar, then
press **Build my week**.

## 5. Verify

```bash
python code/verify_prototype.py   # 13 groups: corpus contract, fail-closed
                                  # filtering, planning invariants, exclusion
                                  # semantics, safety of generated text
python code/verify_thesis.py      # the chapters against the code
python code/verify_figures.py     # every figure against the house palette
python code/shoot.py              # drives a real browser, writes 7 screenshots
```

`verify_prototype.py` and `shoot.py` are complementary and neither replaces the
other: the first runs against Streamlit's `AppTest`, which builds the element
tree but never renders, so it cannot see a control that has wrapped or a column
too narrow for its contents. `shoot.py` starts its own server, drives Chromium
and photographs the result.

---

## Optional: generated notes

The recipe detail view carries a short written note. It is a presentation-layer
aid and is **not part of the recommender**: it runs after planning, describes
figures the planner has already computed, and contributes nothing to filtering,
scoring or ranking.

Without a key, the note is derived arithmetically from the plan and the system
is fully functional. To enable the generated variant, create
`.streamlit/secrets.toml` (git-ignored):

```toml
DEEPSEEK_API_KEY = "sk-..."
DEEPSEEK_MODEL = "deepseek-chat"
```

A generated note may make no claim about allergens, safety or medical
suitability. This is enforced twice — in the instruction and by a filter on the
output — and any response that fails is discarded in favour of the derived one.

## Safety

Allergen screening is automated and is **not a safety guarantee**. Ingredients
are matched against a rule set whose false-negative rate is measured rather than
assumed to be zero. The interface says so persistently and shows the full
ingredient list of every dish expanded by default. Declared allergens are never
traded off against preference and are never relaxed; where an ingredient cannot
be resolved and an allergy is declared, the recipe is excluded rather than
admitted.

No user data is stored. There is no account and no database: ratings given in
the interface are fitted into the trained model in memory for that session only.

## Layout

```
code/
  src/preprocessing.py    cleaning -> nutrition -> allergens -> meal slots
  src/user_model.py       Mifflin-St Jeor -> activity -> macronutrient targets
  src/recommenders.py     content-based, collaborative, switching controller
  src/constraints.py      hard filter, soft penalties, adaptive relaxation
  src/weekly_planner.py   greedy placement with look-ahead; replacement
  src/advisor.py          generated notes (presentation layer only)
  app.py                  Streamlit interface
  uistyle.py              interface palette;  figstyle.py = figure palette
  shoot.py                browser-driven screenshots
  build_docx.py           assembles Chapters 3 and 4 into the thesis
  verify_*.py             the verification suites
```
