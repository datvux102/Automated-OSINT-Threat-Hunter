from __future__ import annotations

import json
import mimetypes
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from cybersentinel.config import Settings
from cybersentinel.dev_server import (
    build_system_status,
    handle_collect_request,
    parse_json_body_bytes,
)
from cybersentinel.lambda_handler import handler


def project_root() -> Path:
    explicit_root = os.getenv("CYBERSENTINEL_PROJECT_ROOT", "").strip()
    candidates: list[Path] = []
    if explicit_root:
        candidates.append(Path(explicit_root))
    candidates.extend([Path.cwd(), Path(__file__).resolve().parents[2]])

    for candidate in candidates:
        resolved = candidate.resolve()
        if (resolved / "frontend").exists() and (resolved / "prompts").exists():
            return resolved

    return Path.cwd().resolve()


def frontend_dist_dir() -> Path:
    return project_root() / "frontend" / "dist"


def health_payload() -> dict[str, str | bool]:
    return {"ok": True, "message": "Backend connected"}


def resolve_static_asset(request_path: str, dist_dir: Path | None = None) -> Path:
    dist_dir = (dist_dir or frontend_dist_dir()).resolve()
    path = unquote(urlparse(request_path).path)

    if path in {"", "/"}:
        return dist_dir / "index.html"

    candidate = (dist_dir / path.lstrip("/")).resolve()
    try:
        candidate.relative_to(dist_dir)
    except ValueError:
        return dist_dir / "index.html"

    if candidate.is_file():
        return candidate

    return dist_dir / "index.html"


def handle_api_get(path: str, settings: Settings | None = None) -> tuple[HTTPStatus, dict] | None:
    if path == "/api/health":
        return HTTPStatus.OK, health_payload()

    if path == "/api/system-status":
        return HTTPStatus.OK, build_system_status(settings or Settings.from_env())

    return None


def handle_api_post(
    path: str,
    payload: dict,
    settings: Settings | None = None,
) -> tuple[HTTPStatus, dict] | None:
    if path == "/api/analyze":
        return HTTPStatus.OK, handler(payload)

    if path == "/api/collect":
        return handle_collect_request(payload, settings=settings)

    return None


class CyberSentinelWebRequestHandler(BaseHTTPRequestHandler):
    server_version = "CyberSentinelWebServer/0.1"

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(HTTPStatus.NO_CONTENT)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        api_response = handle_api_get(self.path)
        if api_response is not None:
            status, payload = api_response
            self._send_json(status, payload)
            return

        if self.path.startswith("/api/"):
            self._send_json(HTTPStatus.NOT_FOUND, {"ok": False, "error": "Route not found."})
            return

        self._serve_static_asset()

    def do_POST(self) -> None:  # noqa: N802
        if not self.path.startswith("/api/"):
            self._send_json(HTTPStatus.NOT_FOUND, {"ok": False, "error": "Route not found."})
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._send_json(
                HTTPStatus.BAD_REQUEST,
                {"ok": False, "error": "Invalid Content-Length header."},
            )
            return

        payload, error = parse_json_body_bytes(
            self.rfile.read(content_length) if content_length else b"{}"
        )
        if error is not None:
            self._send_json(HTTPStatus.BAD_REQUEST, {"ok": False, "error": error})
            return

        api_response = handle_api_post(self.path, payload)
        if api_response is None:
            self._send_json(HTTPStatus.NOT_FOUND, {"ok": False, "error": "Route not found."})
            return

        status, response_payload = api_response
        self._send_json(status, response_payload)

    def log_message(self, format: str, *args: object) -> None:
        return

    def _serve_static_asset(self) -> None:
        asset_path = resolve_static_asset(self.path)
        if not asset_path.exists() or not asset_path.is_file():
            self._send_json(
                HTTPStatus.SERVICE_UNAVAILABLE,
                {
                    "ok": False,
                    "error": "Frontend assets not found. Build frontend before starting web_server.",
                },
            )
            return

        data = asset_path.read_bytes()
        content_type, _ = mimetypes.guess_type(str(asset_path))
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type or "application/octet-stream")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_cors_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _send_json(self, status: HTTPStatus, payload: dict) -> None:
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self._send_cors_headers()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def run(host: str = "0.0.0.0", port: int | None = None) -> None:
    selected_port = port if port is not None else int(os.getenv("PORT", "10000"))
    server = ThreadingHTTPServer((host, selected_port), CyberSentinelWebRequestHandler)
    print(f"CyberSentinel web server listening on http://{host}:{selected_port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    run()
