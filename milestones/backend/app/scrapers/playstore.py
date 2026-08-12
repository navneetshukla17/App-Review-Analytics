import time

from google_play_scraper import Sort
from google_play_scraper import reviews as gp_reviews
from google_play_scraper import search as gp_search

from .base import AppCandidate, PlatformScraper, ReviewItem, to_iso

PAGE_SIZE = 200
PAGE_SLEEP_SECONDS = 0.5


class PlayStoreScraper(PlatformScraper):
    platform = "playstore"

    def search(self, query: str, limit: int = 20) -> list[AppCandidate]:
        results = gp_search(query, lang="en", country="in", n_hits=limit)
        return [
            AppCandidate(
                platform=self.platform,
                store_app_id=r.get("appId", ""),
                name=r.get("title", ""),
                developer=r.get("developer"),
                icon_url=r.get("icon"),
                rating=r.get("score"),
            )
            for r in results
            if r.get("appId")
        ]

    def review_batches(self, app_id: str, country: str = "in"):
        token = None
        while True:
            result, token = gp_reviews(
                app_id,
                lang="en",
                country=country,
                sort=Sort.NEWEST,
                count=PAGE_SIZE,
                continuation_token=token,
            )
            if result:
                yield [self._to_item(r) for r in result]
            if not token:
                break
            time.sleep(PAGE_SLEEP_SECONDS)

    @staticmethod
    def _to_item(r) -> ReviewItem:
        return ReviewItem(
            review_id=str(r.get("reviewId") or ""),
            title="",
            body=r.get("content") or "",
            rating=int(r.get("score") or 0),
            author=r.get("userName") or "",
            author_url=r.get("userImage"),
            version=r.get("reviewCreatedVersion"),
            created_at=to_iso(r.get("at")),
        )
