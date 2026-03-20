import json

from urllib.error import HTTPError

from cybersentinel.collector import CollectorClient


class FakeResponse:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


def test_github_collector_formats_results() -> None:
    requests: list[object] = []

    def fake_opener(request: object, timeout: int = 15) -> FakeResponse:
        requests.append(request)
        return FakeResponse(
            {
                "items": [
                    {
                        "repository": {"full_name": "acme/public-repo"},
                        "path": "src/app.py",
                        "html_url": "https://github.com/acme/public-repo/blob/main/src/app.py",
                        "text_matches": [
                            {"fragment": "AWS_SECRET_ACCESS_KEY=abcd1234"},
                        ],
                    }
                ]
            }
        )

    collector = CollectorClient(github_token="token123", opener=fake_opener)
    record = collector.collect("github", "acme password")

    assert record.source == "github"
    assert "acme/public-repo" in record.raw_text
    assert "AWS_SECRET_ACCESS_KEY=abcd1234" in record.raw_text
    assert "snippet:\nAWS_SECRET_ACCESS_KEY=abcd1234" in record.raw_text
    assert requests[0].full_url.endswith("/search/code?q=acme%20password&per_page=5&page=1")
    assert requests[0].headers["Authorization"] == "Bearer token123"

def test_empty_results_returns_empty_string() -> None:
    def fake_opener(request: object, timeout: int = 15) -> FakeResponse:
        return FakeResponse({"items": []})

    collector = CollectorClient(opener=fake_opener)
    record = collector.collect("github", "no hits")
    assert record.raw_text == ""


def test_collector_rejects_unknown_sources() -> None:
    collector = CollectorClient()

    try:
        collector.collect("pastebin", "acme password")
    except ValueError as exc:
        assert "Unsupported source" in str(exc)
    else:
        raise AssertionError("Collector should reject unknown sources.")


def test_malformed_json_falls_back_to_offline_text() -> None:
    class BadResponse:
        def __enter__(self) -> "BadResponse":
            return self
        def __exit__(self, exc_type, exc, tb) -> None:
            return None
        def read(self) -> bytes:
            return b"{not json"

    def fake_opener(request: object, timeout: int = 15) -> BadResponse:
        return BadResponse()

    collector = CollectorClient(opener=fake_opener, offline_text="OFFLINE_FIXTURE")
    record = collector.collect("github", "acme")
    assert record.raw_text == "OFFLINE_FIXTURE"


def test_rate_limit_error_falls_back_to_offline_text() -> None:
    def fake_opener(request: object, timeout: int = 15) -> FakeResponse:
        raise HTTPError(
            request.full_url,
            403,
            "Forbidden",
            hdrs={"X-RateLimit-Remaining": "0", "Retry-After": "60"},
            fp=None,
        )

    collector = CollectorClient(opener=fake_opener, offline_text="OFFLINE_FIXTURE")
    record = collector.collect("github", "acme")
    assert record.raw_text == "OFFLINE_FIXTURE"


def test_offline_mode_uses_offline_text_without_network() -> None:
    def fake_opener(request: object, timeout: int = 15) -> FakeResponse:
        raise AssertionError("Network should not be called in offline mode.")

    collector = CollectorClient(opener=fake_opener, offline_mode=True, offline_text="OFFLINE_FIXTURE")
    record = collector.collect("github", "acme")
    assert record.raw_text == "OFFLINE_FIXTURE"


def test_malformed_item_shapes_do_not_crash_and_return_normalized_text() -> None:
    def fake_opener(request: object, timeout: int = 15) -> FakeResponse:
        return FakeResponse(
            {
                "items": [
                    {
                        "repository": None,
                        "path": None,
                        "html_url": None,
                        "text_matches": None,
                    }
                ]
            }
        )

    collector = CollectorClient(opener=fake_opener)
    record = collector.collect("github", "acme")
    assert "repository: unknown" in record.raw_text
    assert "snippet:" in record.raw_text
