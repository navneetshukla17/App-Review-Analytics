from datetime import datetime

from app.jobs import JobRegistry, run_fetch_job
from app.scrapers.base import ReviewItem


class FakeScraper:
    platform = "playstore"

    def review_batches(self, app_id, country="in"):
        yield [
            ReviewItem("r1", "", "love it", 5, "alice", None, "1.0",
                       datetime(2024, 1, 1).isoformat()),
        ]
        yield [
            ReviewItem("r2", "", "meh", 3, "bob", None, "1.0",
                       datetime(2024, 1, 2).isoformat()),
        ]


def test_run_fetch_job_inserts_and_completes(db, registry):
    app_id = db.create_app("Instagram", "playstore", "com.instagram.android", "Instagram", None)
    job_id = db.create_job(app_id, "playstore")
    state = registry.create(job_id, app_id)
    run_fetch_job(db, registry, job_id, scrapers={"playstore": FakeScraper()})
    assert db.count_reviews(app_id) == 2
    assert state.status == "completed"
    assert state.fetched_count == 2
    row = db.get_job(job_id)
    assert row["status"] == "completed"
    assert row["fetched_count"] == 2


def test_run_fetch_job_records_failure(db, registry):
    class BoomScraper:
        platform = "playstore"

        def review_batches(self, app_id, country="in"):
            raise RuntimeError("rate limited")

    app_id = db.create_app("Instagram", "playstore", "com.instagram.android", "Instagram", None)
    job_id = db.create_job(app_id, "playstore")
    state = registry.create(job_id, app_id)
    run_fetch_job(db, registry, job_id, scrapers={"playstore": BoomScraper()})
    assert state.status == "failed"
    assert "rate limited" in state.message
    assert db.get_job(job_id)["status"] == "failed"


def test_registry_roundtrip(registry):
    state = registry.create(7, 3)
    assert registry.get(7) is state
    registry.update(7, fetched_count=10)
    assert registry.get(7).fetched_count == 10
    assert registry.get(999) is None
