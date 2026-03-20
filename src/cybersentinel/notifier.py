from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any

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
    """Optional SNS-backed notifier with local alert recording."""

    def __init__(
        self,
        sns_topic_arn: str = "",
        aws_region: str = "us-east-1",
        sns_client: Any | None = None,
    ) -> None:
        self.sent_alerts: list[NotificationRecord] = []
        self.sns_topic_arn = sns_topic_arn
        self.aws_region = aws_region
        self._sns_client = sns_client

    def notify(self, threat_input: ThreatInput, verdict: ThreatVerdict) -> None:
        record = NotificationRecord(
            source=threat_input.source,
            query=threat_input.query,
            severity=verdict.severity,
            threat_type=verdict.threat_type,
            summary=verdict.summary,
        )
        self.sent_alerts.append(record)
        self._publish_to_sns(record)

    def _publish_to_sns(self, record: NotificationRecord) -> None:
        if not self.sns_topic_arn:
            return

        client = self._get_sns_client()
        if client is None:
            return

        try:
            client.publish(
                TopicArn=self.sns_topic_arn,
                Subject=f"CyberSentinel {record.severity} alert",
                Message=json.dumps(record.to_dict()),
            )
        except Exception:
            return

    def _get_sns_client(self) -> Any | None:
        if self._sns_client is not None:
            return self._sns_client

        try:
            import boto3
        except ImportError:
            return None

        self._sns_client = boto3.client("sns", region_name=self.aws_region)
        return self._sns_client
