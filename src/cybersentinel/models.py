from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass
class ThreatInput:
    source: str
    query: str
    raw_text: str


@dataclass
class ThreatVerdict:
    is_threat: bool
    threat_type: str
    severity: str
    summary: str

    def to_dict(self) -> dict[str, str | bool]:
        return asdict(self)

