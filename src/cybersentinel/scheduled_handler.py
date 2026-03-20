from __future__ import annotations

import json

from cybersentinel.config import Settings
from cybersentinel.logging_utils import log_event
from cybersentinel.pipeline import collect_and_process


def handler(event: dict, context: object | None = None) -> dict:
    settings = Settings.from_env()
    source = event.get("source", settings.default_source)
    query = event.get("query", settings.default_query)
    log_event(
        "lambda_invocation",
        handler="scheduled_collection",
        source=source,
        query=query,
    )

    if not query:
        log_event(
            "scheduled_collection_skipped",
            source=source,
            reason="missing_query",
        )
        return {
            "statusCode": 400,
            "body": json.dumps(
                {
                    "error": "No query configured for scheduled execution.",
                    "source": source,
                }
            ),
        }

    result = collect_and_process(
        source=source,
        query=query,
        settings=settings,
    )
    return {
        "statusCode": 200,
        "body": json.dumps(result),
    }
