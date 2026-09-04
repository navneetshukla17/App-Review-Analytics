from datetime import datetime

from app.scrapers.base import AppCandidate, ReviewItem
from app.scrapers.playstore import PlayStoreScraper


def test_search_maps_results(monkeypatch):
    fake = [
        {"appId": "com.spotify.music", "title": "Spotify", "developer": "Spotify AB",
         "icon": "http://icon", "score": 4.3},
        {"appId": "com.spotify.lite", "title": "Spotify Lite", "developer": "Spotify AB",
         "icon": "http://icon2", "score": 4.0},
    ]
    monkeypatch.setattr("app.scrapers.playstore.gp_search", lambda *a, **k: fake)
    results = PlayStoreScraper().search("spotify")
    assert results[0] == AppCandidate("playstore", "com.spotify.music", "Spotify", "Spotify AB",
                                      "http://icon", 4.3)
    assert len(results) == 2


def test_review_batches_maps_reviews(monkeypatch):
    def fake_reviews(app_id, **kwargs):
        return [
            {"reviewId": "r1", "content": "nice", "score": 5, "userName": "alice",
             "userImage": "http://img", "reviewCreatedVersion": "1.0",
             "at": datetime(2024, 5, 1, 10, 0)},
        ], None

    monkeypatch.setattr("app.scrapers.playstore.gp_reviews", fake_reviews)
    batches = list(PlayStoreScraper().review_batches("com.spotify.music"))
    assert len(batches) >= 1
    item = batches[0][0]
    assert isinstance(item, ReviewItem)
    assert item.review_id == "r1"
    assert item.body == "nice"
    assert item.rating == 5
    assert item.author == "alice"
    assert item.version == "1.0"
    assert item.created_at == "2024-05-01T10:00:00"


def test_review_batches_stops_without_token(monkeypatch):
    calls = {"n": 0}

    def fake_reviews(app_id, **kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            return [{"reviewId": "r1", "content": "a", "score": 5, "userName": "u",
                     "at": datetime(2024, 1, 1)}], "token"
        return [], None

    monkeypatch.setattr("app.scrapers.playstore.gp_reviews", fake_reviews)
    batches = list(PlayStoreScraper().review_batches("com.x"))
    assert calls["n"] >= 2
    assert len(batches) >= 1
