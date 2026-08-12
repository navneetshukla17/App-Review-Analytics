from app.sentiment import score_review


def test_positive():
    score, label = score_review("This app is fantastic, I love it!")
    assert label == "positive"
    assert score > 0.05


def test_negative():
    score, label = score_review("Terrible, it crashes every time.")
    assert label == "negative"
    assert score < -0.05


def test_neutral():
    score, label = score_review("It is an app.")
    assert label == "neutral"


def test_empty_text():
    score, label = score_review("")
    assert label == "neutral"
