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
