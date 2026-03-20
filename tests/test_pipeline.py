from cybersentinel.collector import CollectedRecord
from cybersentinel.config import Settings
from cybersentinel.models import ThreatInput
from cybersentinel.pipeline import collect_and_process, process_threat_input


class FakeCollector:
    def collect(self, source: str, query: str) -> CollectedRecord:
        return CollectedRecord(
            source=source,
            query=query,
            raw_text="BEGIN RSA PRIVATE KEY",
        )


def test_process_threat_input_returns_alert_for_critical() -> None:
    result = process_threat_input(
        threat_input=ThreatInput(
            source="github",
            query="acme leak",
            raw_text="BEGIN RSA PRIVATE KEY",
        ),
        settings=Settings(),
    )

    assert result["verdict"]["is_threat"] is True
    assert len(result["alerts_sent"]) == 1


def test_collect_and_process_includes_collected_payload() -> None:
    result = collect_and_process(
        source="github",
        query="acme leak",
        settings=Settings(),
        collector=FakeCollector(),
    )

    assert result["collected"]["source"] == "github"
    assert result["verdict"]["severity"] == "CRITICAL"
