import threading

from fastapi import APIRouter, HTTPException, Query, Request

from ..jobs import run_fetch_job
from ..schemas import JobOut

router = APIRouter(prefix="/api", tags=["jobs"])


@router.post("/apps/{app_id}/fetch", response_model=JobOut)
def start_fetch(request: Request, app_id: int, limit: int = Query(None)):
    db = request.app.state.db
    registry = request.app.state.registry
    app_row = db.get_app(app_id)
    if app_row is None:
        raise HTTPException(404, "App not found")
    job_id = db.create_job(app_id, app_row["platform"])
    state = registry.create(job_id, app_id)
    threading.Thread(
        target=run_fetch_job,
        args=(db, registry, job_id, limit),
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
