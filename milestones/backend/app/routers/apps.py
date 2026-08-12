from fastapi import APIRouter, HTTPException, Query, Request

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
