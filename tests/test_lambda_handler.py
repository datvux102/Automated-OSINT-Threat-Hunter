import json

from cybersentinel.lambda_handler import handler


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
