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

    def _review_where(self, app_id: int, q=None, rating=None, min_rating=None,
                      sentiment=None, start_date=None, end_date=None):
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
        return " AND ".join(where), params

    def query_reviews(self, app_id: int, q: str = None, rating: int = None,
                      min_rating: int = None, sentiment: str = None,
                      start_date: str = None, end_date: str = None,
                      page: int = None, page_size: int = 50) -> list[sqlite3.Row]:
        where, params = self._review_where(
            app_id, q=q, rating=rating, min_rating=min_rating, sentiment=sentiment,
            start_date=start_date, end_date=end_date,
        )
        sql = f"SELECT * FROM reviews WHERE {where} ORDER BY created_at DESC"
        if page is not None:
            sql += " LIMIT ? OFFSET ?"
            params += [page_size, (page - 1) * page_size]
        with self._cursor() as conn:
            return conn.execute(sql, params).fetchall()

    def count_matching(self, app_id: int, q: str = None, rating: int = None,
                       min_rating: int = None, sentiment: str = None,
                       start_date: str = None, end_date: str = None) -> int:
        where, params = self._review_where(
            app_id, q=q, rating=rating, min_rating=min_rating, sentiment=sentiment,
            start_date=start_date, end_date=end_date,
        )
        with self._cursor() as conn:
            return conn.execute(
                f"SELECT COUNT(*) AS c FROM reviews WHERE {where}", params
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
