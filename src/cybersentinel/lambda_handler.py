from __future__ import annotations

import json

from cybersentinel.analyzer import ThreatAnalyzer
from cybersentinel.config import Settings
from cybersentinel.models import ThreatInput
from cybersentinel.notifier import AlertNotifier


SEVERITY_ORDER = {
    "LOW": 1,
    "MEDIUM": 2,
    "HIGH": 3,
    "CRITICAL": 4,
}


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


def _should_alert(severity: str, threshold: str) -> bool:
    return SEVERITY_ORDER.get(severity, 0) >= SEVERITY_ORDER.get(threshold, 99)


def handler(event: dict, context: object | None = None) -> dict:
    settings = Settings.from_env()
    threat_input = _parse_event(event)
    analyzer = ThreatAnalyzer(
        system_prompt_path=settings.system_prompt_path,
        bedrock_model_id=settings.bedrock_model_id,
        aws_region=settings.aws_region,
    )
    notifier = AlertNotifier()

    verdict = analyzer.analyze(threat_input)
    if verdict.is_threat and _should_alert(verdict.severity, settings.alert_threshold):
        notifier.notify(threat_input, verdict)

    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "input": {
                    "source": threat_input.source,
                    "query": threat_input.query,
                },
                "verdict": verdict.to_dict(),
                "alerts_sent": [alert.to_dict() for alert in notifier.sent_alerts],
            }
        ),
    }
