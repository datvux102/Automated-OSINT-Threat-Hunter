import json

import cybersentinel.lambda_handler as lambda_handler


def _body(response: dict) -> dict:
    return json.loads(response["body"])


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
    assert body["alerts_sent"] == []
    assert body["error"]["code"] == "notifier_failed"
