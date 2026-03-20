import json

from cybersentinel import scheduled_handler


def test_scheduled_handler_requires_query(monkeypatch) -> None:
    monkeypatch.delenv("CYBERSENTINEL_DEFAULT_QUERY", raising=False)
    response = scheduled_handler.handler({})

    body = json.loads(response["body"])
    assert response["statusCode"] == 400
    assert "No query configured" in body["error"]


def test_scheduled_handler_uses_event_query(monkeypatch) -> None:
    monkeypatch.delenv("CYBERSENTINEL_DEFAULT_QUERY", raising=False)

    def fake_collect_and_process(source: str, query: str, settings):
        return {
            "input": {"source": source, "query": query},
            "verdict": {
                "is_threat": False,
                "threat_type": "No_Threat_Detected",
                "severity": "LOW",
                "summary": "No issue found.",
            },
            "alerts_sent": [],
            "collected": {
                "source": source,
                "query": query,
                "raw_text": "",
            },
        }

    monkeypatch.setattr(scheduled_handler, "collect_and_process", fake_collect_and_process)
    response = scheduled_handler.handler({"source": "github", "query": "acme password"})

    body = json.loads(response["body"])
    assert response["statusCode"] == 200
    assert body["input"]["query"] == "acme password"
