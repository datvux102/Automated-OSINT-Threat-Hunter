from __future__ import annotations

import json
import sys
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def http_get_json(url: str) -> dict[str, Any]:
    try:
        with urlopen(url, timeout=10) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw)
    except (HTTPError, URLError, TimeoutError) as exc:
        raise RuntimeError(f"GET failed for {url}: {exc}") from exc


def http_post_json(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=15) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw)
    except (HTTPError, URLError, TimeoutError) as exc:
        raise RuntimeError(f"POST failed for {url}: {exc}") from exc


def unwrap_handler_shape(response: dict[str, Any]) -> dict[str, Any]:
    if "body" in response and isinstance(response["body"], str):
        return json.loads(response["body"])
    return response


def assert_health(base_url: str) -> None:
    payload = http_get_json(f"{base_url}/api/health")
    if not payload.get("ok"):
        raise AssertionError(f"Unexpected health payload: {payload}")


def assert_system_status(base_url: str) -> None:
    payload = http_get_json(f"{base_url}/api/system-status")
    expected_keys = {
        "ok",
        "backend_ok",
        "collector_enabled",
        "github_token_configured",
        "bedrock_enabled",
        "sns_enabled",
    }
    if set(payload.keys()) != expected_keys or payload.get("ok") is not True:
        raise AssertionError(f"Unexpected system-status payload: {payload}")


def assert_collect(base_url: str) -> None:
    payload = http_post_json(
        f"{base_url}/api/collect",
        {
            "source": "github",
            "query": "acme password",
        },
    )
    record = payload.get("record", {})
    if payload.get("ok") is not True or record.get("source") != "github":
        raise AssertionError(f"Collect assertion failed: {payload}")


def assert_analyze_benign(base_url: str) -> None:
    raw = http_post_json(
        f"{base_url}/api/analyze",
        {
            "source": "github",
            "query": "docs example",
            "raw_text": "Example only: api_key='your_api_key_here'",
        },
    )
    payload = unwrap_handler_shape(raw)
    verdict = payload.get("verdict", {})
    if verdict.get("is_threat") is not False or verdict.get("severity") != "LOW":
        raise AssertionError(f"Benign assertion failed: {payload}")


def assert_analyze_critical(base_url: str) -> None:
    raw = http_post_json(
        f"{base_url}/api/analyze",
        {
            "source": "github",
            "query": "acme leak",
            "raw_text": "BEGIN RSA PRIVATE KEY",
        },
    )
    payload = unwrap_handler_shape(raw)
    verdict = payload.get("verdict", {})
    if verdict.get("is_threat") is not True or verdict.get("severity") != "CRITICAL":
        raise AssertionError(f"Critical assertion failed: {payload}")


def assert_frontend_root(base_url: str) -> None:
    try:
        with urlopen(f"{base_url}/", timeout=10) as response:
            raw = response.read().decode("utf-8")
    except (HTTPError, URLError, TimeoutError) as exc:
        raise RuntimeError(f"GET failed for {base_url}/: {exc}") from exc

    if "<!doctype html>" not in raw.lower():
        raise AssertionError("Frontend root did not return HTML.")


def assert_spa_fallback(base_url: str) -> None:
    try:
        with urlopen(f"{base_url}/collector", timeout=10) as response:
            raw = response.read().decode("utf-8")
    except (HTTPError, URLError, TimeoutError) as exc:
        raise RuntimeError(f"GET failed for {base_url}/collector: {exc}") from exc

    if "<!doctype html>" not in raw.lower():
        raise AssertionError("SPA fallback did not return index.html.")


def main() -> int:
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
    assert_health(base_url)
    assert_system_status(base_url)
    assert_collect(base_url)
    assert_analyze_benign(base_url)
    assert_analyze_critical(base_url)
    assert_frontend_root(base_url)
    assert_spa_fallback(base_url)
    print(f"Smoke E2E passed for {base_url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
