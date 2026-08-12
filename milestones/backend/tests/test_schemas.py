from app.schemas import AppCreate, JobOut, ReviewPage


def test_app_create_valid():
    body = {"name": "Spotify", "platform": "playstore",
            "store_app_id": "com.spotify.music", "developer": "Spotify AB"}
    app = AppCreate(**body)
    assert app.name == "Spotify"
    assert app.developer == "Spotify AB"


def test_app_create_rejects_bad_platform():
    try:
        AppCreate(name="x", platform="bogus", store_app_id="y")
        assert False, "should have raised"
    except ValueError:
        pass


def test_review_page_and_job_serialize():
    page = ReviewPage(total=0, page=1, page_size=50, items=[])
    assert page.total == 0
    job = JobOut(id=1, app_id=2, status="running", fetched_count=5)
    assert job.model_dump()["fetched_count"] == 5
