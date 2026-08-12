from app.scrapers.appstore import AppStoreScraper
from app.scrapers.base import AppCandidate, ReviewItem

REVIEW_XML = """<?xml version="1.0" encoding="utf-8"?>
<feed xmlns:im="http://itunes.apple.com/rss" xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>100</id>
    <title>Love it</title>
    <content type="text">great app</content>
    <im:rating>5</im:rating>
    <im:version>1.2</im:version>
    <author><name>bob</name></author>
    <updated>2024-03-01T09:30:00-07:00</updated>
  </entry>
</feed>
"""

EMPTY_FEED = '<?xml version="1.0" encoding="utf-8"?><feed xmlns="http://www.w3.org/2005/Atom"></feed>'


class FakeResp:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload

    @property
    def content(self):
        return self._payload


def test_search_maps_results(monkeypatch):
    payload = {
        "results": [
            {"trackId": 389801252, "trackName": "Instagram", "sellerName": "Instagram, Inc.",
             "artworkUrl100": "http://icon", "averageUserRating": 4.7},
        ]
    }

    def fake_get(url, **kwargs):
        assert kwargs["params"]["country"] == "in"
        assert kwargs["params"]["entity"] == "software"
        return FakeResp(payload)

    monkeypatch.setattr("app.scrapers.appstore.requests.get", fake_get)
    results = AppStoreScraper().search("instagram")
    assert results[0] == AppCandidate("appstore", "389801252", "Instagram", "Instagram, Inc.",
                                      "http://icon", 4.7)


def test_review_batches_maps_reviews(monkeypatch):
    calls = {"n": 0}

    def fake_get(url, **kwargs):
        calls["n"] += 1
        assert "customerreviews" in url
        return FakeResp(REVIEW_XML if calls["n"] == 1 else EMPTY_FEED)

    monkeypatch.setattr("app.scrapers.appstore.requests.get", fake_get)
    batches = list(AppStoreScraper().review_batches("389801252"))
    assert calls["n"] == 1
    assert len(batches) == 1
    item = batches[0][0]
    assert isinstance(item, ReviewItem)
    assert item.review_id == "100"
    assert item.body == "great app"
    assert item.rating == 5
    assert item.author == "bob"
    assert item.version == "1.2"
    assert item.created_at == "2024-03-01T09:30:00-07:00"
