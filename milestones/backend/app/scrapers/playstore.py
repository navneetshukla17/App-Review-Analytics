import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from google_play_scraper import Sort
from google_play_scraper import reviews as gp_reviews
from google_play_scraper import search as gp_search

from .base import AppCandidate, PlatformScraper, ReviewItem, to_iso

PAGE_SIZE = 200
PAGE_SLEEP_SECONDS = 0.1  # Reduced from 0.5 to 0.1
MAX_WORKERS = 3  # Fetch up to 3 pages concurrently


class PlayStoreScraper(PlatformScraper):
    platform = "playstore"

    def search(self, query: str, limit: int = 20) -> list[AppCandidate]:
        results = gp_search(query, lang="en", country="in", n_hits=limit)
        candidates = []
        for r in results:
            try:
                # Skip if not a dict or missing appId
                if not isinstance(r, dict) or not r.get("appId"):
                    continue
                
                candidate = AppCandidate(
                    platform=self.platform,
                    store_app_id=str(r.get("appId", "")),
                    name=str(r.get("title", "")) if r.get("title") else "",
                    developer=str(r.get("developer", "")) if r.get("developer") else None,
                    icon_url=str(r.get("icon", "")) if r.get("icon") else None,
                    rating=float(r.get("score", 0)) if r.get("score") else None,
                )
                candidates.append(candidate)
            except (TypeError, ValueError, AttributeError):
                # Skip malformed results
                continue
        return candidates

    def estimate_total_reviews(self, app_id: str, country: str = "in") -> int:
        """Estimate total reviews by fetching the first batch and analyzing metadata"""
        try:
            result, token = gp_reviews(
                app_id,
                lang="en",
                country=country,
                sort=Sort.NEWEST,
                count=10,
            )
            # Google Play Scraper doesn't provide total count, so estimate conservatively
            # Based on availability of continuation token
            if token:
                return 50000  # Indicates there are many more reviews
            return len(result) if result else 0
        except:
            return 10000  # Default estimate on error

    def _fetch_page(self, app_id: str, country: str, token: str = None):
        """Fetch a single page of reviews"""
        result, next_token = gp_reviews(
            app_id,
            lang="en",
            country=country,
            sort=Sort.NEWEST,
            count=PAGE_SIZE,
            continuation_token=token,
        )
        if result:
            return [self._to_item(r) for r in result], next_token
        return [], next_token

    def review_batches(self, app_id: str, country: str = "in"):
        """Fetch reviews with concurrent requests for speed"""
        token = None
        batch_queue = []
        
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {}
            next_token = None
            page_count = 0
            
            # Pre-fill with initial requests
            for _ in range(MAX_WORKERS):
                if next_token is None and page_count == 0:
                    next_token = None
                future = executor.submit(self._fetch_page, app_id, country, next_token)
                futures[future] = next_token
                next_token = None  # Will be updated as we get results
                page_count += 1
            
            # Process completed futures and submit new ones
            while futures:
                for future in as_completed(futures):
                    items, returned_token = future.result()
                    token = futures.pop(future)
                    
                    if items:
                        yield items
                    
                    # If there are more pages, submit new fetch
                    if returned_token:
                        time.sleep(PAGE_SLEEP_SECONDS)  # Small delay to avoid rate limiting
                        new_future = executor.submit(self._fetch_page, app_id, country, returned_token)
                        futures[new_future] = returned_token
                    
                    break  # Process one at a time to maintain order

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
