from .appstore import AppStoreScraper
from .base import AppCandidate
from .playstore import PlayStoreScraper

SCRAPERS: dict[str, object] = {
    "playstore": PlayStoreScraper(),
    "appstore": AppStoreScraper(),
}


def search_apps(query: str, platform: str, limit: int = 20) -> tuple[list[AppCandidate], list[dict]]:
    errors: list[dict] = []
    results: list[AppCandidate] = []
    targets = [platform] if platform != "both" else list(SCRAPERS)
    for name in targets:
        scraper = SCRAPERS.get(name)
        if scraper is None:
            errors.append({"platform": name, "message": f"Unknown platform: {name}"})
            continue
        try:
            platform_results = scraper.search(query, limit)
            # Filter out any None or invalid results
            valid_results = [r for r in platform_results if r and r.name and r.store_app_id]
            results.extend(valid_results)
        except TypeError as exc:
            errors.append({"platform": name, "message": f"Data format error: {str(exc)}"})
        except Exception as exc:  # noqa: BLE001 - isolate store failures
            errors.append({"platform": name, "message": str(exc)})
    return results, errors
