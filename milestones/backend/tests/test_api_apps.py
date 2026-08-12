from app.scrapers.base import AppCandidate


def test_search_endpoint(client, monkeypatch):
    def fake_search(query, platform, limit=20):
        return [AppCandidate(
            platform="playstore", store_app_id="com.spotify.music",
            name="Spotify", developer="Spotify AB",
        )], []

    monkeypatch.setattr("app.routers.apps.search_apps", fake_search)
    resp = client.get("/api/apps/search", params={"q": "spotify", "platform": "both"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["results"][0]["name"] == "Spotify"
    assert body["errors"] == []


def test_search_endpoint_bad_request(client):
    resp = client.get("/api/apps/search", params={"q": "spotify", "platform": "bogus"})
    assert resp.status_code == 400


def test_create_and_list_apps(client, db):
    resp = client.post("/api/apps", json={
        "name": "Spotify", "platform": "playstore",
        "store_app_id": "com.spotify.music", "developer": "Spotify AB",
    })
    assert resp.status_code == 200
    app_id = resp.json()["id"]
    assert db.get_app(app_id)["name"] == "Spotify"

    resp = client.get("/api/apps")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_create_app_validation_error(client):
    resp = client.post("/api/apps", json={
        "name": "Spotify", "platform": "bogus", "store_app_id": "x",
    })
    assert resp.status_code in (400, 422)
