from __future__ import annotations

from cybersentinel.analyzer import ThreatAnalyzer
from cybersentinel.collector import CollectorClient
from cybersentinel.config import Settings
from cybersentinel.logging_utils import log_event
from cybersentinel.models import ThreatInput, ThreatVerdict
from cybersentinel.notifier import AlertNotifier


SEVERITY_ORDER = {
    "LOW": 1,
    "MEDIUM": 2,
    "HIGH": 3,
    "CRITICAL": 4,
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
        github_token_secret_arn=settings.github_token_secret_arn,
        github_api_url=settings.github_api_url,
        github_api_version=settings.github_api_version,
        aws_region=settings.aws_region,
        max_attempts=settings.github_max_attempts,
        backoff_seconds=settings.github_backoff_seconds,
    )


def process_threat_input(
    threat_input: ThreatInput,
    settings: Settings,
    analyzer: ThreatAnalyzer | None = None,
    notifier: AlertNotifier | None = None,
) -> dict:
    analyzer = analyzer or build_analyzer(settings)
    notifier = notifier or build_notifier(settings)

    log_event(
        "analysis_started",
        source=threat_input.source,
        query=threat_input.query,
        alert_threshold=settings.alert_threshold,
    )
    verdict = analyzer.analyze(threat_input)
    if verdict.is_threat and should_alert(verdict.severity, settings.alert_threshold):
        notifier.notify(threat_input, verdict)

    result = {
        "input": {
            "source": threat_input.source,
            "query": threat_input.query,
        },
        "verdict": verdict.to_dict(),
        "alerts_sent": [alert.to_dict() for alert in notifier.sent_alerts],
    }
    log_event(
        "analysis_completed",
        source=threat_input.source,
        query=threat_input.query,
        is_threat=verdict.is_threat,
        severity=verdict.severity,
        alerts_sent=len(result["alerts_sent"]),
    )
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
    log_event(
        "collection_started",
        source=source,
        query=query,
    )
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
    log_event(
        "collection_completed",
        source=record.source,
        query=record.query,
        collected_chars=len(record.raw_text),
    )
    return result
