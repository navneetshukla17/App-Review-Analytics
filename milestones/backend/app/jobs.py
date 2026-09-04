import threading
from dataclasses import dataclass, field

from .db import Database
from .scrapers.search import SCRAPERS
from .sentiment import score_review


@dataclass
class JobState:
    id: int
    app_id: int
    status: str = "running"
    fetched_count: int = 0
    message: str = ""
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "id": self.id,
                "app_id": self.app_id,
                "status": self.status,
                "fetched_count": self.fetched_count,
                "message": self.message,
            }


class JobRegistry:
    def __init__(self):
        self._jobs: dict[int, JobState] = {}
        self._lock = threading.Lock()

    def create(self, job_id: int, app_id: int) -> JobState:
        state = JobState(id=job_id, app_id=app_id)
        with self._lock:
            self._jobs[job_id] = state
        return state

    def get(self, job_id: int) -> JobState | None:
        with self._lock:
            return self._jobs.get(job_id)

    def update(self, job_id: int, status: str = None, fetched_count: int = None,
               message: str = None) -> None:
        state = self.get(job_id)
        if state is None:
            return
        with state._lock:
            if status is not None:
                state.status = status
            if fetched_count is not None:
                state.fetched_count = fetched_count
            if message is not None:
                state.message = message


def run_fetch_job(db: Database, registry: JobRegistry, job_id: int, limit: int = None, scrapers=None) -> None:
    """Background worker: page through reviews, upsert into DB, update progress."""
    scrapers = scrapers or SCRAPERS
    job_row = db.get_job(job_id)
    if job_row is None:
        return
    app_row = db.get_app(job_row["app_id"])
    if app_row is None:
        db.finish_job(job_id, "failed", 0, "App row not found")
        return
    scraper = scrapers[job_row["platform"]]
    total = 0
    try:
        for batch in scraper.review_batches(app_row["store_app_id"], country="in"):
            rows = []
            for item in batch:
                polarity, label = score_review(item.body)
                rows.append((
                    app_row["id"], item.review_id, item.title, item.body, item.rating,
                    item.author, item.author_url, item.version, "in", item.created_at,
                    polarity, label,
                ))
            db.insert_reviews(rows)
            total += len(batch)
            registry.update(job_id, fetched_count=total)
            
            # Stop if limit reached
            if limit and total >= limit:
                break
        db.finish_job(job_id, "completed", total)
        registry.update(job_id, status="completed")
    except Exception as exc:  # noqa: BLE001 - surface any fetch failure to the job
        db.finish_job(job_id, "failed", total, message=str(exc))
        registry.update(job_id, status="failed", message=str(exc))
