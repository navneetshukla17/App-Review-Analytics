from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class AppCandidate:
    platform: str
    store_app_id: str
    name: str
    developer: str | None = None
    icon_url: str | None = None
    rating: float | None = None


@dataclass
class ReviewItem:
    review_id: str
    title: str
    body: str
    rating: int
    author: str
    author_url: str | None
    version: str | None
    created_at: str | None


class PlatformScraper(ABC):
    platform: str

    @abstractmethod
    def search(self, query: str, limit: int = 20) -> list[AppCandidate]:
        ...

    @abstractmethod
    def review_batches(self, app_id: str, country: str = "in"):
        """Yield list[ReviewItem] batches, one page at a time."""
        ...

    def estimate_total_reviews(self, app_id: str, country: str = "in") -> int:
        """Estimate total available reviews. Override in subclass for accuracy."""
        return 10000  # Default conservative estimate


def to_iso(value) -> str | None:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)
