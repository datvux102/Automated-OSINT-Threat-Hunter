from http import HTTPStatus
from pathlib import Path

import cybersentinel.dev_server as dev_server
from cybersentinel.config import Settings
from cybersentinel.web_server import (
    handle_api_get,
    handle_api_post,
    health_payload,
    resolve_static_asset,
)


def test_health_payload_stays_stable() -> None:
    assert health_payload() == {"ok": True, "message": "Backend connected"}


def test_handle_api_get_health() -> None:
    status, payload = handle_api_get("/api/health") or (None, None)
    assert status == HTTPStatus.OK
    assert payload == {"ok": True, "message": "Backend connected"}


def test_handle_api_get_system_status() -> None:
    status, payload = handle_api_get(
        "/api/system-status",
        settings=Settings(github_token="token123", bedrock_model_id="model", sns_topic_arn="arn"),
    ) or (None, None)
    assert status == HTTPStatus.OK
    assert payload["collector_enabled"] is True
    assert payload["github_token_configured"] is True
    assert payload["bedrock_enabled"] is True
    assert payload["sns_enabled"] is True


def test_handle_api_post_collect() -> None:
    original = dev_server.build_collector

    class FakeCollector:
        def collect(self, source: str, query: str) -> object:
            return type(
                "Record",
                (),
                {
                    "to_dict": lambda self: {
                        "source": source,
                        "query": query,
                        "raw_text": "repository: acme/public-repo",
                    }
                },
            )()

    try:
        dev_server.build_collector = lambda settings: FakeCollector()
        status, payload = handle_api_post(
            "/api/collect",
            {"source": "github", "query": "acme password"},
            settings=Settings(),
        ) or (None, None)
    finally:
        dev_server.build_collector = original

    assert status == HTTPStatus.OK
    assert payload["ok"] is True
    assert payload["record"]["source"] == "github"


def test_handle_api_post_analyze() -> None:
    status, payload = handle_api_post(
        "/api/analyze",
        {
            "source": "github",
            "query": "acme leak",
            "raw_text": "BEGIN RSA PRIVATE KEY",
        },
    ) or (None, None)
    assert status == HTTPStatus.OK
    assert "body" in payload


def test_resolve_static_asset_supports_spa_fallback(tmp_path: Path) -> None:
    dist_dir = tmp_path / "frontend" / "dist"
    assets_dir = dist_dir / "assets"
    assets_dir.mkdir(parents=True)
    index_path = dist_dir / "index.html"
    js_path = assets_dir / "app.js"
    index_path.write_text("<!doctype html><html></html>", encoding="utf-8")
    js_path.write_text("console.log('ok')", encoding="utf-8")

    assert resolve_static_asset("/", dist_dir=dist_dir) == index_path
    assert resolve_static_asset("/assets/app.js", dist_dir=dist_dir) == js_path
    assert resolve_static_asset("/collector", dist_dir=dist_dir) == index_path
