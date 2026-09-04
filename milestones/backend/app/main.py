import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .db import Database
from .jobs import JobRegistry
from .routers import apps, jobs, reviews

_default_db_path = Path(__file__).resolve().parent.parent / "review_data.db"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{_default_db_path}")
FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"


def create_app(db: Database, registry: JobRegistry) -> FastAPI:
    app = FastAPI(title="Store Reviews Fetcher")
    app.state.db = db
    app.state.registry = registry
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(apps.router)
    app.include_router(reviews.router)
    app.include_router(jobs.router)
    if FRONTEND_DIST.exists():
        from fastapi.responses import FileResponse
        
        # Serve static assets directly
        app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets", html=True), name="assets")
        
        # Serve index.html for all other routes to support client-side routing (React Router)
        @app.get("/{full_path:path}", include_in_schema=False)
        def serve_react_app(full_path: str):
            if full_path.startswith("api/"):
                from fastapi import HTTPException
                raise HTTPException(status_code=404, detail="API route not found")
            return FileResponse(FRONTEND_DIST / "index.html")
    return app


_db = Database(DATABASE_URL)
_registry = JobRegistry()
app = create_app(_db, _registry)
