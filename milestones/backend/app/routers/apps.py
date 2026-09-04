from fastapi import APIRouter, HTTPException, Query, Request

from ..scrapers.search import search_apps, SCRAPERS
from ..schemas import AppCreate, AppOut, AppSearchResult, SearchResponse

router = APIRouter(prefix="/api/apps", tags=["apps"])


@router.get("/search", response_model=SearchResponse)
def search(request: Request, q: str = Query(..., min_length=1), platform: str = "both"):
    if platform not in ("playstore", "appstore", "both"):
        raise HTTPException(400, "platform must be 'playstore', 'appstore' or 'both'")
    results, errors = search_apps(q, platform)
    
    # Sort results by relevance: exact matches first, then partial matches, then by rating
    query_lower = q.lower()
    
    def relevance_score(app):
        name_lower = app.name.lower()
        # Exact match scores highest
        if name_lower == query_lower:
            return (0, app.rating or 0)
        # Starts with query scores second
        elif name_lower.startswith(query_lower):
            return (1, app.rating or 0)
        # Contains query scores third
        elif query_lower in name_lower:
            return (2, app.rating or 0)
        # Everything else
        else:
            return (3, app.rating or 0)
    
    sorted_results = sorted(results, key=relevance_score, reverse=False)
    return SearchResponse(results=[AppSearchResult(**r.__dict__) for r in sorted_results], errors=errors)


@router.post("", response_model=AppOut)
def create_app(request: Request, body: AppCreate):
    db = request.app.state.db
    app_id = db.create_app(body.name, body.platform, body.store_app_id,
                           body.developer, body.icon_url)
    row = db.get_app(app_id)
    return AppOut(id=row["id"], name=row["name"], platform=row["platform"],
                  store_app_id=row["store_app_id"], developer=row["developer"],
                  icon_url=row["icon_url"])


@router.get("/{app_id}/review-estimate")
def estimate_reviews(request: Request, app_id: int):
    """Estimate total available reviews for an app"""
    db = request.app.state.db
    app_row = db.get_app(app_id)
    if app_row is None:
        raise HTTPException(404, "App not found")
    
    scraper = SCRAPERS.get(app_row["platform"])
    if scraper is None:
        raise HTTPException(500, f"Scraper not found for platform: {app_row['platform']}")
    
    try:
        # Try to estimate by checking first batch
        estimate = scraper.estimate_total_reviews(app_row["store_app_id"])
        
        # Get already fetched count
        fetched_count = db.count_reviews(app_id)
        
        # Suggest batch sizes based on estimate
        suggestions = []
        if estimate > 5000:
            suggestions.append({"label": "5K", "value": 5000})
        if estimate > 10000:
            suggestions.append({"label": "10K", "value": 10000})
        if estimate > 25000:
            suggestions.append({"label": "25K", "value": 25000})
        if estimate > 50000:
            suggestions.append({"label": "50K", "value": 50000})
        if estimate > 100000:
            suggestions.append({"label": "100K", "value": 100000})
        suggestions.append({"label": "All", "value": None})
        
        return {
            "total_available": estimate,
            "already_fetched": fetched_count,
            "remaining": max(0, estimate - fetched_count),
            "suggestions": suggestions,
            "estimated_cycles": max(1, (estimate - fetched_count) // 10000 + 1) if estimate > 0 else 1
        }
    except Exception as e:
        raise HTTPException(500, f"Failed to estimate reviews: {str(e)}")


@router.get("", response_model=list[AppOut])
def list_apps(request: Request):
    db = request.app.state.db
    return [AppOut(id=r["id"], name=r["name"], platform=r["platform"],
                   store_app_id=r["store_app_id"], developer=r["developer"],
                   icon_url=r["icon_url"]) for r in db.list_apps()]
