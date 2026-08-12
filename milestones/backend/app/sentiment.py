from textblob import TextBlob

POSITIVE_THRESHOLD = 0.05
NEGATIVE_THRESHOLD = -0.05


def score_review(text: str) -> tuple[float, str]:
    polarity = TextBlob(text or "").sentiment.polarity
    if polarity > POSITIVE_THRESHOLD:
        label = "positive"
    elif polarity < NEGATIVE_THRESHOLD:
        label = "negative"
    else:
        label = "neutral"
    return polarity, label
