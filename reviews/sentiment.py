import os
import re
import pickle
import logging

import pandas as pd
from django.conf import settings

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score


logger = logging.getLogger(__name__)




def preprocess_text(text):
    

    if not text:
        return ""

    # Remove HTML tags
    text = re.sub(r"<[^>]+>", " ", str(text))

    # Convert to lowercase
    text = text.lower()

    # Remove apostrophe
    text = text.replace("'", "")

    # Remove other special characters
    text = re.sub(r"[^a-z\s]", " ", text)

    # Remove extra spaces
    text = re.sub(r"\s+", " ", text).strip()

    return text



_sentiment_cache = {
    "model": None,
    "vectorizer": None,
}


def load_sentiment_model():
    

    global _sentiment_cache

    if (
        _sentiment_cache["model"] is not None
        and _sentiment_cache["vectorizer"] is not None
    ):
        return (
            _sentiment_cache["model"],
            _sentiment_cache["vectorizer"],
        )

    model_path = settings.SENTIMENT_MODEL_PATH
    vectorizer_path = settings.SENTIMENT_VECTORIZER_PATH

    if not os.path.exists(model_path):
        logger.warning("Sentiment model not found: %s", model_path)
        return None, None

    if not os.path.exists(vectorizer_path):
        logger.warning("Sentiment vectorizer not found: %s", vectorizer_path)
        return None, None

    try:
        with open(model_path, "rb") as f:
            model = pickle.load(f)

        with open(vectorizer_path, "rb") as f:
            vectorizer = pickle.load(f)

        _sentiment_cache["model"] = model
        _sentiment_cache["vectorizer"] = vectorizer

        return model, vectorizer

    except Exception as e:
        logger.exception("Error loading sentiment model: %s", e)
        return None, None



def is_neutral_review(text):
    

    text = preprocess_text(text)

    
    not_watched_patterns = [

        # NOT WATCHED
        r"\bdont watch\b",
        r"\bdo not watch\b",
        r"\bdidnt watch\b",
        r"\bdid not watch\b",
        r"\bhavent watched\b",
        r"\bhave not watched\b",
        r"\bnever watched\b",
        r"\bnever watch\b",
        r"\bnot watched\b",
        r"\bnot watch\b",

        # NOT SEEN
        r"\bdont see\b",
        r"\bdo not see\b",
        r"\bdidnt see\b",
        r"\bdid not see\b",
        r"\bhavent seen\b",
        r"\bhave not seen\b",
        r"\bnever saw\b",
        r"\bnever seen\b",
        r"\bnot seen\b",
        r"\bnot see\b",
    ]

    for pattern in not_watched_patterns:
        if re.search(pattern, text):
            return True

    

    neutral_patterns = [
        r"\bi dont know\b",
        r"\bi do not know\b",
        r"\bnot sure\b",
        r"\bi am not sure\b",
        r"\bim not sure\b",
        r"\bunsure\b",
        r"\bcannot say\b",
        r"\bcan not say\b",
        r"\bno opinion\b",
        r"\bno clear opinion\b",
        r"\bmaybe\b",
        r"\bperhaps\b",
        r"\bnot decided\b",
    ]

    for pattern in neutral_patterns:
        if re.search(pattern, text):
            return True

    return False


# Word weights: strong words = 2, mild words = 1
POSITIVE_WORDS = {
    "amazing": 2,
    "awesome": 2,
    "excellent": 2,
    "fantastic": 2,
    "great": 2,
    "love": 2,
    "loved": 2,
    "wonderful": 2,
    "best": 2,
    "brilliant": 2,
    "perfect": 2,
    "beautiful": 2,
    "masterpiece": 2,
    "outstanding": 2,
    "superb": 2,
    "good": 1,
    "nice": 1,
    "lovely": 1,
    "enjoyed": 1,
    "enjoyable": 1,
    "entertaining": 1,
    "fun": 1,
    "interesting": 1,
    "liked": 1,
}


NEGATIVE_WORDS = {
    "terrible": 2,
    "awful": 2,
    "horrible": 2,
    "worst": 2,
    "hate": 2,
    "hated": 2,
    "waste": 2,
    "stupid": 2,
    "ridiculous": 2,
    "useless": 2,
    "pathetic": 2,
    "bad": 1,
    "boring": 1,
    "weak": 1,
    "disappointing": 1,
    "disappointed": 1,
    "poor": 1,
    "annoying": 1,
    "dull": 1,
    "slow": 1,
}


# Words that make a review lukewarm / mixed
HEDGE_WORDS = {
    "okay",
    "ok",
    "fine",
    "average",
    "decent",
    "alright",
    "mediocre",
    "some",
    "somewhat",
    "partly",
    "mixed",
    "watchable",
    "ordinary",
}

HEDGE_PATTERNS = [
    r"\bso so\b",
    r"\bnot bad\b",
    r"\bnot great\b",
    r"\bnothing special\b",
    r"\bcould have been better\b",
    r"\bone time watch\b",
]

NEGATORS = {
    "not", "no", "never", "dont", "didnt", "doesnt", "isnt", "wasnt",
    "werent", "arent", "cant", "couldnt", "wont", "wouldnt", "hardly",
}


NB_CONFIDENCE_THRESHOLD = 0.70


