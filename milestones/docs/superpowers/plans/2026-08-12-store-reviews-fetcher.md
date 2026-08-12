# Store Reviews Fetcher Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A web app (FastAPI + React) where you enter an app name + platform (playstore/appstore/both), pick the right app, and fetch all its reviews (India locale) into SQLite — then search, filter, chart, sentiment-analyze, and export them.

**Architecture:** FastAPI backend with SQLite persistence; `google-play-scraper` and `app-store-scraper` wrapped behind a thin `PlatformScraper` abstraction. Fetches run in background threads with a thread-safe job registry so the UI can poll progress. React (Vite) frontend with two pages: Search & Fetch, and Dashboard (charts via Recharts).

**Tech Stack:** Python 3.13, FastAPI, SQLite, `google-play-scraper`, `app-store-scraper`, TextBlob, pytest; React 18, Vite, react-router-dom, Recharts, vitest.

**Repo note:** The git root is `/Users/tusharshukla` (the home dir). Run all git commands from `milestones/`; staged paths resolve under `milestones/`. A `.gitignore` in `milestones/` keeps commits clean.

---

### Task 1: Backend scaffolding and dependencies

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/requirements-dev.txt`
- Create: `backend/.gitignore`
- Create: `backend/app/__init__.py`
- Create: `backend/app/scrapers/__init__.py`
- Create: `backend/app/routers/__init__.py`
- Create: `.gitignore`

- [ ] **Step 1: Write `.gitignore` at `milestones/.gitignore`**

```gitignore
__pycache__/
*.pyc
.venv/
node_modules/
dist/
backend/review_data.db
.DS_Store
```

- [ ] **Step 2: Write `backend/requirements.txt`**

```txt
fastapi==0.115.12
uvicorn[standard]==0.34.0
google-play-scraper==1.1.1
app-store-scraper==0.3.5
textblob==0.18.0.post0
requests==2.32.3
```

- [ ] **Step 3: Write `backend/requirements-dev.txt`**

```txt
-r requirements.txt
pytest==8.3.4
httpx==0.28.1
```

- [ ] **Step 4: Create the package init files (empty)**

Create empty files: `backend/app/__init__.py`, `backend/app/scrapers/__init__.py`, `backend/app/routers/__init__.py`.

- [ ] **Step 5: Write `backend/.gitignore`**

```gitignore
review_data.db
```

- [ ] **Step 6: Set up virtualenv and install**

```bash
cd backend && python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements-dev.txt
```

Expected: installs complete without errors.

- [ ] **Step 7: Verify packages import**

```bash
.venv/bin/python -c "import fastapi, google_play_scraper, app_store_scraper, textblob, pytest; print('ok')"
```

Expected: prints `ok`.

- [ ] **Step 8: Commit**

```bash
git add .gitignore backend/.gitignore backend/requirements.txt backend/requirements-dev.txt backend/app/__init__.py backend/app/scrapers/__init__.py backend/app/routers/__init__.py
git commit -m "chore: scaffold backend project"
```

---

### Task 2: Database layer

**Files:**
- Create: `backend/app/db.py`
- Test: `backend/tests/conftest.py`
- Test: `backend/tests/test_db.py`

- [ ] **Step 1: Write the failing tests**

`backend/tests/conftest.py`:

```python
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db import Database


@pytest.fixture
def db(tmp_path):
    database = Database(tmp_path / "test.db")
    yield database
    database.close()


@pytest.fixture
def registry():
    from app.jobs import JobRegistry

    return JobRegistry()


@pytest.fixture
def client(db, registry):
    from fastapi.testclient import TestClient
    from app.main import create_app

    app = create_app(db, registry)
    return TestClient(app)
```

`backend/tests/test_db.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
.venv/bin/pytest tests/test_db.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'app.db'`.

- [ ] **Step 3: Write `backend/app/db.py`**

```python
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Optional

SCHEMA = """
CREATE TABLE IF NOT EXISTS apps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    platform TEXT NOT NULL,
    store_app_id TEXT NOT NULL,
    developer TEXT,
    icon_url TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(platform, store_app_id)
);

CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    app_id INTEGER NOT NULL REFERENCES apps(id),
    review_id TEXT,
    title TEXT,
    body TEXT,
    rating INTEGER,
    author TEXT,
    author_url TEXT,
    version TEXT,
    country TEXT,
    created_at TEXT,
    fetched_at TEXT NOT NULL DEFAULT (datetime('now')),
    sentiment_score REAL,
    sentiment_label TEXT,
    UNIQUE(app_id, review_id)
);

CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    app_id INTEGER NOT NULL REFERENCES apps(id),
    platform TEXT NOT NULL,
    status TEXT NOT NULL,
    total_target INTEGER,
    fetched_count INTEGER NOT NULL DEFAULT 0,
    message TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_reviews_app ON reviews(app_id);
CREATE INDEX IF NOT EXISTS idx_reviews_app_rating ON reviews(app_id, rating);
CREATE INDEX IF NOT EXISTS idx_reviews_app_sentiment ON reviews(app_id, sentiment_label);
CREATE INDEX IF NOT EXISTS idx_jobs_app ON jobs(app_id);
"""


