import xml.etree.ElementTree as ET

import requests

from .base import AppCandidate, PlatformScraper, ReviewItem, to_iso

ITUNES_SEARCH_URL = "https://itunes.apple.com/search"
RSS_REVIEWS_URL = ("https://itunes.apple.com/{country}/rss/customerreviews/"
                   "page={page}/id={app_id}/sortby=mostrecent/xml")
ATOM_NS = "http://www.w3.org/2005/Atom"
IM_NS = "http://itunes.apple.com/rss"
NS = {"a": ATOM_NS, "im": IM_NS}

# Apple's public RSS feed caps at 10 pages of 50 reviews (500 max per country).
MAX_PAGES = 10
BATCH_SIZE = 50
PAGE_SLEEP_SECONDS = 0.3


class AppStoreScraper(PlatformScraper):
    platform = "appstore"

    def search(self, query: str, limit: int = 20) -> list[AppCandidate]:
        resp = requests.get(
            ITUNES_SEARCH_URL,
            params={"term": query, "country": "in", "entity": "software", "limit": limit},
            timeout=30,
        )
        resp.raise_for_status()
        results = resp.json().get("results", [])
        candidates = []
        for r in results:
            try:
                # Skip if not a dict or missing trackId
                if not isinstance(r, dict) or not r.get("trackId"):
                    continue
                
                candidate = AppCandidate(
                    platform=self.platform,
                    store_app_id=str(r.get("trackId", "")),
                    name=str(r.get("trackName", "")) if r.get("trackName") else "",
                    developer=str(r.get("sellerName", "")) if r.get("sellerName") else None,
                    icon_url=str(r.get("artworkUrl100", "")) if r.get("artworkUrl100") else None,
                    rating=float(r.get("averageUserRating", 0)) if r.get("averageUserRating") else None,
                )
                candidates.append(candidate)
            except (TypeError, ValueError, AttributeError):
                # Skip malformed results
                continue
        return candidates

    def estimate_total_reviews(self, app_id: str, country: str = "in") -> int:
        """Apple RSS feed maxes out at 10 pages x 50 reviews = 500 total"""
        return 500  # Apple's hard limit per country

    def review_batches(self, app_id: str, country: str = "in"):
        for page in range(1, MAX_PAGES + 1):
            url = RSS_REVIEWS_URL.format(country=country, page=page, app_id=app_id)
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            root = ET.fromstring(resp.content)
            entries = root.findall("a:entry", NS)
            if not entries:
                break
            yield [self._to_item(e) for e in entries]
            if len(entries) < BATCH_SIZE:
                break

    @staticmethod
    def _to_item(e) -> ReviewItem:
        def txt(tag):
            el = e.find(tag, NS)
            return el.text.strip() if el is not None and el.text else None

        author = e.find("a:author/a:name", NS)
        rating = txt("im:rating")
        return ReviewItem(
            review_id=txt("a:id") or "",
            title=txt("a:title") or "",
            body=txt("a:content") or "",
            rating=int(rating or 0),
            author=author.text if author is not None and author.text else "",
            author_url=None,
            version=txt("im:version"),
            created_at=to_iso(txt("a:updated")),
        )
