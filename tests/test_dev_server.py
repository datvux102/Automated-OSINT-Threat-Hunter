from http import HTTPStatus

import cybersentinel.dev_server as dev_server
from cybersentinel.config import Settings


def test_system_status_reflects_env_settings() -> None:
    payload = dev_server.build_system_status(
        Settings(
            github_token="token123",
            bedrock_model_id="anthropic.test",
            sns_topic_arn="arn:aws:sns:us-east-1:123456789012:test",
        )
    )

    assert payload == {
        "ok": True,
        "backend_ok": True,
        "collector_enabled": True,
        "github_token_configured": True,
        "bedrock_enabled": True,
        "sns_enabled": True,
    }


def test_collect_request_returns_record() -> None:
    original = dev_server.build_collector

    class FakeCollector:
        def collect(self, source: str, query: str) -> object:
            assert source == "github"
            assert query == "acme password"
            return type(
                "Record",
                (),
                {
                    "to_dict": lambda self: {
                        "source": "github",
                        "query": "acme password",
                        "raw_text": "repository: acme/public-repo",
                    }
                },
            )()

    try:
        dev_server.build_collector = lambda settings: FakeCollector()
        status, payload = dev_server.handle_collect_request(
            {"source": "github", "query": "acme password"}
        )
    finally:
        dev_server.build_collector = original

    assert status == HTTPStatus.OK
    assert payload["ok"] is True
    assert payload["record"]["query"] == "acme password"


def test_collect_request_rejects_missing_query() -> None:
    status, payload = dev_server.handle_collect_request({"source": "github", "query": ""})

    assert status == HTTPStatus.BAD_REQUEST
    assert payload == {
        "ok": False,
        "error": "Request body must include non-empty source and query.",
    }


def test_collect_request_returns_real_error_message() -> None:
    original = dev_server.build_collector

    class FailingCollector:
        def collect(self, source: str, query: str) -> object:
            raise ValueError("Unsupported source: pastebin")

    try:
        dev_server.build_collector = lambda settings: FailingCollector()
        status, payload = dev_server.handle_collect_request(
            {"source": "github", "query": "acme password"}
        )
    finally:
        dev_server.build_collector = original

    assert status == HTTPStatus.BAD_GATEWAY
    assert payload == {"ok": False, "error": "Unsupported source: pastebin"}