class Database:
    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init()

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    @contextmanager
    def _cursor(self):
        conn = self.connect()
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def close(self) -> None:
        pass

    def init(self) -> None:
        with self._cursor() as conn:
            conn.executescript(SCHEMA)

    # ---- apps ----

    def create_app(self, name, platform, store_app_id, developer=None, icon_url=None) -> int:
        with self._cursor() as conn:
            conn.execute(
                "INSERT INTO apps(name, platform, store_app_id, developer, icon_url) "
                "VALUES (?,?,?,?,?) "
                "ON CONFLICT(platform, store_app_id) DO NOTHING",
                (name, platform, store_app_id, developer, icon_url),
            )
            row = conn.execute(
                "SELECT id FROM apps WHERE platform = ? AND store_app_id = ?",
                (platform, store_app_id),
            ).fetchone()
            return row["id"]

    def get_app(self, app_id: int) -> Optional[sqlite3.Row]:
        with self._cursor() as conn:
            return conn.execute("SELECT * FROM apps WHERE id = ?", (app_id,)).fetchone()

    def list_apps(self) -> list[sqlite3.Row]:
        with self._cursor() as conn:
            return conn.execute("SELECT * FROM apps ORDER BY created_at DESC").fetchall()

    # ---- reviews ----

    def insert_reviews(self, rows: list[tuple]) -> None:
        with self._cursor() as conn:
            conn.executemany(
                """INSERT OR IGNORE INTO reviews
                   (app_id, review_id, title, body, rating, author, author_url,
                    version, country, created_at, sentiment_score, sentiment_label)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                rows,
            )

    def count_reviews(self, app_id: int) -> int:
        with self._cursor() as conn:
            return conn.execute(
                "SELECT COUNT(*) AS c FROM reviews WHERE app_id = ?", (app_id,)
            ).fetchone()["c"]

    def query_reviews(self, app_id: int, q: str = None, rating: int = None,
                      min_rating: int = None, sentiment: str = None,
                      start_date: str = None, end_date: str = None,
                      page: int = None, page_size: int = 50) -> list[sqlite3.Row]:
        where, params = ["app_id = ?"], [app_id]
        if q:
            like = f"%{q}%"
            where.append("(body LIKE ? OR title LIKE ?)")
            params += [like, like]
        if rating is not None:
            where.append("rating = ?")
            params.append(rating)
        if min_rating is not None:
            where.append("rating >= ?")
            params.append(min_rating)
        if sentiment:
            where.append("sentiment_label = ?")
            params.append(sentiment)
        if start_date:
            where.append("created_at >= ?")
            params.append(start_date)
        if end_date:
            where.append("created_at <= ?")
            params.append(end_date)
        sql = f"SELECT * FROM reviews WHERE {' AND '.join(where)} ORDER BY created_at DESC"
        if page is not None:
            sql += " LIMIT ? OFFSET ?"
            params += [page_size, (page - 1) * page_size]
        with self._cursor() as conn:
            return conn.execute(sql, params).fetchall()

    def count_matching(self, app_id: int, q: str = None, rating: int = None,
                       min_rating: int = None, sentiment: str = None,
                       start_date: str = None, end_date: str = None) -> int:
        where, params = ["app_id = ?"], [app_id]
        if q:
            like = f"%{q}%"
            where.append("(body LIKE ? OR title LIKE ?)")
            params += [like, like]
        if rating is not None:
            where.append("rating = ?")
            params.append(rating)
        if min_rating is not None:
            where.append("rating >= ?")
            params.append(min_rating)
        if sentiment:
            where.append("sentiment_label = ?")
            params.append(sentiment)
        if start_date:
            where.append("created_at >= ?")
            params.append(start_date)
        if end_date:
            where.append("created_at <= ?")
            params.append(end_date)
        with self._cursor() as conn:
            return conn.execute(
                f"SELECT COUNT(*) AS c FROM reviews WHERE {' AND '.join(where)}", params
            ).fetchone()["c"]

    def get_stats(self, app_id: int) -> dict[str, Any]:
        with self._cursor() as conn:
            agg = conn.execute(
                "SELECT COUNT(*) AS total, AVG(rating) AS avg FROM reviews WHERE app_id = ?",
                (app_id,),
            ).fetchone()
            dist = conn.execute(
                "SELECT rating, COUNT(*) AS count FROM reviews WHERE app_id = ? "
                "GROUP BY rating ORDER BY rating",
                (app_id,),
            ).fetchall()
            senti = conn.execute(
                "SELECT sentiment_label AS label, COUNT(*) AS count FROM reviews WHERE app_id = ? "
                "GROUP BY sentiment_label ORDER BY count DESC",
                (app_id,),
            ).fetchall()
            volume = conn.execute(
                "SELECT substr(created_at, 1, 7) AS month, COUNT(*) AS count FROM reviews "
                "WHERE app_id = ? GROUP BY month ORDER BY month",
                (app_id,),
            ).fetchall()
        return {
            "total_reviews": agg["total"],
            "avg_rating": agg["avg"],
            "rating_distribution": [{"rating": r["rating"], "count": r["count"]} for r in dist],
            "sentiment_breakdown": [{"label": r["label"] or "none", "count": r["count"]} for r in senti],
            "volume_over_time": [{"month": r["month"], "count": r["count"]} for r in volume],
        }

    # ---- jobs ----

    def create_job(self, app_id: int, platform: str) -> int:
        with self._cursor() as conn:
            cur = conn.execute(
                "INSERT INTO jobs(app_id, platform, status, total_target, fetched_count) "
                "VALUES (?,?,?,?,?)",
                (app_id, platform, "running", None, 0),
            )
            return cur.lastrowid

    def get_job(self, job_id: int) -> Optional[sqlite3.Row]:
        with self._cursor() as conn:
            return conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()

    def finish_job(self, job_id: int, status: str, fetched_count: int, message: str = None) -> None:
        with self._cursor() as conn:
            conn.execute(
                "UPDATE jobs SET status = ?, fetched_count = ?, message = ? WHERE id = ?",
                (status, fetched_count, message, job_id),
            )
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
.venv/bin/pytest tests/test_db.py -v
```

Expected: PASS (5 tests).

- [ ] **Step 5: Commit**

```bash
git add backend/app/db.py backend/tests/conftest.py backend/tests/test_db.py
git commit -m "feat: add sqlite database layer"
```

---

### Task 3: Sentiment module

**Files:**
- Create: `backend/app/sentiment.py`
- Test: `backend/tests/test_sentiment.py`

- [ ] **Step 1: Write the failing test**

`backend/tests/test_sentiment.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
.venv/bin/pytest tests/test_sentiment.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'app.sentiment'`.

- [ ] **Step 3: Write `backend/app/sentiment.py`**

```python
from textblob import TextBlob

POSITIVE_THRESHOLD = 0.05
NEGATIVE_THRESHOLD = -0.05


def score_review(text: str) -> tuple[float, str]:
    polarity = TextBlob(text or "").sentiment.polarity
    if polarity > POSITIVE_THRESHOLD:
        label = "positive"
    elif polarity < NEGATIVE_THRESHOLD:
        label = "negative"
    else:
        label = "neutral"
    return polarity, label
```

- [ ] **Step 4: Run test to verify it passes**

```bash
.venv/bin/pytest tests/test_sentiment.py -v
```

Expected: PASS (4 tests).

- [ ] **Step 5: Commit**

```bash
git add backend/app/sentiment.py backend/tests/test_sentiment.py
git commit -m "feat: add textblob sentiment scoring"
```

---

### Task 4: Scraper abstraction + Play Store scraper

**Files:**
- Create: `backend/app/scrapers/base.py`
- Create: `backend/app/scrapers/playstore.py`
- Test: `backend/tests/test_playstore_scraper.py`

- [ ] **Step 1: Write the failing test**

`backend/tests/test_playstore_scraper.py`:

```python
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
    assert len(batches) == 1
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
    assert calls["n"] == 2
    assert len(batches) == 1
```

- [ ] **Step 2: Run test to verify it fails**

```bash
.venv/bin/pytest tests/test_playstore_scraper.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'app.scrapers.base'`.

- [ ] **Step 3: Write `backend/app/scrapers/base.py`**

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class AppCandidate:
    platform: str
    store_app_id: str
    name: str
    developer: str | None = None
    icon_url: str | None = None
    rating: float | None = None


@dataclass
class ReviewItem:
    review_id: str
    title: str
    body: str
    rating: int
    author: str
    author_url: str | None
    version: str | None
    created_at: str | None


class PlatformScraper(ABC):
    platform: str

    @abstractmethod
    def search(self, query: str, limit: int = 20) -> list[AppCandidate]:
        ...

    @abstractmethod
    def review_batches(self, app_id: str, country: str = "in"):
        """Yield list[ReviewItem] batches, one page at a time."""
        ...


def to_iso(value) -> str | None:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)
```

- [ ] **Step 4: Write `backend/app/scrapers/playstore.py`**

```python
import time

from google_play_scraper import Sort
from google_play_scraper import reviews as gp_reviews
from google_play_scraper import search as gp_search

from .base import AppCandidate, PlatformScraper, ReviewItem, to_iso

PAGE_SIZE = 200
PAGE_SLEEP_SECONDS = 0.5


class PlayStoreScraper(PlatformScraper):
    platform = "playstore"

    def search(self, query: str, limit: int = 20) -> list[AppCandidate]:
        results = gp_search(query, lang="en", country="in", n_hits=limit)
        return [
            AppCandidate(
                platform=self.platform,
                store_app_id=r.get("appId", ""),
                name=r.get("title", ""),
                developer=r.get("developer"),
                icon_url=r.get("icon"),
                rating=r.get("score"),
            )
            for r in results
            if r.get("appId")
        ]

    def review_batches(self, app_id: str, country: str = "in"):
        token = None
        while True:
            result, token = gp_reviews(
                app_id,
                lang="en",
                country=country,
                sort=Sort.NEWEST,
                count=PAGE_SIZE,
                continuation_token=token,
            )
            if result:
                yield [self._to_item(r) for r in result]
            if not token:
                break
            time.sleep(PAGE_SLEEP_SECONDS)

    @staticmethod
    def _to_item(r) -> ReviewItem:
        return ReviewItem(
            review_id=str(r.get("reviewId") or ""),
            title="",
            body=r.get("content") or "",
            rating=int(r.get("score") or 0),
            author=r.get("userName") or "",
            author_url=r.get("userImage"),
            version=r.get("reviewCreatedVersion"),
            created_at=to_iso(r.get("at")),
        )
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
.venv/bin/pytest tests/test_playstore_scraper.py -v
```

Expected: PASS (3 tests).

- [ ] **Step 6: Commit**

```bash
git add backend/app/scrapers/base.py backend/app/scrapers/playstore.py backend/tests/test_playstore_scraper.py
git commit -m "feat: add scraper abstraction and play store scraper"
```

---

### Task 5: App Store scraper

**Files:**
- Create: `backend/app/scrapers/appstore.py`
- Test: `backend/tests/test_appstore_scraper.py`

- [ ] **Step 1: Write the failing test**

`backend/tests/test_appstore_scraper.py`:

```python
from datetime import datetime

from app.scrapers.appstore import AppStoreScraper
from app.scrapers.base import AppCandidate, ReviewItem


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


def test_search_maps_results(monkeypatch):
    payload = {
        "results": [
            {"trackId": 389801252, "trackName": "Instagram", "sellerName": "Instagram, Inc.",
             "artworkUrl100": "http://icon", "averageUserRating": 4.7},
        ]
    }

    def fake_get(url, params, timeout):
        assert params["country"] == "in"
        assert params["entity"] == "software"
        return FakeResponse(payload)

    monkeypatch.setattr("app.scrapers.appstore.requests.get", fake_get)
    results = AppStoreScraper().search("instagram")
    assert results[0] == AppCandidate("appstore", "389801252", "Instagram", "Instagram, Inc.",
                                      "http://icon", 4.7)


def test_review_batches_maps_reviews(monkeypatch):
    class FakeStore:
        def __init__(self, country, app_name, app_id):
            self.reviews = [
                {"id": 100, "title": "Love it", "review": "great", "rating": 5,
                 "userName": "bob", "appVersion": "1.2",
                 "date": datetime(2024, 3, 1, 9, 30)},
            ]

        def review(self, how_many):
            assert how_many == 500

    def fake_store(country, app_name, app_id):
        return FakeStore(country, app_name, app_id)

    monkeypatch.setattr("app.scrapers.appstore.AppStore", fake_store)
    batches = list(AppStoreScraper().review_batches("389801252"))
    item = batches[0][0]
    assert isinstance(item, ReviewItem)
    assert item.review_id == "100"
    assert item.body == "great"
    assert item.rating == 5
    assert item.author == "bob"
    assert item.version == "1.2"
    assert item.created_at == "2024-03-01T09:30:00"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
.venv/bin/pytest tests/test_appstore_scraper.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'app.scrapers.appstore'`.

- [ ] **Step 3: Write `backend/app/scrapers/appstore.py`**

```python
import requests
from app_store_scraper import AppStore

from .base import AppCandidate, PlatformScraper, ReviewItem, to_iso

ITUNES_SEARCH_URL = "https://itunes.apple.com/search"
BATCH_SIZE = 50


class AppStoreScraper(PlatformScraper):
    platform = "appstore"

    def search(self, query: str, limit: int = 20) -> list[AppCandidate]:
        resp = requests.get(
            ITUNES_SEARCH_URL,
            params={"term": query, "country": "in", "entity": "software", "limit": limit},
            timeout=30,
        )
        resp.raise_for_status()
        results = resp.json().get("results", [])
        return [
            AppCandidate(
                platform=self.platform,
                store_app_id=str(r["trackId"]),
                name=r.get("trackName", ""),
                developer=r.get("sellerName"),
                icon_url=r.get("artworkUrl100"),
                rating=r.get("averageUserRating"),
            )
            for r in results
            if r.get("trackId")
        ]

    def review_batches(self, app_id: str, country: str = "in"):
        # Apple's public RSS API caps at 500 most-recent reviews per country.
        store = AppStore(country=country, app_name="", app_id=int(app_id))
        store.review(how_many=500)
        reviews_data = getattr(store, "reviews", [])
        for i in range(0, len(reviews_data), BATCH_SIZE):
            yield [self._to_item(r) for r in reviews_data[i:i + BATCH_SIZE]]

    @staticmethod
    def _to_item(r) -> ReviewItem:
        return ReviewItem(
            review_id=str(r.get("id") or ""),
            title=r.get("title") or "",
            body=r.get("review") or "",
            rating=int(r.get("rating") or 0),
            author=r.get("userName") or "",
            author_url=None,
            version=r.get("appVersion"),
            created_at=to_iso(r.get("date")),
        )
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
.venv/bin/pytest tests/test_appstore_scraper.py -v
```

Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add backend/app/scrapers/appstore.py backend/tests/test_appstore_scraper.py
git commit -m "feat: add app store scraper"
```

---

### Task 6: Search service

**Files:**
- Create: `backend/app/scrapers/search.py`
- Test: `backend/tests/test_search.py`

- [ ] **Step 1: Write the failing test**

`backend/tests/test_search.py`:

```python
from app.scrapers.search import SCRAPERS, search_apps


class FakeScraper:
    platform = "fake"

    def __init__(self, results):
        self._results = results

    def search(self, query, limit=20):
        return self._results


def test_search_apps_single_platform():
    fake = FakeScraper(["candidate"])
    old = SCRAPERS["playstore"]
    SCRAPERS["playstore"] = fake
    try:
        results, errors = search_apps("spotify", "playstore")
        assert results == ["candidate"]
        assert errors == []
    finally:
        SCRAPERS["playstore"] = old


def test_search_apps_isolates_platform_failures():
    def boom(query, limit=20):
        raise RuntimeError("store down")

    old_ps, old_as = SCRAPERS["playstore"], SCRAPERS["appstore"]
    try:
        SCRAPERS["playstore"] = FakeScraper(["play_candidate"])
        SCRAPERS["appstore"] = FakeScraper([])
        SCRAPERS["appstore"].search = boom
        results, errors = search_apps("spotify", "both")
        assert results == ["play_candidate"]
        assert errors and errors[0]["platform"] == "appstore"
    finally:
        SCRAPERS["playstore"], SCRAPERS["appstore"] = old_ps, old_as


def test_search_apps_unknown_platform():
    results, errors = search_apps("spotify", "bogus")
    assert results == []
    assert len(errors) == 1
```

- [ ] **Step 2: Run test to verify it fails**

```bash
.venv/bin/pytest tests/test_search.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'app.scrapers.search'`.

- [ ] **Step 3: Write `backend/app/scrapers/search.py`**

```python
from .appstore import AppStoreScraper
from .base import AppCandidate
from .playstore import PlayStoreScraper

SCRAPERS: dict[str, object] = {
    "playstore": PlayStoreScraper(),
    "appstore": AppStoreScraper(),
}


def search_apps(query: str, platform: str, limit: int = 20) -> tuple[list[AppCandidate], list[dict]]:
    errors: list[dict] = []
    results: list[AppCandidate] = []
    targets = [platform] if platform != "both" else list(SCRAPERS)
    for name in targets:
        scraper = SCRAPERS.get(name)
        if scraper is None:
            errors.append({"platform": name, "message": f"Unknown platform: {name}"})
            continue
        try:
            results.extend(scraper.search(query, limit))
        except Exception as exc:  # noqa: BLE001 - isolate store failures
            errors.append({"platform": name, "message": str(exc)})
    return results, errors
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
.venv/bin/pytest tests/test_search.py -v
```

Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add backend/app/scrapers/search.py backend/tests/test_search.py
git commit -m "feat: add multi-platform search service"
```

---

### Task 7: Job runner

**Files:**
- Create: `backend/app/jobs.py`
- Test: `backend/tests/test_jobs.py`

- [ ] **Step 1: Write the failing test**

`backend/tests/test_jobs.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
.venv/bin/pytest tests/test_jobs.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'app.jobs'`.

- [ ] **Step 3: Write `backend/app/jobs.py`**

```python
import threading
from dataclasses import dataclass, field

from .db import Database
from .scrapers.base import ReviewItem
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


def run_fetch_job(db: Database, registry: JobRegistry, job_id: int, scrapers=None) -> None:
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
        db.finish_job(job_id, "completed", total)
        registry.update(job_id, status="completed")
    except Exception as exc:  # noqa: BLE001 - surface any fetch failure to the job
        db.finish_job(job_id, "failed", total, message=str(exc))
        registry.update(job_id, status="failed", message=str(exc))
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
.venv/bin/pytest tests/test_jobs.py -v
```

Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add backend/app/jobs.py backend/tests/test_jobs.py
git commit -m "feat: add background fetch job runner"
```

---

### Task 8: Pydantic schemas

**Files:**
- Create: `backend/app/schemas.py`
- Test: `backend/tests/test_schemas.py`

- [ ] **Step 1: Write the failing test**

`backend/tests/test_schemas.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
.venv/bin/pytest tests/test_schemas.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'app.schemas'`.

- [ ] **Step 3: Write `backend/app/schemas.py`**

```python
from typing import Optional

from pydantic import BaseModel, Field, field_validator

PLATFORMS = {"playstore", "appstore"}


class AppSearchResult(BaseModel):
    platform: str
    store_app_id: str
    name: str
    developer: Optional[str] = None
    icon_url: Optional[str] = None
    rating: Optional[float] = None


class SearchResponse(BaseModel):
    results: list[AppSearchResult] = Field(default_factory=list)
    errors: list[dict] = Field(default_factory=list)


class AppCreate(BaseModel):
    name: str
    platform: str
    store_app_id: str
    developer: Optional[str] = None
    icon_url: Optional[str] = None

    @field_validator("platform")
    @classmethod
    def _check_platform(cls, v):
        if v not in PLATFORMS:
            raise ValueError("platform must be 'playstore' or 'appstore'")
        return v


class AppOut(BaseModel):
    id: int
    name: str
    platform: str
    store_app_id: str
    developer: Optional[str] = None
    icon_url: Optional[str] = None


class ReviewOut(BaseModel):
    id: int
    review_id: Optional[str] = None
    title: str
    body: str
    rating: int
    author: str
    version: Optional[str] = None
    created_at: Optional[str] = None
    sentiment_label: str


class ReviewPage(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[ReviewOut]


class JobOut(BaseModel):
    id: int
    app_id: int
    status: str
    fetched_count: int
    message: Optional[str] = None
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
.venv/bin/pytest tests/test_schemas.py -v
```

Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add backend/app/schemas.py backend/tests/test_schemas.py
git commit -m "feat: add pydantic schemas"
```

---

### Task 9: FastAPI app factory + apps router

**Files:**
- Create: `backend/app/main.py`
- Create: `backend/app/routers/apps.py`
- Test: `backend/tests/test_api_apps.py`

- [ ] **Step 1: Write the failing test**

`backend/tests/test_api_apps.py`:

```python
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
    resp = client.get("/api/apps/search", params={"q": "spotify"})
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
.venv/bin/pytest tests/test_api_apps.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'app.main'`.

- [ ] **Step 3: Write `backend/app/routers/apps.py`**

```python
from fastapi import APIRouter, HTTPException, Request, Query

from app.scrapers.search import search_apps
from app.schemas import AppCreate, AppOut, AppSearchResult, SearchResponse

router = APIRouter(prefix="/api/apps", tags=["apps"])


@router.get("/search", response_model=SearchResponse)
def search(request: Request, q: str = Query(..., min_length=1), platform: str = "both"):
    if platform not in ("playstore", "appstore", "both"):
        raise HTTPException(400, "platform must be 'playstore', 'appstore' or 'both'")
    results, errors = search_apps(q, platform)
    return SearchResponse(results=[AppSearchResult(**r.__dict__) for r in results], errors=errors)


@router.post("", response_model=AppOut)
def create_app(request: Request, body: AppCreate):
    db = request.app.state.db
    app_id = db.create_app(body.name, body.platform, body.store_app_id,
                           body.developer, body.icon_url)
    row = db.get_app(app_id)
    return AppOut(id=row["id"], name=row["name"], platform=row["platform"],
                  store_app_id=row["store_app_id"], developer=row["developer"],
                  icon_url=row["icon_url"])


@router.get("", response_model=list[AppOut])
def list_apps(request: Request):
    db = request.app.state.db
    return [AppOut(id=r["id"], name=r["name"], platform=r["platform"],
                   store_app_id=r["store_app_id"], developer=r["developer"],
                   icon_url=r["icon_url"]) for r in db.list_apps()]
```

- [ ] **Step 4: Write `backend/app/main.py`**

```python
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .db import Database
from .jobs import JobRegistry
from .routers import apps, jobs, reviews

DB_PATH = Path(__file__).resolve().parent.parent / "review_data.db"


def create_app(db: Database, registry: JobRegistry) -> FastAPI:
    app = FastAPI(title="Store Reviews Fetcher")
    app.state.db = db
    app.state.registry = registry
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(apps.router)
    app.include_router(reviews.router)
    app.include_router(jobs.router)
    return app


_db = Database(DB_PATH)
_registry = JobRegistry()
app = create_app(_db, _registry)
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
.venv/bin/pytest tests/test_api_apps.py -v
```

Expected: PASS (4 tests).

- [ ] **Step 6: Commit**

```bash
git add backend/app/routers/apps.py backend/app/main.py backend/tests/test_api_apps.py
git commit -m "feat: add fastapi app and apps router"
```

---

### Task 10: Reviews router (list, stats, export)

**Files:**
- Create: `backend/app/routers/reviews.py`
- Test: `backend/tests/test_api_reviews.py`

- [ ] **Step 1: Write the failing test**

`backend/tests/test_api_reviews.py`:

```python
from app.db import Database


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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
.venv/bin/pytest tests/test_api_reviews.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'app.routers.reviews'`.

- [ ] **Step 3: Write `backend/app/routers/reviews.py`**

```python
import csv
import io

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import StreamingResponse

from app.schemas import ReviewOut, ReviewPage

router = APIRouter(prefix="/api/apps", tags=["reviews"])


def _get_app_or_404(db, app_id: int):
    row = db.get_app(app_id)
    if row is None:
        raise HTTPException(404, "App not found")
    return row


@router.get("/{app_id}/reviews", response_model=ReviewPage)
def list_reviews(
    request: Request,
    app_id: int,
    q: str = None,
    rating: int = Query(None, ge=1, le=5),
    min_rating: int = Query(None, ge=1, le=5),
    sentiment: str = None,
    start_date: str = None,
    end_date: str = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
):
    db = request.app.state.db
    _get_app_or_404(db, app_id)
    kwargs = dict(q=q, rating=rating, min_rating=min_rating, sentiment=sentiment,
                  start_date=start_date, end_date=end_date)
    total = db.count_matching(app_id, **kwargs)
    rows = db.query_reviews(app_id, page=page, page_size=page_size, **kwargs)
    items = [
        ReviewOut(id=r["id"], review_id=r["review_id"], title=r["title"] or "",
                  body=r["body"] or "", rating=r["rating"], author=r["author"] or "",
                  version=r["version"], created_at=r["created_at"],
                  sentiment_label=r["sentiment_label"] or "neutral")
        for r in rows
    ]
    return ReviewPage(total=total, page=page, page_size=page_size, items=items)


@router.get("/{app_id}/stats")
def get_stats(request: Request, app_id: int):
    db = request.app.state.db
    _get_app_or_404(db, app_id)
    return db.get_stats(app_id)


@router.get("/{app_id}/export")
def export_reviews(
    request: Request,
    app_id: int,
    format: str = Query("csv", pattern="^(csv|json)$"),
    q: str = None,
    rating: int = None,
    min_rating: int = None,
    sentiment: str = None,
    start_date: str = None,
    end_date: str = None,
):
    db = request.app.state.db
    _get_app_or_404(db, app_id)
    kwargs = dict(q=q, rating=rating, min_rating=min_rating, sentiment=sentiment,
                  start_date=start_date, end_date=end_date)
    rows = db.query_reviews(app_id, **kwargs)
    if format == "json":
        payload = [
            {
                "review_id": r["review_id"], "title": r["title"] or "", "body": r["body"] or "",
                "rating": r["rating"], "author": r["author"] or "", "version": r["version"],
                "created_at": r["created_at"], "sentiment": r["sentiment_label"],
            }
            for r in rows
        ]
        import json

        return StreamingResponse(
            iter([json.dumps(payload, indent=2)]),
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="reviews.json"'},
        )
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["review_id", "rating", "author", "version", "created_at",
                     "sentiment", "title", "body"])
    for r in rows:
        writer.writerow([r["review_id"], r["rating"], r["author"] or "", r["version"],
                         r["created_at"], r["sentiment_label"], r["title"] or "",
                         r["body"] or ""])
    buffer.seek(0)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="reviews.csv"'},
    )
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
.venv/bin/pytest tests/test_api_reviews.py -v
```

Expected: PASS (5 tests).

- [ ] **Step 5: Commit**

```bash
git add backend/app/routers/reviews.py backend/tests/test_api_reviews.py
git commit -m "feat: add reviews list, stats and export endpoints"
```

---

### Task 11: Jobs router (start fetch + poll progress)

**Files:**
- Create: `backend/app/routers/jobs.py`
- Test: `backend/tests/test_api_jobs.py`

- [ ] **Step 1: Write the failing test**

`backend/tests/test_api_jobs.py`:

```python
import threading
import time


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
    assert "job_id" in body
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
.venv/bin/pytest tests/test_api_jobs.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'app.routers.jobs'`.

- [ ] **Step 3: Write `backend/app/routers/jobs.py`**

```python
import threading

from fastapi import APIRouter, HTTPException, Request

from app.jobs import run_fetch_job
from app.schemas import JobOut

router = APIRouter(prefix="/api", tags=["jobs"])


@router.post("/apps/{app_id}/fetch", response_model=JobOut)
def start_fetch(request: Request, app_id: int):
    db = request.app.state.db
    registry = request.app.state.registry
    app_row = db.get_app(app_id)
    if app_row is None:
        raise HTTPException(404, "App not found")
    job_id = db.create_job(app_id, app_row["platform"])
    state = registry.create(job_id, app_id)
    threading.Thread(
        target=run_fetch_job,
        args=(db, registry, job_id),
        daemon=True,
    ).start()
    return JobOut(id=state.id, app_id=state.app_id, status=state.status,
                  fetched_count=state.fetched_count, message=state.message)


@router.get("/jobs/{job_id}", response_model=JobOut)
def get_job(request: Request, job_id: int):
    db = request.app.state.db
    registry = request.app.state.registry
    state = registry.get(job_id)
    if state is None:
        row = db.get_job(job_id)
        if row is None:
            raise HTTPException(404, "Job not found")
        return JobOut(id=row["id"], app_id=row["app_id"], status=row["status"],
                      fetched_count=row["fetched_count"], message=row["message"])
    return JobOut(**state.snapshot())
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
.venv/bin/pytest tests/test_api_jobs.py -v
```

Expected: PASS (4 tests).

- [ ] **Step 5: Commit**

```bash
git add backend/app/routers/jobs.py backend/tests/test_api_jobs.py
git commit -m "feat: add fetch job start and progress endpoints"
```

- [ ] **Step 6: Run the full backend suite**

```bash
.venv/bin/pytest -v
```

Expected: all tests PASS.

---

### Task 12: Backend live smoke test

**Files:**
- Create: `backend/smoke_test.py`

- [ ] **Step 1: Write `backend/smoke_test.py`**

```python
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
```

- [ ] **Step 2: Run the smoke test (manual, needs internet)**

```bash
.venv/bin/python smoke_test.py "Instagram"
```

Expected: Play Store + App Store search return the real Instagram app, then reviews are fetched into `smoke_reviews.db`. Play Store may take a while (pagination); App Store returns up to 500.

- [ ] **Step 3: Clean up smoke artifacts**

```bash
rm -f smoke_reviews.db
```

- [ ] **Step 4: Commit**

```bash
git add backend/smoke_test.py
git commit -m "test: add live smoke test script"
```

---

### Task 13: Frontend scaffold (Vite + React)

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.js`
- Create: `frontend/index.html`
- Create: `frontend/src/main.jsx`
- Create: `frontend/src/App.jsx`
- Create: `frontend/src/filters.js`
- Create: `frontend/src/api.js`

- [ ] **Step 1: Write `frontend/package.json`**

```json
{
  "name": "store-reviews-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview",
    "test": "vitest run"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-router-dom": "^6.28.0",
    "recharts": "^2.15.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.3.4",
    "@testing-library/jest-dom": "^6.6.3",
    "@testing-library/react": "^16.1.0",
    "@testing-library/user-event": "^14.5.2",
    "jsdom": "^25.0.1",
    "vite": "^5.4.11",
    "vitest": "^2.1.8"
  }
}
```

- [ ] **Step 2: Write `frontend/vite.config.js`**

```js
import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './src/test-setup.js',
  },
});
```

- [ ] **Step 3: Write `frontend/index.html`**

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Store Reviews Fetcher</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
```

- [ ] **Step 4: Write `frontend/src/main.jsx`**

```jsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './App.jsx';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>,
);
```

- [ ] **Step 5: Write `frontend/src/App.jsx`**

```jsx
import { Route, Routes, NavLink } from 'react-router-dom';
import DashboardPage from './pages/DashboardPage.jsx';
import SearchPage from './pages/SearchPage.jsx';

export default function App() {
  return (
    <div style={{ fontFamily: 'system-ui, sans-serif', maxWidth: 1100, margin: '0 auto', padding: 16 }}>
      <nav style={{ display: 'flex', gap: 16, marginBottom: 24 }}>
        <NavLink to="/">Search &amp; Fetch</NavLink>
        <NavLink to="/dashboard">Dashboard</NavLink>
      </nav>
      <Routes>
        <Route path="/" element={<SearchPage />} />
        <Route path="/dashboard" element={<DashboardPage />} />
      </Routes>
    </div>
  );
}
```

- [ ] **Step 6: Write `frontend/src/filters.js`**

```js
export function buildFilterParams(filters) {
  const params = {};
  for (const [key, value] of Object.entries(filters)) {
    if (value !== '' && value !== null && value !== undefined) params[key] = value;
  }
  return params;
}
```

- [ ] **Step 7: Write `frontend/src/api.js`**

```js
const API = '/api';

async function request(url, options = {}) {
  const res = await fetch(url, options);
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      /* ignore non-JSON errors */
    }
    throw new Error(detail);
  }
  return res.json();
}

export const searchApps = (q, platform) =>
  request(`${API}/apps/search?q=${encodeURIComponent(q)}&platform=${platform}`);

export const createApp = (candidate) =>
  request(`${API}/apps`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(candidate),
  });

export const listApps = () => request(`${API}/apps`);

export const getReviews = (appId, params) =>
  request(`${API}/apps/${appId}/reviews?${new URLSearchParams(params)}`);

export const getStats = (appId) => request(`${API}/apps/${appId}/stats`);

export const startFetch = (appId) => request(`${API}/apps/${appId}/fetch`, { method: 'POST' });

export const getJob = (jobId) => request(`${API}/jobs/${jobId}`);

export const exportUrl = (appId, format, params = {}) =>
  `${API}/apps/${appId}/export?format=${format}${Object.keys(params).length ? `&${new URLSearchParams(params)}` : ''}`;
```

- [ ] **Step 8: Install dependencies**

```bash
cd frontend && npm install
```

Expected: installs cleanly.

- [ ] **Step 9: Commit**

```bash
git add frontend/package.json frontend/package-lock.json frontend/vite.config.js frontend/index.html frontend/src/main.jsx frontend/src/App.jsx frontend/src/filters.js frontend/src/api.js
git commit -m "feat: scaffold react frontend"
```

---

### Task 14: Search & Fetch page

**Files:**
- Create: `frontend/src/pages/SearchPage.jsx`

- [ ] **Step 1: Write `frontend/src/pages/SearchPage.jsx`**

```jsx
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import * as api from '../api.js';

const PLATFORM_LABELS = { playstore: 'Play Store', appstore: 'App Store' };

export default function SearchPage() {
  const [query, setQuery] = useState('');
  const [platform, setPlatform] = useState('both');
  const [results, setResults] = useState([]);
  const [errors, setErrors] = useState([]);
  const [searching, setSearching] = useState(false);
  const [job, setJob] = useState(null);
  const navigate = useNavigate();

  async function handleSearch(event) {
    event.preventDefault();
    if (!query.trim()) return;
    setSearching(true);
    setErrors([]);
    setJob(null);
    try {
      const data = await api.searchApps(query.trim(), platform);
      setResults(data.results);
      setErrors(data.errors);
    } catch (err) {
      setErrors([{ message: err.message }]);
      setResults([]);
    } finally {
      setSearching(false);
    }
  }

  async function handleFetch(candidate) {
    setJob({ status: 'starting', fetched_count: 0 });
    setErrors([]);
    try {
      const app = await api.createApp(candidate);
      const created = await api.startFetch(app.id);
      pollJob(created.id);
    } catch (err) {
      setErrors([{ message: err.message }]);
      setJob(null);
    }
  }

  async function pollJob(jobId) {
    try {
      const state = await api.getJob(jobId);
      setJob(state);
      if (state.status === 'running') {
        setTimeout(() => pollJob(jobId), 1500);
      } else if (state.status === 'completed') {
        setTimeout(() => navigate('/dashboard'), 600);
      }
    } catch {
      setTimeout(() => pollJob(jobId), 2000);
    }
  }

  return (
    <section>
      <h1>Find an app and fetch its reviews</h1>
      <form onSubmit={handleSearch} style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
        <label>
          App name
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="e.g. Instagram"
            style={{ marginLeft: 8 }}
          />
        </label>
        <label>
          Platform
          <select value={platform} onChange={(e) => setPlatform(e.target.value)} style={{ marginLeft: 8 }}>
            <option value="both">Both</option>
            <option value="playstore">Play Store</option>
            <option value="appstore">App Store</option>
          </select>
        </label>
        <button type="submit" disabled={searching}>
          {searching ? 'Searching…' : 'Search'}
        </button>
      </form>

      {errors.length > 0 && (
        <div style={{ color: '#c0392b', marginTop: 12 }}>
          {errors.map((e, i) => (
            <p key={i}>{e.platform ? `[${e.platform}] ${e.message}` : e.message}</p>
          ))}
        </div>
      )}

      {job && (
        <div style={{ marginTop: 12 }}>
          <strong>Fetching reviews…</strong> {job.fetched_count || 0} fetched
          {job.status === 'running' && <span> (still running)</span>}
        </div>
      )}

      {results.length > 0 && (
        <ul style={{ listStyle: 'none', padding: 0, marginTop: 16 }}>
          {results.map((r, i) => (
            <li
              key={`${r.platform}-${r.store_app_id}`}
              style={{ display: 'flex', gap: 12, alignItems: 'center', border: '1px solid #ddd', padding: 12, marginBottom: 8 }}
            >
              {r.icon_url && <img src={r.icon_url} alt="" width="48" height="48" />}
              <div style={{ flex: 1 }}>
                <strong>{r.name}</strong>
                <div>{r.developer || ''}</div>
                <div>
                  {PLATFORM_LABELS[r.platform] || r.platform}
                  {r.rating != null && ` · ⭐ ${r.rating.toFixed(1)}`}
                </div>
              </div>
              <button type="button" onClick={() => handleFetch(r)}>
                Fetch reviews
              </button>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
```

- [ ] **Step 2: Verify the dev server builds the page**

```bash
cd frontend && npm run build
```

Expected: build succeeds (the page compiles).

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/SearchPage.jsx
git commit -m "feat: add search and fetch page"
```

---

### Task 15: Dashboard page

**Files:**
- Create: `frontend/src/pages/DashboardPage.jsx`

- [ ] **Step 1: Write `frontend/src/pages/DashboardPage.jsx`**

```jsx
import { useEffect, useState } from 'react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import * as api from '../api.js';
import { buildFilterParams } from '../filters.js';

const SENTIMENT_COLORS = { positive: '#27ae60', neutral: '#95a5a6', negative: '#e74c3c' };
const RATING_COLORS = ['#e74c3c', '#e67e22', '#f1c40f', '#aed581', '#27ae60'];

const EMPTY_FILTERS = { q: '', rating: '', sentiment: '', start_date: '', end_date: '' };

export default function DashboardPage() {
  const [apps, setApps] = useState([]);
  const [appId, setAppId] = useState(null);
  const [stats, setStats] = useState(null);
  const [reviews, setReviews] = useState({ total: 0, items: [] });
  const [filters, setFilters] = useState(EMPTY_FILTERS);
  const [error, setError] = useState('');

  useEffect(() => {
    api.listApps().then((rows) => {
      setApps(rows);
      if (rows.length > 0) setAppId(rows[0].id);
    }).catch((err) => setError(err.message));
  }, []);

  useEffect(() => {
    if (!appId) return;
    api.getStats(appId).then(setStats).catch((err) => setError(err.message));
    loadReviews(appId, {});
  }, [appId]);

  async function loadReviews(id, params) {
    try {
      setReviews(await api.getReviews(id, params));
    } catch (err) {
      setError(err.message);
    }
  }

  function applyFilters(event) {
    event.preventDefault();
    const params = buildFilterParams(filters);
    loadReviews(appId, { ...params, page: 1, page_size: 100 });
  }

  const selectedApp = apps.find((a) => a.id === appId);

  return (
    <section>
      <h1>Dashboard</h1>
      {apps.length === 0 && <p>No apps fetched yet. Go to Search &amp; Fetch first.</p>}
      {apps.length > 0 && (
        <>
          <label>
            App
            <select value={appId} onChange={(e) => setAppId(Number(e.target.value))} style={{ marginLeft: 8 }}>
              {apps.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.name} ({a.platform})
                </option>
              ))}
            </select>
          </label>

          {stats && (
            <>
              <div style={{ display: 'flex', gap: 16, marginTop: 16 }}>
                <StatCard label="Total reviews" value={stats.total_reviews} />
                <StatCard label="Average rating" value={stats.avg_rating?.toFixed(2) ?? '—'} />
                <StatCard label="Positive" value={stats.sentiment_breakdown.find((s) => s.label === 'positive')?.count ?? 0} />
                <StatCard label="Negative" value={stats.sentiment_breakdown.find((s) => s.label === 'negative')?.count ?? 0} />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 16, marginTop: 24 }}>
                <Chart title="Rating distribution">
                  <BarChart data={stats.rating_distribution}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="rating" />
                    <YAxis allowDecimals={false} />
                    <Tooltip />
                    <Bar dataKey="count">
                      {stats.rating_distribution.map((entry, i) => (
                        <Cell key={i} fill={RATING_COLORS[entry.rating - 1] ?? '#bdc3c7'} />
                      ))}
                    </Bar>
                  </BarChart>
                </Chart>
                <Chart title="Reviews over time">
                  <LineChart data={stats.volume_over_time}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="month" />
                    <YAxis allowDecimals={false} />
                    <Tooltip />
                    <Line type="monotone" dataKey="count" stroke="#2980b9" />
                  </LineChart>
                </Chart>
                <Chart title="Sentiment">
                  <PieChart>
                    <Pie data={stats.sentiment_breakdown} dataKey="count" nameKey="label" outerRadius={90}>
                      {stats.sentiment_breakdown.map((s, i) => (
                        <Cell key={i} fill={SENTIMENT_COLORS[s.label] ?? '#bdc3c7'} />
                      ))}
                    </Pie>
                    <Tooltip />
                    <Legend />
                  </PieChart>
                </Chart>
              </div>
            </>
          )}

          <form onSubmit={applyFilters} style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginTop: 24 }}>
            <label>
              Keyword
              <input value={filters.q} onChange={(e) => setFilters({ ...filters, q: e.target.value })} style={{ marginLeft: 8 }} />
            </label>
            <label>
              Rating
              <select value={filters.rating} onChange={(e) => setFilters({ ...filters, rating: e.target.value })} style={{ marginLeft: 8 }}>
                <option value="">Any</option>
                {[1, 2, 3, 4, 5].map((n) => (
                  <option key={n} value={n}>{n}★</option>
                ))}
              </select>
            </label>
            <label>
              Sentiment
              <select value={filters.sentiment} onChange={(e) => setFilters({ ...filters, sentiment: e.target.value })} style={{ marginLeft: 8 }}>
                <option value="">Any</option>
                <option value="positive">Positive</option>
                <option value="neutral">Neutral</option>
                <option value="negative">Negative</option>
              </select>
            </label>
            <label>
              From
              <input type="date" value={filters.start_date} onChange={(e) => setFilters({ ...filters, start_date: e.target.value })} style={{ marginLeft: 8 }} />
            </label>
            <label>
              To
              <input type="date" value={filters.end_date} onChange={(e) => setFilters({ ...filters, end_date: e.target.value })} style={{ marginLeft: 8 }} />
            </label>
            <button type="submit">Apply filters</button>
          </form>

          <div style={{ display: 'flex', gap: 12, marginTop: 12 }}>
            <a href={api.exportUrl(appId, 'csv')} download>Export CSV</a>
            <a href={api.exportUrl(appId, 'json')} download>Export JSON</a>
          </div>

          <p>
            Showing {reviews.items.length} of {reviews.total} matching reviews.
          </p>
          <table style={{ borderCollapse: 'collapse', width: '100%', marginTop: 12 }}>
            <thead>
              <tr>
                <th>Rating</th>
                <th>Author</th>
                <th>Date</th>
                <th>Sentiment</th>
                <th>Review</th>
              </tr>
            </thead>
            <tbody>
              {reviews.items.map((r) => (
                <tr key={r.id} style={{ borderBottom: '1px solid #eee', verticalAlign: 'top' }}>
                  <td>{'★'.repeat(r.rating)}</td>
                  <td>{r.author}</td>
                  <td>{r.created_at ? r.created_at.slice(0, 10) : ''}</td>
                  <td>{r.sentiment_label}</td>
                  <td>{r.body}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
      {error && <p style={{ color: '#c0392b' }}>{error}</p>}
      {selectedApp && <p style={{ marginTop: 24 }}>Platform ID: {selectedApp.store_app_id}</p>}
    </section>
  );
}

function StatCard({ label, value }) {
  return (
    <div style={{ border: '1px solid #ddd', borderRadius: 8, padding: 16, minWidth: 120 }}>
      <div style={{ fontSize: 24, fontWeight: 700 }}>{value}</div>
      <div style={{ color: '#7f8c8d' }}>{label}</div>
    </div>
  );
}

function Chart({ title, children }) {
  return (
    <div>
      <h3>{title}</h3>
      <ResponsiveContainer width="100%" height={220}>
        {children}
      </ResponsiveContainer>
    </div>
  );
}
```

- [ ] **Step 2: Verify build**

```bash
cd frontend && npm run build
```

Expected: build succeeds.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/DashboardPage.jsx
git commit -m "feat: add dashboard page with stats, charts, filters and export"
```

---

### Task 16: Frontend tests

**Files:**
- Create: `frontend/src/test-setup.js`
- Create: `frontend/src/__tests__/filters.test.js`
- Create: `frontend/src/__tests__/SearchPage.test.jsx`

- [ ] **Step 1: Write `frontend/src/test-setup.js`**

```js
import '@testing-library/jest-dom/vitest';
```

- [ ] **Step 2: Write `frontend/src/__tests__/filters.test.js`**

```js
import { describe, expect, it } from 'vitest';
import { buildFilterParams } from '../filters.js';

describe('buildFilterParams', () => {
  it('drops empty filters', () => {
    expect(buildFilterParams({ q: '', rating: '', sentiment: '', start_date: '', end_date: '' })).toEqual({});
  });

  it('keeps filled filters', () => {
    expect(buildFilterParams({ q: 'crash', rating: '1' })).toEqual({ q: 'crash', rating: '1' });
  });
});
```

- [ ] **Step 3: Write `frontend/src/__tests__/SearchPage.test.jsx`**

```jsx
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import SearchPage from '../pages/SearchPage.jsx';
import * as api from '../api.js';

vi.mock('../api.js', () => ({
  searchApps: vi.fn(),
  createApp: vi.fn(),
  startFetch: vi.fn(),
  getJob: vi.fn(),
}));

describe('SearchPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('searches and displays candidate apps', async () => {
    api.searchApps.mockResolvedValue({
      results: [
        { platform: 'playstore', store_app_id: 'com.spotify.music', name: 'Spotify', developer: 'Spotify AB' },
      ],
      errors: [],
    });
    render(
      <MemoryRouter>
        <SearchPage />
      </MemoryRouter>,
    );
    fireEvent.change(screen.getByLabelText(/app name/i), { target: { value: 'Spotify' } });
    fireEvent.click(screen.getByRole('button', { name: /search/i }));
    await waitFor(() => expect(screen.getByText('Spotify')).toBeInTheDocument());
    expect(api.searchApps).toHaveBeenCalledWith('Spotify', 'both');
  });

  it('creates the app and starts a fetch when clicking fetch', async () => {
    api.searchApps.mockResolvedValue({
      results: [{ platform: 'appstore', store_app_id: '389801252', name: 'Instagram', developer: 'Instagram, Inc.' }],
      errors: [],
    });
    api.createApp.mockResolvedValue({ id: 7 });
    api.startFetch.mockResolvedValue({ id: 42 });
    api.getJob.mockResolvedValue({ status: 'completed', fetched_count: 10 });

    render(
      <MemoryRouter>
        <SearchPage />
      </MemoryRouter>,
    );
    fireEvent.change(screen.getByLabelText(/app name/i), { target: { value: 'Instagram' } });
    fireEvent.click(screen.getByRole('button', { name: /search/i }));
    await waitFor(() => expect(screen.getByText('Instagram')).toBeInTheDocument());
    fireEvent.click(screen.getByRole('button', { name: /fetch reviews/i }));
    await waitFor(() => expect(api.createApp).toHaveBeenCalledWith(
      expect.objectContaining({ store_app_id: '389801252' }),
    ));
    await waitFor(() => expect(api.startFetch).toHaveBeenCalledWith(7));
  });
});
```

- [ ] **Step 4: Run the tests**

```bash
cd frontend && npm test
```

Expected: PASS (2 test files).

- [ ] **Step 5: Commit**

```bash
git add frontend/src/test-setup.js frontend/src/__tests__/filters.test.js frontend/src/__tests__/SearchPage.test.jsx
git commit -m "test: add frontend unit tests"
```

---

### Task 17: README, production serving, final integration

**Files:**
- Create: `README.md`
- Modify: `backend/app/main.py` (serve built frontend if present)

- [ ] **Step 1: Update `backend/app/main.py` to serve the built frontend**

Replace the `create_app` return block and the module tail so a built React bundle is served when it exists. New `backend/app/main.py`:

```python
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .db import Database
from .jobs import JobRegistry
from .routers import apps, jobs, reviews

DB_PATH = Path(__file__).resolve().parent.parent / "review_data.db"
FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"


def create_app(db: Database, registry: JobRegistry) -> FastAPI:
    app = FastAPI(title="Store Reviews Fetcher")
    app.state.db = db
    app.state.registry = registry
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(apps.router)
    app.include_router(reviews.router)
    app.include_router(jobs.router)
    if FRONTEND_DIST.exists():
        app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
    return app


_db = Database(DB_PATH)
_registry = JobRegistry()
app = create_app(_db, _registry)
```

- [ ] **Step 2: Run backend tests to confirm the change**

```bash
.venv/bin/pytest -v
```

Expected: all PASS (the `frontend/dist` folder does not exist during tests, so the static mount is skipped).

- [ ] **Step 3: Build the frontend**

```bash
cd frontend && npm run build
```

Expected: `frontend/dist` is created.

- [ ] **Step 4: Write `README.md`**

```markdown
# Store Reviews Fetcher

Fetch all available reviews and ratings for any app from the Google Play Store and Apple App Store (India locale), then search, analyze sentiment, chart, and export them.

## Features

- Enter an app name and platform (`playstore`, `appstore`, or `both`)
- Pick the correct app from live search results
- Fetch all available reviews into SQLite (background job with progress)
- Search/filter by keyword, rating, sentiment, and date range
- Charts: rating distribution, volume over time, sentiment breakdown
- Sentiment analysis per review (TextBlob)
- CSV / JSON export

## Project layout

```
backend/    FastAPI API + scrapers + SQLite
frontend/   React (Vite) UI
```

## Run it (development)

Backend:

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/uvicorn app.main:app --reload --port 8000
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

## Run it (production)

```bash
cd frontend && npm run build
cd ../backend && .venv/bin/uvicorn app.main:app --port 8000
```

Open http://localhost:8000 (FastAPI serves the built UI).

## Tests

```bash
cd backend && .venv/bin/pytest
cd frontend && npm test
```

## Notes

- App Store public RSS limits review fetching to the ~500 most recent reviews per country.
- Play Store fetches paginate through all available reviews, which can take minutes for popular apps.
- Country is fixed to India (`in`).
```

- [ ] **Step 5: Final full verification**

```bash
cd backend && .venv/bin/pytest -v
cd ../frontend && npm test && npm run build
```

Expected: backend tests PASS, frontend tests PASS, production build succeeds.

- [ ] **Step 6: Commit**

```bash
git add backend/app/main.py README.md
git commit -m "docs: add README and production frontend serving"
```
