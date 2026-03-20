import json
from urllib.error import HTTPError, URLError

from cybersentinel.collector import CollectorClient, CollectorError


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


class FakeSecretsClient:
    def get_secret_value(self, SecretId: str) -> dict[str, str]:
        assert SecretId == "arn:aws:secretsmanager:us-east-1:123:secret:github-token"
        return {"SecretString": '{"token":"secret-token-123"}'}


def test_collector_loads_github_token_from_secret() -> None:
    requests: list[object] = []

    def fake_opener(request: object, timeout: int = 15) -> FakeResponse:
        requests.append(request)
        return FakeResponse({"items": []})

    collector = CollectorClient(
        github_token_secret_arn="arn:aws:secretsmanager:us-east-1:123:secret:github-token",
        opener=fake_opener,
        secrets_client=FakeSecretsClient(),
    )
    collector.collect("github", "acme password")

    assert requests[0].headers["Authorization"] == "Bearer secret-token-123"


def test_collector_rejects_unknown_sources() -> None:
    collector = CollectorClient()

    try:
        collector.collect("pastebin", "acme password")
    except ValueError as exc:
        assert "Unsupported source" in str(exc)
    else:
        raise AssertionError("Collector should reject unknown sources.")


def test_collector_retries_retryable_http_error() -> None:
    attempts: list[int] = []
    sleeps: list[float] = []

    def fake_opener(request: object, timeout: int = 15) -> FakeResponse:
        attempts.append(1)
        if len(attempts) < 3:
            raise HTTPError(
                request.full_url,
                503,
                "Service unavailable",
                hdrs={},
                fp=None,
            )
        return FakeResponse({"items": []})

    collector = CollectorClient(
        opener=fake_opener,
        sleeper=lambda seconds: sleeps.append(seconds),
        max_attempts=3,
        backoff_seconds=0.25,
    )
    record = collector.collect("github", "acme password")

    assert record.raw_text == ""
    assert len(attempts) == 3
    assert sleeps == [0.25, 0.5]


def test_collector_raises_clear_rate_limit_error() -> None:
    def fake_opener(request: object, timeout: int = 15) -> FakeResponse:
        raise HTTPError(
            request.full_url,
            403,
            "Forbidden",
            hdrs={
                "Retry-After": "60",
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": "9999999999",
            },
            fp=None,
        )

    collector = CollectorClient(
        opener=fake_opener,
        sleeper=lambda seconds: None,
        max_attempts=1,
    )

    try:
        collector.collect("github", "acme password")
    except CollectorError as exc:
        message = str(exc)
        assert "rate limit" in message.lower()
        assert "retry_after=60" in message
    else:
        raise AssertionError("Collector should raise a rate-limit error.")


def test_collector_raises_on_network_failure_after_retries() -> None:
    sleeps: list[float] = []

    def fake_opener(request: object, timeout: int = 15) -> FakeResponse:
        raise URLError("temporary dns failure")

    collector = CollectorClient(
        opener=fake_opener,
        sleeper=lambda seconds: sleeps.append(seconds),
        max_attempts=2,
        backoff_seconds=0.5,
    )

    try:
        collector.collect("github", "acme password")
    except CollectorError as exc:
        assert "temporary dns failure" in str(exc)
    else:
        raise AssertionError("Collector should raise a network failure error.")

    assert sleeps == [0.5]


def test_collector_paginates_until_short_page() -> None:
    requests: list[object] = []

    def fake_opener(request: object, timeout: int = 15) -> FakeResponse:
        requests.append(request)
        if "page=1" in request.full_url:
            return FakeResponse(
                {
                    "items": [
                        {
                            "repository": {"full_name": "acme/repo-one"},
                            "path": "src/a.py",
                            "html_url": "https://github.com/acme/repo-one/blob/main/src/a.py",
                            "text_matches": [{"fragment": "line one\n\nline two"}],
                        },
                        {
                            "repository": {"full_name": "acme/repo-two"},
                            "path": "src/b.py",
                            "html_url": "https://github.com/acme/repo-two/blob/main/src/b.py",
                            "text_matches": [{"fragment": "another line"}],
                        },
                    ]
                }
            )
        return FakeResponse(
            {
                "items": [
                    {
                        "repository": {"full_name": "acme/repo-three"},
                        "path": "src/c.py",
                        "html_url": "https://github.com/acme/repo-three/blob/main/src/c.py",
                        "text_matches": [{"fragment": "final line"}],
                    }
                ]
            }
        )

    collector = CollectorClient(opener=fake_opener, per_page=2, max_pages=3)
    record = collector.collect("github", "acme password")

    assert len(requests) == 2
    assert "acme/repo-one" in record.raw_text
    assert "acme/repo-three" in record.raw_text
    assert "line one\nline two" in record.raw_text


def test_collector_honors_max_pages_limit() -> None:
    requests: list[object] = []

    def fake_opener(request: object, timeout: int = 15) -> FakeResponse:
        requests.append(request)
        return FakeResponse({"items": [{"repository": {"full_name": "acme/repo"}, "path": "x", "html_url": "u", "text_matches": []}]})

    collector = CollectorClient(opener=fake_opener, per_page=1, max_pages=2)
    collector.collect("github", "acme password")

    assert len(requests) == 2
