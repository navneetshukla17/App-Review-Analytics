def _seed(client):
    resp = client.post("/api/apps", json={
        "name": "Spotify", "platform": "playstore",
        "store_app_id": "com.spotify.music", "developer": "Spotify AB",
    })
    app_id = resp.json()["id"]
    db = client.app.state.db
    db.insert_reviews([
        (app_id, "1", "", "crashes all the time", 1, "a", None, None, "in",
         "2024-01-05", -0.6, "negative"),
        (app_id, "2", "", "love the music", 5, "b", None, None, "in",
         "2024-02-01", 0.7, "positive"),
        (app_id, "3", "", "its ok", 3, "c", None, None, "in",
         "2024-03-01", 0.0, "neutral"),
    ])
    return app_id


def test_reviews_pagination_and_filter(client):
    app_id = _seed(client)
    resp = client.get(f"/api/apps/{app_id}/reviews", params={"q": "crash"})
    body = resp.json()
    assert resp.status_code == 200
    assert body["total"] == 1
    assert body["items"][0]["review_id"] == "1"

    resp = client.get(f"/api/apps/{app_id}/reviews", params={"page": 1, "page_size": 2})
    assert resp.json()["items"][0]["review_id"] == "3"


def test_reviews_missing_app_404(client):
    resp = client.get("/api/apps/999/reviews")
    assert resp.status_code == 404


def test_stats(client):
    app_id = _seed(client)
    resp = client.get(f"/api/apps/{app_id}/stats")
    body = resp.json()
    assert resp.status_code == 200
    assert body["total_reviews"] == 3
    assert len(body["rating_distribution"]) == 3
    assert len(body["volume_over_time"]) == 3


def test_export_csv(client):
    app_id = _seed(client)
    resp = client.get(f"/api/apps/{app_id}/export", params={"format": "csv"})
    assert resp.status_code == 200
    text = resp.text
    assert "crashes all the time" in text
    assert "review_id,rating" in text


def test_export_json(client):
    app_id = _seed(client)
    resp = client.get(f"/api/apps/{app_id}/export", params={"format": "json"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 3
    assert data[0]["body"] == "its ok"
