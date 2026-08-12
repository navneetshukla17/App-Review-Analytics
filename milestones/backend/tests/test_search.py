from app.scrapers.search import SCRAPERS, search_apps


class FakeScraper:
    platform = "fake"

    def __init__(self, results):
        self._results = results

    def search(self, query, limit=20):
        return self._results


def test_search_apps_single_platform():
    fake = FakeScraper(["candidate"])
    old = SCRAPERS["playstore"]
    SCRAPERS["playstore"] = fake
    try:
        results, errors = search_apps("spotify", "playstore")
        assert results == ["candidate"]
        assert errors == []
    finally:
        SCRAPERS["playstore"] = old


def test_search_apps_isolates_platform_failures():
    def boom(query, limit=20):
        raise RuntimeError("store down")

    old_ps, old_as = SCRAPERS["playstore"], SCRAPERS["appstore"]
    try:
        SCRAPERS["playstore"] = FakeScraper(["play_candidate"])
        SCRAPERS["appstore"] = FakeScraper([])
        SCRAPERS["appstore"].search = boom
        results, errors = search_apps("spotify", "both")
        assert results == ["play_candidate"]
        assert errors and errors[0]["platform"] == "appstore"
    finally:
        SCRAPERS["playstore"], SCRAPERS["appstore"] = old_ps, old_as


def test_search_apps_unknown_platform():
    results, errors = search_apps("spotify", "bogus")
    assert results == []
    assert len(errors) == 1
