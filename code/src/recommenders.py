"""Recommenders and the switching controller.

Implements Section 3.4 of the dissertation: a content-based component, a
collaborative component, and a controller that selects between them per request
on the size of the user's interaction history.

Both components expose the same two methods, so that either -- or one of the
baselines used in the evaluation -- can be substituted without the planner
noticing:

    is_available(profile)   whether this component can serve this user at all
    scores(profile)         a relevance score for every recipe in the corpus

Run:  python code/src/recommenders.py       builds and stores the index
Out:  code/outputs/content_index.pkl
"""

import os
import pickle
import sys
import time

import numpy as np
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "outputs")

sys.path.insert(0, HERE)
from user_model import preference_tokens  # noqa: E402

# The switching threshold (§3.4.3).  Set from the interaction distribution
# rather than by assertion: the median user has rated one recipe, 10.2 per cent
# have rated five or more and 5.5 per cent ten or more, so a threshold high
# enough for a well-estimated factor vector would exclude almost everyone.
# Ten admits the densest 5.5 per cent while keeping ten observations behind
# every estimate.  Chapter 5 examines the sensitivity of the results to it.
SWITCH_THRESHOLD = 10

# Weight applied to a rejected recipe when it is fed back as a negative
# preference signal (§3.6.3).  Below one because a rejection says less about
# preference than an explicit rating does: a user may reject a recipe for a
# reason the ingredient vector cannot see.
REJECTION_WEIGHT = 0.5

# Midpoint of the five-point rating scale.  Ratings are expressed relative to
# it, so that a rating below it is evidence against a recipe rather than weaker
# evidence for it.  Three is the midpoint of the scale the interface offers and
# the scale the corpus records, which keeps session ratings and corpus ratings
# interchangeable for the collaborative component.
NEUTRAL_RATING = 3.0


def identity_analyzer(tokens):
    """Pass a pre-tokenised document through unchanged.

    Defined at module level rather than as a lambda because the vectoriser is
    only useful if it can be pickled, and a lambda cannot be.
    """
    return tokens


# ---------------------------------------------------------------------------
# Offline index construction (§3.7.3: the expensive artefacts are built once)
# ---------------------------------------------------------------------------

def build_content_index(corpus, out_path=None):
    """Build and store the term-document matrix and the ingredient matrix.

    Two matrices come out of this, both over the same rows as `corpus`:

      tfidf   recipes x (ingredients + tags), term frequency-inverse document
              frequency, L2-normalised rows.  Section 3.4.1.  The idf term is
              what makes the representation useful: salt, water and butter
              appear in a large fraction of the corpus and carry almost no
              preference information, whereas a distinctive ingredient
              identifies a style of cooking efficiently.

      ingr    recipes x ingredients, binary.  Used by the repetition penalty of
              Section 3.5.2, which needs ingredient overlap with the partial
              plan and must not be influenced by term weighting.

    Only the arrays and the vocabularies are stored, not the fitted sklearn
    objects, so that loading does not depend on the analyzer being importable
    or on the scikit-learn version matching.
    """
    out_path = out_path or os.path.join(OUT, "content_index.pkl")

    tfidf = TfidfVectorizer(analyzer=identity_analyzer, norm="l2",
                            sublinear_tf=True, min_df=2)
    matrix = tfidf.fit_transform(corpus["doc_tokens"])

    ingr_docs = [[i.replace(" ", "_") for i in ings]
                 for ings in corpus["ingredients_norm"]]
    counts = CountVectorizer(analyzer=identity_analyzer, binary=True, min_df=2)
    ingr_matrix = counts.fit_transform(ingr_docs)

    index = {
        "matrix": matrix.tocsr(),
        "vocabulary": tfidf.vocabulary_,
        "idf": tfidf.idf_,
        "ingr_matrix": ingr_matrix.tocsr(),
        "ingr_vocabulary": counts.vocabulary_,
        "recipe_ids": corpus["id"].to_numpy(),
    }
    with open(out_path, "wb") as f:
        pickle.dump(index, f, protocol=pickle.HIGHEST_PROTOCOL)
    return index


def load_content_index(path=None):
    with open(path or os.path.join(OUT, "content_index.pkl"), "rb") as f:
        return pickle.load(f)


# ---------------------------------------------------------------------------
# Content-based component (§3.4.1)
# ---------------------------------------------------------------------------

