from __future__ import annotations

from dataclasses import asdict, dataclass

from cybersentinel.models import ThreatInput, ThreatVerdict


@dataclass(slots=True)
class NotificationRecord:
    source: str
    query: str
    severity: str
    threat_type: str
    summary: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


class AlertNotifier:
    """Notification boundary for future SNS integration."""

    def __init__(self) -> None:
        self.sent_alerts: list[NotificationRecord] = []

    def notify(self, threat_input: ThreatInput, verdict: ThreatVerdict) -> None:
        self.sent_alerts.append(
            NotificationRecord(
                source=threat_input.source,
                query=threat_input.query,
                severity=verdict.severity,
                threat_type=verdict.threat_type,
                summary=verdict.summary,
            )
        )

