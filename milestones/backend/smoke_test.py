"""Manual live smoke test - verifies real scraping works.

Usage: .venv/bin/python smoke_test.py "Instagram"
"""
import sys
import time

from app.db import Database
from app.jobs import JobRegistry, run_fetch_job
from app.scrapers.search import search_apps


def main(query: str):
    db = Database("smoke_reviews.db")
    registry = JobRegistry()
    for platform in ("playstore", "appstore"):
        print(f"== Searching {platform} for {query!r}")
        results, errors = search_apps(query, platform, limit=3)
        if errors:
            print("  errors:", errors)
        if not results:
            print("  no results; skipping")
            continue
        candidate = results[0]
        print(f"  picked: {candidate.name} ({candidate.store_app_id})")
        app_id = db.create_app(candidate.name, candidate.platform,
                               candidate.store_app_id, candidate.developer,
                               candidate.icon_url)
        job_id = db.create_job(app_id, platform)
        state = registry.create(job_id, app_id)
        start = time.time()
        run_fetch_job(db, registry, job_id)
        elapsed = round(time.time() - start, 1)
        print(f"  job: {state.status} - {state.fetched_count} reviews in {elapsed}s")
        print(f"  total stored: {db.count_reviews(app_id)}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "Instagram")
