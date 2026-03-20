from __future__ import annotations

import json
import logging
from typing import Any


LOGGER_NAME = "cybersentinel"


def get_logger() -> logging.Logger:
    logger = logging.getLogger(LOGGER_NAME)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    return logger


def log_event(event_type: str, **fields: Any) -> None:
    payload = {"event_type": event_type, **fields}
    get_logger().info(json.dumps(payload, sort_keys=True))
