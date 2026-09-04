import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Optional
import urllib.parse

SQLITE_SCHEMA = """
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

PG_SCHEMA = """
CREATE TABLE IF NOT EXISTS apps (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    platform VARCHAR NOT NULL,
    store_app_id VARCHAR NOT NULL,
    developer VARCHAR,
    icon_url VARCHAR,
    created_at VARCHAR NOT NULL DEFAULT CAST(CURRENT_TIMESTAMP AS VARCHAR),
    UNIQUE(platform, store_app_id)
);
CREATE TABLE IF NOT EXISTS reviews (
    id SERIAL PRIMARY KEY,
    app_id INTEGER NOT NULL REFERENCES apps(id),
    review_id VARCHAR,
    title VARCHAR,
    body TEXT,
    rating INTEGER,
    author VARCHAR,
    author_url VARCHAR,
    version VARCHAR,
    country VARCHAR,
    created_at VARCHAR,
    fetched_at VARCHAR NOT NULL DEFAULT CAST(CURRENT_TIMESTAMP AS VARCHAR),
    sentiment_score REAL,
    sentiment_label VARCHAR,
    UNIQUE(app_id, review_id)
);
CREATE TABLE IF NOT EXISTS jobs (
    id SERIAL PRIMARY KEY,
    app_id INTEGER NOT NULL REFERENCES apps(id),
    platform VARCHAR NOT NULL,
    status VARCHAR NOT NULL,
    total_target INTEGER,
    fetched_count INTEGER NOT NULL DEFAULT 0,
    message TEXT,
    created_at VARCHAR NOT NULL DEFAULT CAST(CURRENT_TIMESTAMP AS VARCHAR)
);
CREATE INDEX IF NOT EXISTS idx_reviews_app ON reviews(app_id);
CREATE INDEX IF NOT EXISTS idx_reviews_app_rating ON reviews(app_id, rating);
CREATE INDEX IF NOT EXISTS idx_reviews_app_sentiment ON reviews(app_id, sentiment_label);
CREATE INDEX IF NOT EXISTS idx_jobs_app ON jobs(app_id);
"""

class Database:
    def __init__(self, db_url: str | Path):
        self.db_url = str(db_url)
        self.is_postgres = self.db_url.startswith("postgres")
        
        if not self.is_postgres:
            if self.db_url.startswith("sqlite:///"):
                self.db_url = self.db_url[10:]
            path = Path(self.db_url)
            path.parent.mkdir(parents=True, exist_ok=True)
        
        if self.is_postgres:
            import psycopg2
            self.psycopg2 = psycopg2
            from psycopg2.extras import RealDictCursor
            self.RealDictCursor = RealDictCursor
            
        self.init()

    def connect(self):
        if self.is_postgres:
            return self.psycopg2.connect(self.db_url, cursor_factory=self.RealDictCursor)
        else:
            conn = sqlite3.connect(self.db_url)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            return conn

    @contextmanager
    def _cursor(self):
        conn = self.connect()
        try:
            cur = conn.cursor()
            yield cur
            if self.is_postgres:
                cur.close()
            conn.commit()
        finally:
            conn.close()

    def _param(self, query: str) -> str:
        """Swap placeholders ? for %s if using Postgres"""
        if self.is_postgres:
            return query.replace("?", "%s")
        return query

    def init(self) -> None:
        with self._cursor() as c:
            if self.is_postgres:
                c.execute(PG_SCHEMA)
            else:
                c.executescript(SQLITE_SCHEMA)

    def close(self) -> None:
        pass

    # ---- apps ----
    def create_app(self, name, platform, store_app_id, developer=None, icon_url=None) -> int:
        with self._cursor() as c:
            if self.is_postgres:
                c.execute(
                    "INSERT INTO apps(name, platform, store_app_id, developer, icon_url) "
                    "VALUES (%s,%s,%s,%s,%s) "
                    "ON CONFLICT(platform, store_app_id) DO NOTHING RETURNING id",
                    (name, platform, store_app_id, developer, icon_url),
                )
                res = c.fetchone()
                if res:
                    return res["id"]
                c.execute("SELECT id FROM apps WHERE platform = %s AND store_app_id = %s", (platform, store_app_id))
                return c.fetchone()["id"]
            else:
                c.execute(
                    "INSERT INTO apps(name, platform, store_app_id, developer, icon_url) "
                    "VALUES (?,?,?,?,?) "
                    "ON CONFLICT(platform, store_app_id) DO NOTHING",
                    (name, platform, store_app_id, developer, icon_url),
                )
                row = c.execute(
                    "SELECT id FROM apps WHERE platform = ? AND store_app_id = ?",
                    (platform, store_app_id),
                ).fetchone()
                return row["id"]

    def get_app(self, app_id: int) -> Optional[dict]:
        with self._cursor() as c:
            c.execute(self._param("SELECT * FROM apps WHERE id = ?"), (app_id,))
            return c.fetchone()

    def list_apps(self) -> list[dict]:
        with self._cursor() as c:
            c.execute(self._param("SELECT * FROM apps ORDER BY created_at DESC"))
            return c.fetchall()

    # ---- reviews ----
    def insert_reviews(self, rows: list[tuple]) -> None:
        if not rows: return
        with self._cursor() as c:
            if self.is_postgres:
                from psycopg2.extras import execute_batch
                execute_batch(
                    c,
                    """INSERT INTO reviews
                       (app_id, review_id, title, body, rating, author, author_url,
                        version, country, created_at, sentiment_score, sentiment_label)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                       ON CONFLICT (app_id, review_id) DO NOTHING""",
                    rows,
                )
            else:
                c.executemany(
                    """INSERT OR IGNORE INTO reviews
                       (app_id, review_id, title, body, rating, author, author_url,
                        version, country, created_at, sentiment_score, sentiment_label)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                    rows,
                )

    def count_reviews(self, app_id: int) -> int:
        with self._cursor() as c:
            if self.is_postgres:
                c.execute("SELECT COUNT(*) AS c FROM reviews WHERE app_id = %s", (app_id,))
            else:
                c = c.execute("SELECT COUNT(*) AS c FROM reviews WHERE app_id = ?", (app_id,))
            return c.fetchone()["c"]

    def _review_where(self, app_id: int, q=None, rating=None, min_rating=None,
                      sentiment=None, start_date=None, end_date=None):
        where, params = ["app_id = ?"], [app_id]
        if q:
            like = f"%{q}%"
            where.append(f"(body {'ILIKE' if self.is_postgres else 'LIKE'} ? OR title {'ILIKE' if self.is_postgres else 'LIKE'} ?)")
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
                      page: int = None, page_size: int = 50) -> list[dict]:
        where, params = self._review_where(
            app_id, q=q, rating=rating, min_rating=min_rating, sentiment=sentiment,
            start_date=start_date, end_date=end_date,
        )
        sql = f"SELECT * FROM reviews WHERE {where} ORDER BY created_at DESC"
        if page is not None:
            sql += " LIMIT ? OFFSET ?"
            params += [page_size, (page - 1) * page_size]
        
        with self._cursor() as c:
            if self.is_postgres:
                c.execute(self._param(sql), params)
                return c.fetchall()
            else:
                return c.execute(sql, params).fetchall()

    def count_matching(self, app_id: int, q: str = None, rating: int = None,
                       min_rating: int = None, sentiment: str = None,
                       start_date: str = None, end_date: str = None) -> int:
        where, params = self._review_where(
            app_id, q=q, rating=rating, min_rating=min_rating, sentiment=sentiment,
            start_date=start_date, end_date=end_date,
        )
        with self._cursor() as c:
            if self.is_postgres:
                c.execute(self._param(f"SELECT COUNT(*) AS c FROM reviews WHERE {where}"), params)
                return c.fetchone()["c"]
            else:
                return c.execute(f"SELECT COUNT(*) AS c FROM reviews WHERE {where}", params).fetchone()["c"]

    def get_stats(self, app_id: int) -> dict[str, Any]:
        with self._cursor() as c:
            if self.is_postgres:
                c.execute("SELECT COUNT(*) AS total, AVG(rating) AS avg FROM reviews WHERE app_id = %s", (app_id,))
                agg = c.fetchone()
                c.execute("SELECT rating, COUNT(*) AS count FROM reviews WHERE app_id = %s GROUP BY rating ORDER BY rating", (app_id,))
                dist = c.fetchall()
                c.execute("SELECT sentiment_label AS label, COUNT(*) AS count FROM reviews WHERE app_id = %s GROUP BY sentiment_label ORDER BY count DESC", (app_id,))
                senti = c.fetchall()
                c.execute("SELECT SUBSTRING(created_at FROM 1 FOR 7) AS month, COUNT(*) AS count FROM reviews WHERE app_id = %s GROUP BY month ORDER BY month", (app_id,))
                volume = c.fetchall()
            else:
                agg = c.execute("SELECT COUNT(*) AS total, AVG(rating) AS avg FROM reviews WHERE app_id = ?", (app_id,)).fetchone()
                dist = c.execute("SELECT rating, COUNT(*) AS count FROM reviews WHERE app_id = ? GROUP BY rating ORDER BY rating", (app_id,)).fetchall()
                senti = c.execute("SELECT sentiment_label AS label, COUNT(*) AS count FROM reviews WHERE app_id = ? GROUP BY sentiment_label ORDER BY count DESC", (app_id,)).fetchall()
                volume = c.execute("SELECT substr(created_at, 1, 7) AS month, COUNT(*) AS count FROM reviews WHERE app_id = ? GROUP BY month ORDER BY month", (app_id,)).fetchall()
                
        return {
            "total_reviews": agg["total"],
            "avg_rating": agg["avg"] if agg["avg"] else 0,
            "rating_distribution": [{"rating": r["rating"], "count": r["count"]} for r in dist],
            "sentiment_breakdown": [{"label": r["label"] or "none", "count": r["count"]} for r in senti],
            "volume_over_time": [{"month": r["month"], "count": r["count"]} for r in volume],
        }

    # ---- jobs ----
    def create_job(self, app_id: int, platform: str) -> int:
        with self._cursor() as c:
            if self.is_postgres:
                c.execute(
                    "INSERT INTO jobs(app_id, platform, status, total_target, fetched_count) "
                    "VALUES (%s,%s,%s,%s,%s) RETURNING id",
                    (app_id, platform, "running", None, 0),
                )
                return c.fetchone()["id"]
            else:
                cur = c.execute(
                    "INSERT INTO jobs(app_id, platform, status, total_target, fetched_count) "
                    "VALUES (?,?,?,?,?)",
                    (app_id, platform, "running", None, 0),
                )
                return cur.lastrowid

    def get_job(self, job_id: int) -> Optional[dict]:
        with self._cursor() as c:
            if self.is_postgres:
                c.execute("SELECT * FROM jobs WHERE id = %s", (job_id,))
                return c.fetchone()
            else:
                return c.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()

    def finish_job(self, job_id: int, status: str, fetched_count: int, message: str = None) -> None:
        with self._cursor() as c:
            if self.is_postgres:
                c.execute(
                    "UPDATE jobs SET status = %s, fetched_count = %s, message = %s WHERE id = %s",
                    (status, fetched_count, message, job_id),
                )
            else:
                c.execute(
                    "UPDATE jobs SET status = ?, fetched_count = ?, message = ? WHERE id = ?",
                    (status, fetched_count, message, job_id),
                )