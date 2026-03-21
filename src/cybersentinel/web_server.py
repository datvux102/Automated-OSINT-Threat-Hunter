from __future__ import annotations

import json
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from cybersentinel.lambda_handler import handler


class CyberSentinelWebHandler(BaseHTTPRequestHandler):
    server_version = "CyberSentinelWebServer/0.1"

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(HTTPStatus.NO_CONTENT)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        if self.path.startswith("/api/"):
            if self.path != "/api/health":
                self._send_json(
                    HTTPStatus.NOT_FOUND,
                    {"ok": False, "error": "Route not found."},
                )
                return

            self._send_json(
                HTTPStatus.OK,
                {"ok": True, "message": "Backend connected"},
            )
            return

        static_dir = _static_dir()
        if not static_dir:
            self._send_json(
                HTTPStatus.NOT_FOUND,
                {"ok": False, "error": "Static frontend is not configured."},
            )
            return

        self._serve_static(static_dir)

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/api/analyze":
            self._send_json(
                HTTPStatus.NOT_FOUND,
                {"ok": False, "error": "Route not found."},
            )
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._send_json(
                HTTPStatus.BAD_REQUEST,
                {"ok": False, "error": "Invalid Content-Length header."},
            )
            return

        body = self.rfile.read(content_length).decode("utf-8") if content_length else "{}"
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            self._send_json(
                HTTPStatus.BAD_REQUEST,
                {"ok": False, "error": "Request body must be valid JSON."},
            )
            return

        if not isinstance(payload, dict):
            self._send_json(
                HTTPStatus.BAD_REQUEST,
                {"ok": False, "error": "Request body must be a JSON object."},
            )
            return

        response = handler(payload)
        self._send_json(HTTPStatus.OK, response)

    def log_message(self, format: str, *args: object) -> None:
        return

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

    def _serve_static(self, static_dir: Path) -> None:
        parsed = urlparse(self.path)
        path = unquote(parsed.path)
        if path == "/":
            path = "/index.html"

        candidate = _safe_join(static_dir, path.lstrip("/"))
        if candidate and candidate.is_file():
            self._send_file(candidate)
            return

        index = static_dir / "index.html"
        if index.is_file():
            self._send_file(index)
            return

        self._send_json(
            HTTPStatus.NOT_FOUND,
            {"ok": False, "error": "Frontend assets not found."},
        )

    def _send_file(self, path: Path) -> None:
        content_type = _content_type(path.suffix.lower())
        data = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def _static_dir() -> Path | None:
    raw = os.environ.get("CYBERSENTINEL_STATIC_DIR", "")
    if not raw:
        default = Path(__file__).resolve().parents[2] / "frontend" / "dist"
        return default if default.exists() else None

    path = Path(raw).expanduser().resolve()
    return path if path.exists() else None


def _safe_join(root: Path, rel: str) -> Path | None:
    try:
        candidate = (root / rel).resolve()
    except (OSError, RuntimeError):
        return None

    try:
        candidate.relative_to(root.resolve())
    except ValueError:
        return None

    return candidate


def _content_type(suffix: str) -> str:
    return {
        ".html": "text/html; charset=utf-8",
        ".css": "text/css; charset=utf-8",
        ".js": "text/javascript; charset=utf-8",
        ".mjs": "text/javascript; charset=utf-8",
        ".json": "application/json; charset=utf-8",
        ".svg": "image/svg+xml",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".ico": "image/x-icon",
        ".txt": "text/plain; charset=utf-8",
        ".map": "application/json; charset=utf-8",
    }.get(suffix, "application/octet-stream")


def run() -> None:
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8000"))
    server = ThreadingHTTPServer((host, port), CyberSentinelWebHandler)
    print(f"CyberSentinel web server listening on http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    run()
