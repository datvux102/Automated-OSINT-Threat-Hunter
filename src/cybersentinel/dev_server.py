from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from cybersentinel.config import Settings
from cybersentinel.pipeline import build_collector
from cybersentinel.lambda_handler import handler


class CyberSentinelRequestHandler(BaseHTTPRequestHandler):
    server_version = "CyberSentinelDevServer/0.1"

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(HTTPStatus.NO_CONTENT)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/api/health":
            self._send_json(
                HTTPStatus.OK,
                {"ok": True, "message": "Backend connected"},
            )
            return

        if self.path == "/api/system-status":
            settings = Settings.from_env()
            self._send_json(HTTPStatus.OK, build_system_status(settings))
            return

        self._send_json(
            HTTPStatus.NOT_FOUND,
            {"ok": False, "error": "Route not found."},
        )

    def do_POST(self) -> None:  # noqa: N802
        if self.path not in {"/api/analyze", "/api/collect"}:
            self._send_json(
                HTTPStatus.NOT_FOUND,
                {"ok": False, "error": "Route not found."},
            )
            return

        payload, error = self._parse_json_body()
        if error is not None:
            self._send_json(HTTPStatus.BAD_REQUEST, {"ok": False, "error": error})
            return

        if self.path == "/api/analyze":
            response = handler(payload)
            self._send_json(HTTPStatus.OK, response)
            return

        self._handle_collect(payload)

    def log_message(self, format: str, *args: object) -> None:
        return

    def _handle_collect(self, payload: dict) -> None:
        status, response = handle_collect_request(payload)
        self._send_json(status, response)

    def _parse_json_body(self) -> tuple[dict | None, str | None]:
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            return None, "Invalid Content-Length header."

        body = self.rfile.read(content_length).decode("utf-8") if content_length else "{}"
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            return None, "Request body must be valid JSON."

        if not isinstance(payload, dict):
            return None, "Request body must be a JSON object."

        return payload, None

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


def handle_collect_request(
    payload: dict,
    settings: Settings | None = None,
) -> tuple[HTTPStatus, dict]:
    source = str(payload.get("source", "")).strip().lower()
    query = str(payload.get("query", "")).strip()
    if not source or not query:
        return (
            HTTPStatus.BAD_REQUEST,
            {"ok": False, "error": "Request body must include non-empty source and query."},
        )

    settings = settings or Settings.from_env()
    collector = build_collector(settings)
    try:
        record = collector.collect(source=source, query=query)
    except Exception as exc:
        return HTTPStatus.BAD_GATEWAY, {"ok": False, "error": str(exc)}

    return HTTPStatus.OK, {"ok": True, "record": record.to_dict()}


def build_system_status(settings: Settings) -> dict[str, bool]:
    return {
        "ok": True,
        "backend_ok": True,
        "collector_enabled": True,
        "github_token_configured": bool(settings.github_token.strip()),
        "bedrock_enabled": bool(settings.bedrock_model_id.strip()),
        "sns_enabled": bool(settings.sns_topic_arn.strip()),
    }


def run(host: str = "127.0.0.1", port: int = 8000) -> None:
    server = ThreadingHTTPServer((host, port), CyberSentinelRequestHandler)
    print(f"CyberSentinel dev server listening on http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    run()
