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
                """
                {
                  "content": [
                    {
                      "type": "text",
                      "text": "{\\"is_threat\\": true, \\"threat_type\\": \\"API_Key_Leak\\", \\"severity\\": \\"HIGH\\", \\"summary\\": \\"Model detected a likely key exposure.\\"}"
                    }
                  ]
                }
                """
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