def _lexicon_score(text):
    

    tokens = text.split()
    score = 0
    hits = 0
    hedges = sum(1 for t in tokens if t in HEDGE_WORDS)
    hedges += sum(1 for p in HEDGE_PATTERNS if re.search(p, text))

    for i, token in enumerate(tokens):
        if token in POSITIVE_WORDS:
            weight = POSITIVE_WORDS[token]
        elif token in NEGATIVE_WORDS:
            weight = -NEGATIVE_WORDS[token]
        else:
            continue

        hits += 1

        # Negation in the previous two words: "not good", "wasnt very good"
        if any(t in NEGATORS for t in tokens[max(0, i - 2):i]):
            if weight > 0:
                weight = -1        
            else:
                weight = 0          

        score += weight

    return score, hits, hedges


def _lexicon_label(text):
   

    score, hits, hedges = _lexicon_score(text)

    # Lukewarm words + only weak sentiment -> neutral
    # e.g. "The movie was okay and had some interesting scenes."
    if hedges and abs(score) < 2:
        return "neutral"

    if hits == 0:
        return None

    if score > 0:
        return "positive"
    if score < 0:
        return "negative"

    # Positive and negative cancel out -> mixed review
    return "neutral"


def analyze_sentiment(text):
    

    if not text or not str(text).strip():
        return "neutral"

    cleaned_text = preprocess_text(text)

    if not cleaned_text:
        return "neutral"

    if is_neutral_review(cleaned_text):
        return "neutral"

    label = _lexicon_label(cleaned_text)
    if label is not None:
        return label

    model, vectorizer = load_sentiment_model()

    if model is not None and vectorizer is not None:

        try:
            vectorized_text = vectorizer.transform([cleaned_text])

            # No known vocabulary at all -> model would only guess
            if vectorized_text.nnz == 0:
                return "neutral"

            probabilities = model.predict_proba(vectorized_text)[0]
            best = probabilities.argmax()

            if probabilities[best] < NB_CONFIDENCE_THRESHOLD:
                return "neutral"

            prediction = str(model.classes_[best]).lower().strip()

            if prediction in ["positive", "negative", "neutral"]:
                return prediction

        except Exception as e:
            logger.warning(
                "Naive Bayes sentiment prediction failed: %s",
                e
            )

    return _heuristic_sentiment(cleaned_text)


def _heuristic_sentiment(text):
    """
    Simple fallback sentiment detection.

    Used when the trained Naive Bayes model
    is unavailable or prediction fails.
    """

    if is_neutral_review(text):
        return "neutral"

    return _lexicon_label(preprocess_text(text)) or "neutral"



def train_sentiment_model(
    dataset_path=None,
    test_size=0.2,
    random_state=42,
):
    

    

    if dataset_path is None:
        dataset_path = os.path.join(
            settings.BASE_DIR,
            "datasets",
            "imdb_reviews.csv",
        )

    logger.info("Loading sentiment dataset: %s", dataset_path)

    

    df = pd.read_csv(dataset_path)

    


    required_columns = {"review", "sentiment"}

    if not required_columns.issubset(df.columns):
        raise ValueError(
            "Dataset must contain 'review' and 'sentiment' columns."
        )

    

    df = df.dropna(subset=["review", "sentiment"])

    
    df["review"] = df["review"].astype(str).apply(preprocess_text)

   
    df["sentiment"] = (
        df["sentiment"]
        .astype(str)
        .str.lower()
        .str.strip()
    )

    

    df = df[df["sentiment"].isin(["positive", "negative"])]

    if len(df) == 0:
        raise ValueError(
            "No valid positive/negative sentiment data found."
        )

    logger.info(
        "Training sentiment model on %s samples",
        len(df)
    )



    X = df["review"]
    y = df["sentiment"]

    

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=test_size,
        random_state=random_state,
        stratify=y,
    )



    vectorizer = CountVectorizer(
        max_features=20000,
        stop_words="english",
        ngram_range=(1, 2),
    )

    X_train_vectorized = vectorizer.fit_transform(X_train)

    X_test_vectorized = vectorizer.transform(X_test)

    

    model = MultinomialNB(
        alpha=0.5
    )

    model.fit(
        X_train_vectorized,
        y_train,
    )

    
    predictions = model.predict(
        X_test_vectorized
    )

    accuracy = accuracy_score(
        y_test,
        predictions,
    )

    logger.info(
        "Sentiment model accuracy: %.4f",
        accuracy
    )

    
    model_path = settings.SENTIMENT_MODEL_PATH

    vectorizer_path = settings.SENTIMENT_VECTORIZER_PATH

    
    os.makedirs(
        os.path.dirname(model_path),
        exist_ok=True,
    )

    os.makedirs(
        os.path.dirname(vectorizer_path),
        exist_ok=True,
    )

    

    with open(model_path, "wb") as f:
        pickle.dump(model, f)

    
    with open(vectorizer_path, "wb") as f:
        pickle.dump(vectorizer, f)

    

    _sentiment_cache["model"] = model

    _sentiment_cache["vectorizer"] = vectorizer

    logger.info(
        "Sentiment model saved successfully."
    )

    return {
        "accuracy": accuracy,
        "samples": len(df),
        "model_path": model_path,
        "vectorizer_path": vectorizer_path,
    }