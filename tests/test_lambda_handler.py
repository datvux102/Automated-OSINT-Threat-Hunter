import json

import cybersentinel.lambda_handler as lambda_handler


def _body(response: dict) -> dict:
    return json.loads(response["body"])

VALID_SEVERITIES = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}


def test_direct_event_input() -> None:
    response = lambda_handler.handler(
        {
            "source": "github",
            "query": "acme password",
            "raw_text": "password=supersecret",
        }
    )

    body = _body(response)
    assert response["statusCode"] == 200
    assert body["ok"] is True
    assert body["input"]["source"] == "github"
    assert set(body["verdict"].keys()) == {"is_threat", "threat_type", "severity", "summary"}
    assert body["verdict"]["severity"] in VALID_SEVERITIES


def test_api_gateway_body_input() -> None:
    response = lambda_handler.handler(
        {
            "body": json.dumps(
                {
                    "source": "github",
                    "query": "acme leak",
                    "raw_text": "BEGIN RSA PRIVATE KEY",
                }
            )
        }
    )

    body = _body(response)
    assert body["ok"] is True
    assert body["verdict"]["severity"] == "CRITICAL"
    assert body["verdict"]["severity"] in VALID_SEVERITIES


def test_benign_input_returns_no_alert() -> None:
    response = lambda_handler.handler(
        {
            "source": "github",
            "query": "acme example",
            "raw_text": "example api_key=dummy-value",
        }
    )

    body = _body(response)
    assert body["verdict"]["is_threat"] is False
    assert body["verdict"]["severity"] in VALID_SEVERITIES
    assert body["alerts_sent"] == []


def test_critical_input_triggers_alert_path() -> None:
    response = lambda_handler.handler(
        {
            "source": "github",
            "query": "acme leak",
            "raw_text": "BEGIN RSA PRIVATE KEY",
        }
    )

    body = _body(response)
    assert body["verdict"]["severity"] == "CRITICAL"
    assert body["verdict"]["severity"] in VALID_SEVERITIES
    assert len(body["alerts_sent"]) == 1


def test_notifier_failure_does_not_break_response() -> None:
    original = lambda_handler.AlertNotifier

    class FailingNotifier:
        def __init__(self, *args, **kwargs) -> None:
            self.sent_alerts = []

        def notify(self, threat_input, verdict) -> None:
            raise RuntimeError("SNS unavailable")

    try:
        lambda_handler.AlertNotifier = FailingNotifier
        response = lambda_handler.handler(
            {
                "source": "github",
                "query": "acme leak",
                "raw_text": "BEGIN RSA PRIVATE KEY",
            }
        )
    finally:
        lambda_handler.AlertNotifier = original

    body = _body(response)
    assert body["ok"] is True
    assert body["verdict"]["severity"] == "CRITICAL"
    assert body["verdict"]["severity"] in VALID_SEVERITIES
    assert body["alerts_sent"] == []
    assert body["error"]["code"] == "notifier_failed"


def test_invalid_bedrock_output_falls_back_to_heuristic() -> None:
    from pathlib import Path

    from cybersentinel.analyzer import ThreatAnalyzer as RealAnalyzer

    original = lambda_handler.ThreatAnalyzer

    class FakeBedrockBody:
        def read(self) -> bytes:
            return json.dumps({"content": [{"type": "text", "text": "not-json {broken"}]}).encode(
                "utf-8"
            )

    class FakeBedrockClient:
        def invoke_model(self, **_: object) -> dict[str, FakeBedrockBody]:
            return {"body": FakeBedrockBody()}

    def fake_analyzer_ctor(*, system_prompt_path, bedrock_model_id, aws_region):
        return RealAnalyzer(
            system_prompt_path=Path(system_prompt_path) if isinstance(system_prompt_path, str) else system_prompt_path,
            bedrock_model_id="anthropic.test",
            bedrock_client=FakeBedrockClient(),
        )

    try:
        lambda_handler.ThreatAnalyzer = fake_analyzer_ctor
        response = lambda_handler.handler(
            {
                "source": "github",
                "query": "acme key",
                "raw_text": "password=supersecret",
            }
        )
    finally:
        lambda_handler.ThreatAnalyzer = original

    body = _body(response)
    assert body["ok"] is True
    assert body["verdict"]["is_threat"] is True
    assert body["verdict"]["threat_type"] == "Credential_Leak"
    assert body["verdict"]["severity"] == "HIGH"
    assert body["verdict"]["severity"] in VALID_SEVERITIES


def test_invalid_api_gateway_body_returns_stable_schema() -> None:
    response = lambda_handler.handler({"body": "not-json"})
    body = _body(response)
    assert body["ok"] is False
    assert set(body["verdict"].keys()) == {"is_threat", "threat_type", "severity", "summary"}
    assert body["verdict"]["severity"] in VALID_SEVERITIES
