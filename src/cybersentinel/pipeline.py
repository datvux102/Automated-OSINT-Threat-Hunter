from __future__ import annotations

from cybersentinel.analyzer import ThreatAnalyzer
from cybersentinel.collector import CollectorClient
from cybersentinel.config import Settings
from cybersentinel.models import ThreatInput, ThreatVerdict
from cybersentinel.notifier import AlertNotifier


SEVERITY_ORDER = {
    "LOW": 1,
    "MEDIUM": 2,
    "HIGH": 3,
    "CRITICAL": 4,
}

VALID_SEVERITIES = set(SEVERITY_ORDER)


def _normalize_severity(value: object) -> str:
    normalized = str(value).strip().upper()
    if normalized in VALID_SEVERITIES:
        return normalized
    if "CRIT" in normalized:
        return "CRITICAL"
    if "HIGH" in normalized:
        return "HIGH"
    if "MED" in normalized:
        return "MEDIUM"
    if "LOW" in normalized:
        return "LOW"
    return "LOW"


def _verdict_schema(verdict: ThreatVerdict) -> dict[str, str | bool]:
    data = verdict.to_dict()
    return {
        "is_threat": bool(data.get("is_threat", False)),
        "threat_type": str(data.get("threat_type", "Unknown")),
        "severity": _normalize_severity(data.get("severity", "LOW")),
        "summary": str(data.get("summary", "")),
    }


def should_alert(severity: str, threshold: str) -> bool:
    return SEVERITY_ORDER.get(severity, 0) >= SEVERITY_ORDER.get(threshold, 99)


def build_analyzer(settings: Settings) -> ThreatAnalyzer:
    return ThreatAnalyzer(
        system_prompt_path=settings.system_prompt_path,
        bedrock_model_id=settings.bedrock_model_id,
        aws_region=settings.aws_region,
    )


def build_notifier(settings: Settings) -> AlertNotifier:
    return AlertNotifier(
        sns_topic_arn=settings.sns_topic_arn,
        aws_region=settings.aws_region,
    )


def build_collector(settings: Settings) -> CollectorClient:
    return CollectorClient(
        github_token=settings.github_token,
        github_api_url=settings.github_api_url,
        github_api_version=settings.github_api_version,
    )


def process_threat_input(
    threat_input: ThreatInput,
    settings: Settings,
    analyzer: ThreatAnalyzer | None = None,
    notifier: AlertNotifier | None = None,
) -> dict:
    analyzer = analyzer or build_analyzer(settings)
    notifier = notifier or build_notifier(settings)

    try:
        verdict = analyzer.analyze(threat_input)
    except Exception:
        verdict = ThreatVerdict(
            is_threat=False,
            threat_type="Analysis_Error",
            severity="LOW",
            summary="Analyzer failed; returned safe fallback verdict.",
        )

    if verdict.is_threat and should_alert(_normalize_severity(verdict.severity), settings.alert_threshold):
        try:
            notifier.notify(threat_input, verdict)
        except Exception:
            # Demo hardening: never break the response if the notifier fails.
            pass

    result = {
        "input": {
            "source": threat_input.source,
            "query": threat_input.query,
        },
        "verdict": _verdict_schema(verdict),
        "alerts_sent": [alert.to_dict() for alert in notifier.sent_alerts],
    }
    return result


def collect_and_process(
    source: str,
    query: str,
    settings: Settings,
    collector: CollectorClient | None = None,
    analyzer: ThreatAnalyzer | None = None,
    notifier: AlertNotifier | None = None,
) -> dict:
    collector = collector or build_collector(settings)
    record = collector.collect(source, query)
    threat_input = ThreatInput(
        source=record.source,
        query=record.query,
        raw_text=record.raw_text,
    )
    result = process_threat_input(
        threat_input=threat_input,
        settings=settings,
        analyzer=analyzer,
        notifier=notifier,
    )
    result["collected"] = record.to_dict()
    return result
