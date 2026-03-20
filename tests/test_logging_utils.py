import json
import logging

from cybersentinel.logging_utils import get_logger, log_event


def test_log_event_emits_json_payload(caplog) -> None:
    logger = get_logger()
    with caplog.at_level(logging.INFO, logger=logger.name):
        log_event("analysis_completed", severity="HIGH", alerts_sent=1)

    payload = json.loads(caplog.records[-1].message)
    assert payload["event_type"] == "analysis_completed"
    assert payload["severity"] == "HIGH"
    assert payload["alerts_sent"] == 1
