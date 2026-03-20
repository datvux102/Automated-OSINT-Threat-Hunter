from __future__ import annotations

import json

from cybersentinel.config import Settings
from cybersentinel.logging_utils import log_event
from cybersentinel.models import ThreatInput
from cybersentinel.pipeline import process_threat_input


def _parse_event(event: dict) -> ThreatInput:
    payload = event
    if "body" in event:
        body = event["body"]
        payload = json.loads(body) if isinstance(body, str) else body

    return ThreatInput(
        source=payload.get("source", "unknown"),
        query=payload.get("query", ""),
        raw_text=payload.get("raw_text", ""),
    )

def handler(event: dict, context: object | None = None) -> dict:
    settings = Settings.from_env()
    threat_input = _parse_event(event)
    log_event(
        "lambda_invocation",
        handler="threat_analysis",
        source=threat_input.source,
        query=threat_input.query,
    )
    result = process_threat_input(threat_input=threat_input, settings=settings)

    return {
        "statusCode": 200,
        "body": json.dumps(result),
    }