class ContentRecommender:
    """Ranks by cosine similarity between a user vector and each recipe.

    Two properties of this component matter for the design.  It scores recipes
    that no one has ever rated, which is what makes it usable for the cold-start
    majority of this corpus.  And it composes cleanly with the hard filter,
    since removing recipes from the candidate set does not alter the scores of
    those that remain -- so the filter can run first and the scores stay valid.
    """

    name = "content-based"

    def __init__(self, index):
        self.index = index
        self.matrix = index["matrix"]
        self.vocabulary = index["vocabulary"]
        self.idf = index["idf"]
        self._row_of = {rid: i for i, rid in enumerate(index["recipe_ids"])}

    def is_available(self, profile):
        """Always: the component needs no history to produce a ranking."""
        return True

    def user_vector(self, profile):
        """The user's position in the recipe space.

        Built from three sources, in the order Section 3.3.3 and Section 3.6.3
        describe: the declared likes of the cold-start pseudo-profile, the
        rating-weighted mean of the recipes rated during the session, and the
        recipes the user replaced by hand, subtracted as a negative signal.
        """
        vec = np.zeros(self.matrix.shape[1], dtype=np.float64)

        for token in preference_tokens(profile):
            col = self.vocabulary.get(token)
            if col is not None:
                vec[col] += self.idf[col]

        rated = [(self._row_of[rid], r) for rid, r in profile.ratings.items()
                 if rid in self._row_of]
        if rated:
            rows = [i for i, _ in rated]
            # Weights are centred on the neutral point of the scale, not taken
            # raw.  With raw weights every rating is positive, so awarding one
            # star would pull the user vector *towards* the dish just rated
            # badly -- the opposite of what the user meant.  Centring makes one
            # and two stars push away and four and five pull towards, which is
            # what a rating control implies.  Normalising by the sum of the
            # absolute weights keeps the result on the same scale whether the
            # ratings are mostly positive or mostly negative.
            weights = np.array([w - NEUTRAL_RATING for _, w in rated],
                               dtype=np.float64)
            denom = np.abs(weights).sum()
            if denom > 0:
                block = self.matrix[rows].toarray()
                vec += (weights[:, None] * block).sum(axis=0) / denom

        rejected = [self._row_of[rid] for rid in profile.rejected
                    if rid in self._row_of]
        if rejected:
            block = self.matrix[rejected].toarray()
            vec -= REJECTION_WEIGHT * block.mean(axis=0)

        norm = np.linalg.norm(vec)
        return vec / norm if norm > 0 else vec

    def scores(self, profile):
        """Cosine similarity to every recipe in the corpus.

        The matrix rows are L2-normalised and the user vector is normalised
        above, so the cosine is a single sparse matrix-vector product.
        """
        vec = self.user_vector(profile)
        if not vec.any():
            # No preference signal at all.  Returning zeros rather than an
            # arbitrary ranking lets the nutritional and contextual terms of
            # Section 3.5.2 decide the order, which is the honest behaviour
            # when the system knows nothing about the user's taste.
            return np.zeros(self.matrix.shape[0], dtype=np.float64)
        return self.matrix @ vec


# ---------------------------------------------------------------------------
# Collaborative component (§3.4.2)
# ---------------------------------------------------------------------------

def train_matrix_factorisation(inter, n_factors=20, epochs=15, lr=0.005,
                               reg=0.05, val_fraction=0.1, seed=20260816):
    """Truncated SVD trained by stochastic gradient descent (§3.4.2).

    Predicts a rating as a global mean plus a user bias, an item bias and the
    inner product of the user and item factor vectors, which is the form that
    has become the standard baseline for rating prediction.  Written directly in
    NumPy rather than taken from a library: the two obvious candidates both
    require a C toolchain, and a build failure two weeks before submission is a
    worse risk than sixty lines of arithmetic.

    A validation split is held out and its root mean squared error returned, so
    the figure Chapter 5 reports is produced by the same run that fits the
    model rather than by a separate script that might drift from it.
    """
    rng = np.random.default_rng(seed)
    users = inter["user_id"].to_numpy()
    items = inter["recipe_id"].to_numpy()
    ratings = inter["rating"].to_numpy(dtype=np.float64)

    uids = {u: i for i, u in enumerate(np.unique(users))}
    iids = {r: i for i, r in enumerate(np.unique(items))}
    u = np.array([uids[x] for x in users], dtype=np.int64)
    i = np.array([iids[x] for x in items], dtype=np.int64)

    order = rng.permutation(len(u))
    cut = int(len(u) * (1.0 - val_fraction))
    tr, va = order[:cut], order[cut:]

    mu = float(ratings[tr].mean())
    bu = np.zeros(len(uids))
    bi = np.zeros(len(iids))
    pu = rng.normal(0, 0.05, (len(uids), n_factors))
    qi = rng.normal(0, 0.05, (len(iids), n_factors))

    history = []
    for epoch in range(epochs):
        rng.shuffle(tr)
        for n in tr:
            uu, ii, r = u[n], i[n], ratings[n]
            pred = mu + bu[uu] + bi[ii] + pu[uu] @ qi[ii]
            err = r - pred
            bu[uu] += lr * (err - reg * bu[uu])
            bi[ii] += lr * (err - reg * bi[ii])
            pu_old = pu[uu].copy()
            pu[uu] += lr * (err * qi[ii] - reg * pu[uu])
            qi[ii] += lr * (err * pu_old - reg * qi[ii])

        pred = (mu + bu[u[va]] + bi[i[va]]
                + np.sum(pu[u[va]] * qi[i[va]], axis=1))
        rmse = float(np.sqrt(np.mean((ratings[va] - np.clip(pred, 1, 5)) ** 2)))
        history.append(rmse)

    return {
        "mu": mu, "bu": bu, "bi": bi, "pu": pu, "qi": qi,
        "user_index": uids, "item_index": iids,
        "val_rmse": history[-1], "rmse_history": history,
        "n_factors": n_factors, "n_train": len(tr), "n_val": len(va),
    }


