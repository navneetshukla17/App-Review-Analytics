from app.db import Database


def test_create_app_and_get(db):
    app_id = db.create_app("Instagram", "playstore", "com.instagram.android", "Instagram", "http://icon")
    row = db.get_app(app_id)
    assert row["name"] == "Instagram"
    assert row["platform"] == "playstore"
    assert row["store_app_id"] == "com.instagram.android"


def test_create_app_unique_per_platform(db):
    db.create_app("Instagram", "playstore", "com.instagram.android", "Instagram", None)
    db.create_app("Instagram", "appstore", "389801252", "Instagram, Inc.", None)
    assert len(db.list_apps()) == 2


def test_create_app_idempotent(db):
    a = db.create_app("Instagram", "playstore", "com.instagram.android", "Instagram", None)
    b = db.create_app("Instagram", "playstore", "com.instagram.android", "Instagram", None)
    assert a == b
    assert len(db.list_apps()) == 1


def test_insert_reviews_dedupes(db):
    app_id = db.create_app("Instagram", "playstore", "com.instagram.android", "Instagram", None)
    rows = [
        (app_id, "r1", "", "Great app", 5, "alice", None, None, "in", "2024-01-01T10:00:00", 0.8, "positive"),
        (app_id, "r1", "", "Great app", 5, "alice", None, None, "in", "2024-01-01T10:00:00", 0.8, "positive"),
    ]
    db.insert_reviews(rows)
    assert db.count_reviews(app_id) == 1


def test_query_reviews_filters(db):
    app_id = db.create_app("Spotify", "playstore", "com.spotify.music", "Spotify", None)
    db.insert_reviews([
        (app_id, "1", "", "crashes all the time", 1, "a", None, None, "in", "2024-01-01", -0.6, "negative"),
        (app_id, "2", "", "love the music", 5, "b", None, None, "in", "2024-02-01", 0.7, "positive"),
        (app_id, "3", "", "its ok", 3, "c", None, None, "in", "2024-03-01", 0.0, "neutral"),
    ])
    q = db.query_reviews(app_id, q="crash")
    assert len(q) == 1 and q[0]["review_id"] == "1"
    q = db.query_reviews(app_id, min_rating=4)
    assert len(q) == 1 and q[0]["review_id"] == "2"
    q = db.query_reviews(app_id, sentiment="neutral")
    assert len(q) == 1 and q[0]["review_id"] == "3"


def test_stats(db):
    app_id = db.create_app("Spotify", "playstore", "com.spotify.music", "Spotify", None)
    db.insert_reviews([
        (app_id, "1", "", "crashes", 1, "a", None, None, "in", "2024-01-05", -0.6, "negative"),
        (app_id, "2", "", "great", 5, "b", None, None, "in", "2024-01-20", 0.7, "positive"),
        (app_id, "3", "", "ok", 3, "c", None, None, "in", "2024-02-10", 0.0, "neutral"),
    ])
    stats = db.get_stats(app_id)
    assert stats["total_reviews"] == 3
    assert round(stats["avg_rating"], 2) == 3.0
    assert len(stats["rating_distribution"]) == 3
    assert len(stats["sentiment_breakdown"]) == 3
    assert len(stats["volume_over_time"]) == 2
