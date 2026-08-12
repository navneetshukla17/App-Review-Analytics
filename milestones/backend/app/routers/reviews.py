import csv
import io
import json

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
        return StreamingResponse(
            iter([json.dumps(payload, indent=2)]),
            media_type="application/json",
            headers={"Content-Disposition": 'attachment; filename="reviews.json"'},
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
