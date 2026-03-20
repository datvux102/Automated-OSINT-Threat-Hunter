import json
from pathlib import Path

from cybersentinel.analyzer import ThreatAnalyzer
from cybersentinel.models import ThreatInput


def test_benign_sample_input() -> None:
    verdict = ThreatAnalyzer().analyze(
        ThreatInput(source="pastebin", query="acme password", raw_text="example api_key=dummy-value")
    )
    assert verdict.is_threat is False
    assert verdict.threat_type == "Benign_Example"


def test_critical_sample_input() -> None:
    verdict = ThreatAnalyzer().analyze(
        ThreatInput(source="github", query="acme leak", raw_text="BEGIN RSA PRIVATE KEY")
    )
    assert verdict.is_threat is True
    assert verdict.severity == "CRITICAL"


class FakeBedrockBody:
    def __init__(self, text: str) -> None:
        self.text = text

    def read(self) -> bytes:
        return self.text.encode("utf-8")


class FakeBedrockValidClient:
    def invoke_model(self, **_: object) -> dict[str, FakeBedrockBody]:
        return {
            "body": FakeBedrockBody(
                json.dumps(
                    {
                        "content": [
                            {
                                "type": "text",
                                "text": (
                                    "Result:\n"
                                    + json.dumps(
                                        {
                                            "is_threat": True,
                                            "threat_type": "API_Key_Leak",
                                            "severity": "critical",
                                            "summary": "Model detected a likely key exposure.",
                                        }
                                    )
                                    + "\nThanks."
                                ),
                            }
                        ]
                    }
                )
            )
        }


def test_valid_bedrock_json() -> None:
    analyzer = ThreatAnalyzer(
        Path("prompts/system_prompt.txt"),
        bedrock_model_id="anthropic.test",
        bedrock_client=FakeBedrockValidClient(),
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
    assert verdict.severity == "CRITICAL"


class FakeBedrockInvalidJsonClient:
    def invoke_model(self, **_: object) -> dict[str, FakeBedrockBody]:
        return {
            "body": FakeBedrockBody(
                json.dumps(
                    {
                        "content": [
                            {
                                "type": "text",
                                "text": "not-json: {this is broken",
                            }
                        ]
                    }
                )
            )
        }


def test_invalid_bedrock_json_falls_back_to_heuristic() -> None:
    analyzer = ThreatAnalyzer(
        Path("prompts/system_prompt.txt"),
        bedrock_model_id="anthropic.test",
        bedrock_client=FakeBedrockInvalidJsonClient(),
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

class FakeBedrockMissingKeysClient:
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
                                        "summary": "Missing threat_type key.",
                                    }
                                ),
                            }
                        ]
                    }
                )
            )
        }


def test_missing_keys_in_bedrock_output_falls_back_to_heuristic() -> None:
    analyzer = ThreatAnalyzer(
        Path("prompts/system_prompt.txt"),
        bedrock_model_id="anthropic.test",
        bedrock_client=FakeBedrockMissingKeysClient(),
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
