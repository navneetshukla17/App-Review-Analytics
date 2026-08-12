# Store Reviews Fetcher — Design

**Date:** 2026-08-12

## Goal

A web app where a user enters an app name and a platform (`playstore`, `appstore`, or `both`), resolves the name to the correct app(s), and fetches **all** available reviews (India locale) into a SQLite database. The user can then search, filter, chart, analyze sentiment, and export the review data in a structured manner.

## Architecture

- **Backend:** FastAPI (`backend/`) with SQLite storage (`review_data.db`).
- **Frontend:** React + Vite (`frontend/`). Dev server on `:5173` proxies API calls to FastAPI on `:8000`. The production React build is served statically by FastAPI.
- **Scrapers:** `google-play-scraper` and `app-store-scraper` (Python), wrapped behind a thin abstraction layer exposing `search()` and `fetch_all_reviews()`. Nothing outside the scraper modules depends on the libraries directly, so a library can be swapped or patched without touching the rest of the app.
- **Fetches:** run as background jobs with progress polling so long fetches do not block API requests.

## Data model (SQLite)

```sql
apps(id INTEGER PK, name TEXT, platform TEXT, store_app_id TEXT,
     developer TEXT, icon_url TEXT, created_at TEXT,
     UNIQUE(platform, store_app_id))

reviews(id INTEGER PK, app_id INTEGER FK, review_id TEXT, title TEXT, body TEXT,
        rating INTEGER, author TEXT, author_url TEXT, version TEXT,
        country TEXT, created_at TEXT, fetched_at TEXT,
        sentiment_score REAL, sentiment_label TEXT,
        UNIQUE(app_id, review_id))

jobs(id INTEGER PK, app_id INTEGER FK, platform TEXT, status TEXT,
     total_target INTEGER, fetched_count INTEGER, message TEXT, created_at TEXT)
```

- One `apps` row per (platform, store_app_id); selecting "both" creates two rows.
- `UNIQUE(app_id, review_id)` dedupes reviews on re-fetch.
- `jobs` powers the live progress bar in the UI.

## API endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/apps/search?q=&platform=` | Resolve app name → candidate list |
| `POST` | `/api/apps` | Create app row(s) for a selected candidate |
| `GET` | `/api/apps` | List previously fetched apps |
| `GET` | `/api/apps/{id}/reviews` | Reviews with filters: `q`, `rating`, `min_rating`, `sentiment`, `start_date`, `end_date`, `page`, `page_size` |
| `GET` | `/api/apps/{id}/stats` | Avg rating, rating distribution, volume over time, sentiment breakdown |
| `POST` | `/api/apps/{id}/fetch` | Start a background fetch job |
| `GET` | `/api/jobs/{id}` | Poll job progress |
| `GET` | `/api/apps/{id}/export?format=csv\|json` | Download all (filtered) reviews |

## Frontend (2 pages)

1. **Search & Fetch** — app name + platform selector → show candidate results → pick the right app → "Fetch reviews" with live progress bar → auto-navigate to dashboard when done.
2. **Dashboard** — app selector (from fetched apps), stat cards (total reviews, avg rating), charts (rating distribution bar, volume-over-time line, sentiment donut via Recharts), filter bar (keyword, rating, sentiment, date range), reviews table, CSV/JSON export buttons.

## Sentiment

- Computed per review at fetch time using TextBlob polarity.
- Label thresholds: polarity > 0.05 → `positive`, < -0.05 → `negative`, else `neutral`.
- Stored in `reviews.sentiment_score` / `reviews.sentiment_label` so filtering and aggregation are instant.

## Scraping & job pipeline

1. `search(name, platform)` returns candidates (name, app_id, developer, icon_url, rating) via the abstraction layer.
2. User selects a candidate → `POST /api/apps` creates the app row(s).
3. `POST /api/apps/{id}/fetch` starts a background job (FastAPI `BackgroundTasks` + in-memory job registry).
4. The job paginates with `reviews_all()` semantics, country fixed to India (`in`), writing each page to SQLite and updating `jobs.fetched_count`.
5. Re-fetching upserts new reviews without duplicating existing ones.
6. Long fetches survive page refreshes (job state in memory). If the server restarts mid-fetch, the job is marked failed and partial data remains in the DB.

## Error handling

- Library failures (endpoint changes, rate limits) produce a clear job error message.
- Pagination loops are wrapped in try/except with a configurable delay between requests to avoid hammering the stores.
- The scraper abstraction layer allows swapping/patching a library without touching API or frontend code.

## Testing

- Backend: `pytest` for API + SQLite layer (search endpoint with mocked scraper, dedupe on re-fetch, stats/filter query correctness, export format).
- Scrapers: unit tests with mocked library responses; a live smoke test script for one known app (e.g. "Instagram") on both platforms, run manually once.
- Frontend: `vitest` + React Testing Library for the search form and dashboard filter logic. No browser E2E in v1 (covered by the manual smoke test).

## Project layout

```
milestones/
  backend/    requirements.txt, app/ (FastAPI), tests/
  frontend/   Vite React app, src/, tests/
  docs/superpowers/specs/2026-08-12-store-reviews-fetcher-design.md
  README.md
```

## Out of scope (v1)

- Auth / multi-user
- Scheduled re-fetching
- Non-India locales
- Anything beyond the single SQLite database