class CollaborativeRecommender:
    """Matrix factorisation over the rating matrix (§3.4.2).

    Shares an interface with the content-based component so that the controller
    and the planner do not know which of them they are talking to.

    The corpus sets a hard limit on what this component can contribute: the
    median user has rated one recipe and only 5.5 per cent reach the threshold
    of ten, so the controller routes almost everyone to the content-based branch
    regardless.  That argues for the switching design rather than against it --
    a purely collaborative system would have nothing at all to offer those
    users.
    """

    name = "collaborative"

    def __init__(self, factors=None, recipe_ids=None):
        self.factors = factors
        # Held here so that scores() takes the same argument as the
        # content-based component's and the controller can treat them alike.
        self.recipe_ids = recipe_ids

    @classmethod
    def load(cls, recipe_ids, path=None):
        path = path or os.path.join(OUT, "mf.pkl")
        if not os.path.exists(path):
            return cls(None, recipe_ids)
        with open(path, "rb") as f:
            return cls(pickle.load(f), recipe_ids)

    def is_available(self, profile):
        """Usable only for a user whose ratings the factorisation has seen.

        A session user is not in the training matrix, so their factor vector
        does not exist.  One is folded in below from the items they have rated,
        which is only meaningful once there are several of them -- the same
        condition the switching threshold already tests.
        """
        if self.factors is None:
            return False
        known = sum(1 for r in profile.ratings
                    if r in self.factors["item_index"])
        return known >= SWITCH_THRESHOLD

    def _fold_in(self, profile):
        """A factor vector for a user the model was not trained on.

        Least squares against the item factors of the recipes they rated, which
        is the standard way to place a new user in an existing latent space
        without refitting the model.
        """
        f = self.factors
        rows, targets = [], []
        for rid, rating in profile.ratings.items():
            idx = f["item_index"].get(rid)
            if idx is not None:
                rows.append(f["qi"][idx])
                targets.append(rating - f["mu"] - f["bi"][idx])
        if not rows:
            return np.zeros(f["n_factors"]), 0.0
        Q = np.asarray(rows)
        y = np.asarray(targets)
        reg = 0.1 * np.eye(Q.shape[1])
        pu = np.linalg.solve(Q.T @ Q + reg, Q.T @ y)
        return pu, float(y.mean() - (Q @ pu).mean())

    def predicted_ratings(self, profile):
        """The model's rating prediction: mu + bu + bi + q.p, on the scale.

        This is the quantity Section 3.4.2 defines and the quantity the root
        mean squared error of Chapter 5 is computed over.  It is NOT what
        `scores` returns, and the difference is the subject of Section 5.3.
        """
        f = self.factors
        pu, bu = self._fold_in(profile)
        out = np.full(len(self.recipe_ids), f["mu"] + bu, dtype=np.float64)
        idx = np.array([f["item_index"].get(int(r), -1)
                        for r in self.recipe_ids])
        seen = idx >= 0
        known = idx[seen]
        out[seen] = f["mu"] + bu + f["bi"][known] + f["qi"][known] @ pu
        return np.clip(out, 1.0, 5.0)

    def scores(self, profile):
        """The ranking signal: the latent inner product alone.

        WHY THIS IS NOT THE PREDICTED RATING, which is the obvious thing to
        rank by and which this component used to return.

        A predicted rating is a sum of a global mean, a user bias, an item bias
        and the latent inner product.  Of those four, only the last two vary
        across items for a fixed user, so ranking by the prediction is ranking
        by `bi + q.p`.  The item bias is exactly right for predicting a rating
        -- it is how highly this recipe tends to be rated -- and on this corpus
        it is ruinous for ranking, because 76.9 per cent of recipes carry fewer
        than five ratings and 88.9 per cent of all ratings are four or five.
        A recipe rated once, at five stars, therefore acquires a large positive
        bias estimated from a single observation, and outranks every recipe the
        model actually knows something about.

        Measured over 2,000 held-out users, ranking by the full prediction gave
        an NDCG@10 of 0.0000 -- indistinguishable from random -- while the same
        model ranked by the latent term alone gave 0.0028.  The factorisation
        was never the problem; the bias term was.  Section 5.3 reports the
        measurement and how the defect was found.

        The user bias and the global mean are omitted for the same reason they
        do not matter: they are constant across items and cannot change an
        ordering.
        """
        f = self.factors
        pu, _ = self._fold_in(profile)
        out = np.zeros(len(self.recipe_ids), dtype=np.float64)
        idx = np.array([f["item_index"].get(int(r), -1)
                        for r in self.recipe_ids])
        seen = idx >= 0
        out[seen] = f["qi"][idx[seen]] @ pu
        return out


