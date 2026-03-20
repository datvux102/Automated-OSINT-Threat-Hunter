from __future__ import annotations

import base64
import json
import logging
from typing import Any

from cybersentinel.config import Settings
from cybersentinel.models import ThreatInput
from cybersentinel.pipeline import should_alert
from cybersentinel.analyzer import ThreatAnalyzer
from cybersentinel.notifier import AlertNotifier


logger = logging.getLogger("cybersentinel.lambda")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
logger.setLevel(logging.INFO)
logger.propagate = False


def _log(event_type: str, **fields: Any) -> None:
    logger.info(json.dumps({"event_type": event_type, **fields}, sort_keys=True))


def _default_verdict() -> dict[str, str | bool]:
    return {
        "is_threat": False,
        "threat_type": "Invalid_Request",
        "severity": "LOW",
        "summary": "Request could not be processed.",
    }


def _normalize_str(value: Any, default: str = "") -> str:
    if value is None:
        return default
    if isinstance(value, str):
        return value
    return str(value)


def _parse_event_payload(event: dict) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    # Returns (payload, error) where payload is a dict or None.
    if not isinstance(event, dict):
        return None, {"code": "invalid_event", "message": "Event must be an object."}

    if "body" not in event:
        return event, None

    body = event.get("body")
    if isinstance(body, dict):
        return body, None

    if not isinstance(body, str):
        return None, {"code": "invalid_body", "message": "API Gateway body must be a string or object."}

    raw_body = body
    if event.get("isBase64Encoded") is True:
        try:
            raw_body = base64.b64decode(body).decode("utf-8")
        except Exception:
            return None, {"code": "invalid_body", "message": "Base64 body could not be decoded."}

    try:
        return json.loads(raw_body), None
    except json.JSONDecodeError:
        return None, {"code": "invalid_json", "message": "API Gateway body is not valid JSON."}


def _parse_threat_input(payload: dict[str, Any]) -> ThreatInput:
    return ThreatInput(
        source=_normalize_str(payload.get("source", "unknown"), default="unknown").strip().lower()
        or "unknown",
        query=_normalize_str(payload.get("query", ""), default="").strip(),
        raw_text=_normalize_str(payload.get("raw_text", ""), default=""),
    )


def handler(event: dict, context: object | None = None) -> dict:
    settings = Settings.from_env()
    payload, parse_error = _parse_event_payload(event)

    if parse_error is not None or payload is None:
        _log("request_rejected", error=parse_error)
        response_body = {
            "ok": False,
            "input": {"source": "unknown", "query": ""},
            "verdict": _default_verdict(),
            "alerts_sent": [],
            "error": parse_error,
        }
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(response_body),
        }

    threat_input = _parse_threat_input(payload)
    _log(
        "request_received",
        source=threat_input.source,
        query=threat_input.query,
        raw_text_len=len(threat_input.raw_text),
        api_gateway="body" in event,
    )

    analyzer = ThreatAnalyzer(
        system_prompt_path=settings.system_prompt_path,
        bedrock_model_id=settings.bedrock_model_id,
        aws_region=settings.aws_region,
    )
    notifier = AlertNotifier(
        sns_topic_arn=settings.sns_topic_arn,
        aws_region=settings.aws_region,
    )

    verdict = analyzer.analyze(threat_input)

    alerts_sent: list[dict[str, str]] = []
    notifier_error: dict[str, str] | None = None
    if verdict.is_threat and (verdict.severity == "CRITICAL" or should_alert(verdict.severity, settings.alert_threshold)):
        try:
            notifier.notify(threat_input, verdict)
            alerts_sent = [alert.to_dict() for alert in notifier.sent_alerts]
        except Exception as exc:
            notifier_error = {"code": "notifier_failed", "message": str(exc)}
            _log("notifier_failed", error=notifier_error)

    response_body = {
        "ok": True,
        "input": {"source": threat_input.source, "query": threat_input.query},
        "verdict": verdict.to_dict(),
        "alerts_sent": alerts_sent,
        "error": notifier_error,
    }
    _log(
        "request_completed",
        source=threat_input.source,
        query=threat_input.query,
        is_threat=verdict.is_threat,
        severity=verdict.severity,
        alerts_sent=len(alerts_sent),
    )

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(response_body),
    }
