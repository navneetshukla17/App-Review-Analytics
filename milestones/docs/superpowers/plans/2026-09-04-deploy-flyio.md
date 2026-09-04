# Fly.io Deployment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deploy the FastAPI + React application to Fly.io using a multi-stage Dockerfile and SQLite on a persistent volume.

**Architecture:** We will create a `Dockerfile` that first builds the React frontend in a Node environment, then sets up a Python environment for the FastAPI backend, copies the built frontend assets over, and runs Uvicorn. The backend will read the database path from an environment variable (`DB_PATH`), which will point to a Fly.io volume.

**Tech Stack:** Docker, Fly.io, FastAPI, React, SQLite

---

### Task 1: Update Database Path Configuration

**Files:**
- Modify: `backend/app/main.py`

- [ ] **Step 1: Read DB path from environment variable**

```python
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .db import Database
from .jobs import JobRegistry
from .routers import apps, jobs, reviews

_default_db_path = Path(__file__).resolve().parent.parent / "review_data.db"
DB_PATH = Path(os.getenv("DB_PATH", _default_db_path))
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

- [ ] **Step 2: Commit**

```bash
git add backend/app/main.py
git commit -m "chore: make DB path configurable via environment variable for deployment"
```

### Task 2: Create Dockerfile and Dockerignore

**Files:**
- Create: `Dockerfile`
- Create: `.dockerignore`

- [ ] **Step 1: Create the `.dockerignore` file**

```text
node_modules/
backend/.venv/
.git/
.env
__pycache__/
*.pyc
backend/review_data.db
```

- [ ] **Step 2: Create the `Dockerfile`**

```dockerfile
# Stage 1: Build the React frontend
FROM node:18-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Setup FastAPI backend
FROM python:3.13-slim
WORKDIR /app

# Install system dependencies needed for python packages (if any)
RUN apt-get update && apt-get install -y --no-install-recommends \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy backend code
COPY backend/ ./backend/

# Copy built frontend assets
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

# Expose the port
EXPOSE 8000

# Set environment variables
ENV HOST=0.0.0.0
ENV PORT=8000
# The DB_PATH will be overridden by Fly.io to point to the volume
ENV DB_PATH=/app/data/review_data.db

# Run uvicorn
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 3: Commit**

```bash
git add Dockerfile .dockerignore
git commit -m "chore: add multi-stage Dockerfile and dockerignore"
```

### Task 3: Create Fly.io Configuration

**Files:**
- Create: `fly.toml`

- [ ] **Step 1: Generate fly.toml**

```toml
# fly.toml app configuration file generated for review-insights

app = "review-insights-prod" # Note: user may need to change this if taken
primary_region = "ewr"

[build]
  dockerfile = "Dockerfile"

[[mounts]]
  source = "review_data_vol"
  destination = "/app/data"

[http_service]
  internal_port = 8000
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 0
  processes = ["app"]
```

- [ ] **Step 2: Commit**

```bash
git add fly.toml
git commit -m "chore: add fly.toml configuration with volume mount"
```
