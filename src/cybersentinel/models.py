from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(slots=True)
class ThreatInput:
    source: str
    query: str
    raw_text: str


@dataclass(slots=True)
class ThreatVerdict:
    is_threat: bool
    threat_type: str
    severity: str
    summary: str

    def to_dict(self) -> dict[str, str | bool]:
        return asdict(self)