# ---------------------------------------------------------------------------
# Switching controller (§3.4.3)
# ---------------------------------------------------------------------------

class SwitchingController:
    """Selects one recommender per request on the size of the user's history.

    Switching, rather than blending, is the hybrid strategy adopted here: a
    single recommender is chosen per request according to a criterion evaluated
    at that moment.  The criterion is history size, and the threshold is
    SWITCH_THRESHOLD.
    """

    def __init__(self, content, collaborative=None, threshold=SWITCH_THRESHOLD):
        self.content = content
        self.collaborative = collaborative or CollaborativeRecommender()
        self.threshold = threshold

    def select(self, profile):
        """Return (recommender, an explanation fit to show the user)."""
        n = profile.n_interactions()
        if n >= self.threshold and self.collaborative.is_available(profile):
            return self.collaborative, (
                f"collaborative filtering ({n} interactions, "
                f"threshold {self.threshold})")
        if n >= self.threshold:
            return self.content, (
                f"content-based ({n} interactions reach the threshold of "
                f"{self.threshold}, but too few of the rated recipes appear in "
                f"the training matrix to place you in it)")
        return self.content, (
            f"content-based ({n} interactions, below the threshold of "
            f"{self.threshold})")

    def scores(self, profile):
        recommender, _ = self.select(profile)
        return recommender.scores(profile)


def train_and_store(out_path=None, **kwargs):
    """Fit the collaborative model on the cleaned interactions and store it."""
    with open(os.path.join(OUT, "interactions.pkl"), "rb") as f:
        inter = pickle.load(f)
    factors = train_matrix_factorisation(inter, **kwargs)
    out_path = out_path or os.path.join(OUT, "mf.pkl")
    with open(out_path, "wb") as f:
        pickle.dump(factors, f, protocol=pickle.HIGHEST_PROTOCOL)
    return factors


if __name__ == "__main__":
    t0 = time.time()
    with open(os.path.join(OUT, "corpus.pkl"), "rb") as f:
        corpus = pickle.load(f)
    print(f"loaded {len(corpus):,} recipes", flush=True)

    index = build_content_index(corpus)
    m, g = index["matrix"], index["ingr_matrix"]
    size = os.path.getsize(os.path.join(OUT, "content_index.pkl")) / 1e6
    print(f"term-document matrix : {m.shape[0]:,} x {m.shape[1]:,}, "
          f"{m.nnz:,} non-zeros")
    print(f"ingredient matrix    : {g.shape[0]:,} x {g.shape[1]:,}, "
          f"{g.nnz:,} non-zeros")
    print(f"wrote outputs/content_index.pkl ({size:.0f} MB) "
          f"in {time.time() - t0:.0f} s")

    # The heaviest terms are a quick sanity check on the weighting: if the idf
    # term is doing its job, the most distinctive ingredients of an arbitrary
    # recipe should be the ones a person would name when describing it.
    inv = {v: k for k, v in index["vocabulary"].items()}
    row = m[0].toarray().ravel()
    top = np.argsort(row)[::-1][:8]
    print(f"\nheaviest terms for '{corpus['name'].iloc[0]}':")
    print("  " + ", ".join(f"{inv[i]} ({row[i]:.2f})" for i in top if row[i] > 0))

    print("\ntraining the collaborative component ...", flush=True)
    t1 = time.time()
    factors = train_and_store()
    print(f"  {factors['n_train']:,} training and {factors['n_val']:,} "
          f"validation ratings, {factors['n_factors']} factors")
    print("  validation RMSE by epoch: "
          + ", ".join(f"{r:.4f}" for r in factors["rmse_history"]))
    print(f"  final validation RMSE: {factors['val_rmse']:.4f}")
    print(f"  trained in {time.time() - t1:.0f} s; wrote outputs/mf.pkl")
