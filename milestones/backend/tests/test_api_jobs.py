def test_start_fetch_returns_job(client, db, monkeypatch):
    monkeypatch.setattr("app.routers.jobs.run_fetch_job", lambda *a, **k: None)
    resp = client.post("/api/apps", json={
        "name": "Spotify", "platform": "playstore",
        "store_app_id": "com.spotify.music", "developer": "Spotify AB",
    })
    app_id = resp.json()["id"]
    resp = client.post(f"/api/apps/{app_id}/fetch")
    assert resp.status_code == 200
    body = resp.json()
    assert "id" in body
    assert body["status"] == "running"


def test_start_fetch_missing_app_404(client):
    resp = client.post("/api/apps/999/fetch")
    assert resp.status_code == 404


def test_job_progress_roundtrip(client, registry):
    state = registry.create(42, 1)
    registry.update(42, status="completed", fetched_count=150)
    resp = client.get("/api/jobs/42")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "completed"
    assert body["fetched_count"] == 150
    assert body["id"] == 42


def test_job_progress_missing_404(client):
    resp = client.get("/api/jobs/999")
    assert resp.status_code == 404
