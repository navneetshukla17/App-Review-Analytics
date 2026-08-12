from typing import Optional

from pydantic import BaseModel, Field, field_validator

PLATFORMS = {"playstore", "appstore"}


class AppSearchResult(BaseModel):
    platform: str
    store_app_id: str
    name: str
    developer: Optional[str] = None
    icon_url: Optional[str] = None
    rating: Optional[float] = None


class SearchResponse(BaseModel):
    results: list[AppSearchResult] = Field(default_factory=list)
    errors: list[dict] = Field(default_factory=list)


class AppCreate(BaseModel):
    name: str
    platform: str
    store_app_id: str
    developer: Optional[str] = None
    icon_url: Optional[str] = None

    @field_validator("platform")
    @classmethod
    def _check_platform(cls, v):
        if v not in PLATFORMS:
            raise ValueError("platform must be 'playstore' or 'appstore'")
        return v


class AppOut(BaseModel):
    id: int
    name: str
    platform: str
    store_app_id: str
    developer: Optional[str] = None
    icon_url: Optional[str] = None


class ReviewOut(BaseModel):
    id: int
    review_id: Optional[str] = None
    title: str
    body: str
    rating: int
    author: str
    version: Optional[str] = None
    created_at: Optional[str] = None
    sentiment_label: str


class ReviewPage(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[ReviewOut]


class JobOut(BaseModel):
    id: int
    app_id: int
    status: str
    fetched_count: int
    message: Optional[str] = None
