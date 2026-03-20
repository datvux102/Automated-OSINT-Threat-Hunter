import json
from pathlib import Path

from cybersentinel.analyzer import ThreatAnalyzer
from cybersentinel.models import ThreatInput


def test_analyzer_flags_high_signal_secret() -> None:
    analyzer = ThreatAnalyzer(Path("prompts/system_prompt.txt"))
    verdict = analyzer.analyze(
        ThreatInput(
            source="github",
            query="acme secret",
            raw_text="const key = 'AWS_SECRET_ACCESS_KEY=abcd1234';",
        )
    )

    assert verdict.is_threat is True
    assert verdict.threat_type == "Cloud_Credential_Leak"
    assert verdict.severity == "CRITICAL"


def test_analyzer_rejects_dummy_data() -> None:
    analyzer = ThreatAnalyzer()
    verdict = analyzer.analyze(
        ThreatInput(
            source="pastebin",
            query="acme password",
            raw_text="example api_key=dummy-value",
        )
    )

    assert verdict.is_threat is False
    assert verdict.threat_type == "Benign_Example"


class FakeBedrockBody:
    def __init__(self, text: str) -> None:
        self.text = text

    def read(self) -> bytes:
        return self.text.encode("utf-8")


class FakeBedrockClient:
    def invoke_model(self, **_: object) -> dict[str, FakeBedrockBody]:
        return {
            "body": FakeBedrockBody(
                json.dumps(
                    {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(
                                    {
                                        "is_threat": True,
                                        "threat_type": "API_Key_Leak",
                                        "severity": "HIGH",
                                        "summary": "Model detected a likely key exposure.",
                                    }
                                ),
                            }
                        ]
                    }
                )
            )
        }


def test_analyzer_uses_bedrock_when_configured() -> None:
    analyzer = ThreatAnalyzer(
        Path("prompts/system_prompt.txt"),
        bedrock_model_id="anthropic.test",
        bedrock_client=FakeBedrockClient(),
    )
    verdict = analyzer.analyze(
        ThreatInput(
            source="github",
            query="acme key",
            raw_text="token candidate without heuristic marker",
        )
    )

    assert verdict.is_threat is True
    assert verdict.threat_type == "API_Key_Leak"
    assert verdict.severity == "HIGH"


class FakeBedrockFencedClient:
    def invoke_model(self, **_: object) -> dict[str, FakeBedrockBody]:
        return {
            "body": FakeBedrockBody(
                json.dumps(
                    {
                        "content": [
                            {
                                "type": "text",
                                "text": (
                                    "```json\n"
                                    "{\n"
                                    '  "is_threat": "true",\n'
                                    '  "threat_type": "Credential_Leak",\n'
                                    '  "severity": "high",\n'
                                    '  "summary": "Model found a likely leaked password."\n'
                                    "}\n"
                                    "```"
                                ),
                            }
                        ]
                    }
                )
            )
        }


def test_analyzer_handles_fenced_bedrock_json() -> None:
    analyzer = ThreatAnalyzer(
        Path("prompts/system_prompt.txt"),
        bedrock_model_id="anthropic.test",
        bedrock_client=FakeBedrockFencedClient(),
    )
    verdict = analyzer.analyze(
        ThreatInput(
            source="github",
            query="acme leak",
            raw_text="suspicious content without heuristic marker",
        )
    )

    assert verdict.is_threat is True
    assert verdict.threat_type == "Credential_Leak"
    assert verdict.severity == "HIGH"


def test_analyzer_aggregates_multi_hit_bundle() -> None:
    analyzer = ThreatAnalyzer()
    verdict = analyzer.analyze(
        ThreatInput(
            source="github",
            query="acme leak",
            raw_text=(
                "repository: acme/example\nsnippet:\nexample api_key=dummy\n\n---\n\n"
                "repository: acme/prod\nsnippet:\nBEGIN RSA PRIVATE KEY"
            ),
        )
    )

    assert verdict.is_threat is True
    assert verdict.threat_type == "Private_Key_Leak"
    assert verdict.severity == "CRITICAL"
    assert "Analyzed 2 collected hits" in verdict.summary


class FakeBedrockInvalidSeverityClient:
    def invoke_model(self, **_: object) -> dict[str, FakeBedrockBody]:
        return {
            "body": FakeBedrockBody(
                json.dumps(
                    {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(
                                    {
                                        "is_threat": True,
                                        "threat_type": "API_Key_Leak",
                                        "severity": "SEVERE",
                                        "summary": "Invalid severity value.",
                                    }
                                ),
                            }
                        ]
                    }
                )
            )
        }


class FakeBedrockExtraTextClient:
    def invoke_model(self, **_: object) -> dict[str, FakeBedrockBody]:
        return {
            "body": FakeBedrockBody(
                json.dumps(
                    {
                        "content": [
                            {
                                "type": "text",
                                "text": (
                                    "Here is the result:\n"
                                    '{"is_threat": true, "threat_type": "API_Key_Leak", '
                                    '"severity": "HIGH", "summary": "Suspicious token."}'
                                ),
                            }
                        ]
                    }
                )
            )
        }


class FakeBedrockMissingKeyClient:
    def invoke_model(self, **_: object) -> dict[str, FakeBedrockBody]:
        return {
            "body": FakeBedrockBody(
                json.dumps(
                    {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(
                                    {
                                        "is_threat": True,
                                        "severity": "HIGH",
                                        "summary": "Missing threat type.",
                                    }
                                ),
                            }
                        ]
                    }
                )
            )
        }


def test_analyzer_rejects_invalid_bedrock_severity_and_falls_back() -> None:
    analyzer = ThreatAnalyzer(
        Path("prompts/system_prompt.txt"),
        bedrock_model_id="anthropic.test",
        bedrock_client=FakeBedrockInvalidSeverityClient(),
    )
    verdict = analyzer.analyze(
        ThreatInput(
            source="github",
            query="acme key",
            raw_text="password=supersecret",
        )
    )

    assert verdict.is_threat is True
    assert verdict.threat_type == "Credential_Leak"
    assert verdict.severity == "HIGH"


def test_analyzer_rejects_bedrock_json_with_prefix_text() -> None:
    analyzer = ThreatAnalyzer(
        Path("prompts/system_prompt.txt"),
        bedrock_model_id="anthropic.test",
        bedrock_client=FakeBedrockExtraTextClient(),
    )
    verdict = analyzer.analyze(
        ThreatInput(
            source="github",
            query="acme key",
            raw_text="password=supersecret",
        )
    )

    assert verdict.is_threat is True
    assert verdict.threat_type == "Credential_Leak"
    assert verdict.severity == "HIGH"


def test_analyzer_rejects_bedrock_json_missing_required_key() -> None:
    analyzer = ThreatAnalyzer(
        Path("prompts/system_prompt.txt"),
        bedrock_model_id="anthropic.test",
        bedrock_client=FakeBedrockMissingKeyClient(),
    )
    verdict = analyzer.analyze(
        ThreatInput(
            source="github",
            query="acme key",
            raw_text="password=supersecret",
        )
    )

    assert verdict.is_threat is True
    assert verdict.threat_type == "Credential_Leak"
    assert verdict.severity == "HIGH"
