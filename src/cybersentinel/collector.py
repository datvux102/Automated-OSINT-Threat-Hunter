from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(slots=True)
class CollectedRecord:
    source: str
    query: str
    raw_text: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


class CollectorClient:
    """Stub collector that defines the boundary for OSINT gathering."""

    def collect(self, source: str, query: str) -> CollectedRecord:
        return CollectedRecord(
            source=source,
            query=query,
            raw_text="",
        )

