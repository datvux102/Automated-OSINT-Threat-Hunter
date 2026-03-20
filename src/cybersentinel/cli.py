from __future__ import annotations

import argparse
import json
from typing import Sequence

from cybersentinel.config import Settings
from cybersentinel.models import ThreatInput
from cybersentinel.pipeline import collect_and_process, process_threat_input


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="CyberSentinel AI runner")
    parser.add_argument("--source", required=True, help="Data source, currently github")
    parser.add_argument("--query", required=True, help="Search query to collect or analyze")
    parser.add_argument(
        "--raw-text",
        default="",
        help="Raw text to analyze directly. If omitted, the collector is used.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    settings = Settings.from_env()

    if args.raw_text:
        result = process_threat_input(
            threat_input=ThreatInput(
                source=args.source,
                query=args.query,
                raw_text=args.raw_text,
            ),
            settings=settings,
        )
    else:
        result = collect_and_process(
            source=args.source,
            query=args.query,
            settings=settings,
        )

    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
