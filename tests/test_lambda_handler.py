import json

from cybersentinel.lambda_handler import handler
from cybersentinel.notifier import AlertNotifier, NotificationRecord


def test_handler_supports_direct_event() -> None:
    response = handler(
        {
            "source": "github",
            "query": "acme password",
            "raw_text": "password=supersecret",
        }
    )

    body = json.loads(response["body"])
    assert response["statusCode"] == 200
    assert body["verdict"]["is_threat"] is True
    assert body["alerts_sent"] == []


def test_handler_supports_api_gateway_event() -> None:
    response = handler(
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

    body = json.loads(response["body"])
    assert body["verdict"]["severity"] == "CRITICAL"
    assert len(body["alerts_sent"]) == 1


class FakeSnsClient:
    def __init__(self) -> None:
        self.messages: list[dict[str, str]] = []

    def publish(self, **kwargs: str) -> None:
        self.messages.append(kwargs)


def test_notifier_publishes_to_sns_when_configured() -> None:
    client = FakeSnsClient()
    notifier = AlertNotifier(
        sns_topic_arn="arn:aws:sns:us-east-1:123456789012:cybersentinel",
        sns_client=client,
    )

    notifier._publish_to_sns(
        NotificationRecord(
            source="github",
            query="acme key",
            severity="CRITICAL",
            threat_type="Cloud_Credential_Leak",
            summary="Detected exposed cloud credential.",
        )
    )

    assert len(client.messages) == 1
    assert client.messages[0]["TopicArn"].endswith(":cybersentinel")
