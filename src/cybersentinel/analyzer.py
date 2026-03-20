from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from cybersentinel.models import ThreatInput, ThreatVerdict


HIGH_SIGNAL_PATTERNS = {
    "AWS_SECRET_ACCESS_KEY": ("Cloud_Credential_Leak", "CRITICAL"),
    "BEGIN RSA PRIVATE KEY": ("Private_Key_Leak", "CRITICAL"),
    "ghp_": ("GitHub_Token_Leak", "HIGH"),
    "password=": ("Credential_Leak", "HIGH"),
    "api_key": ("API_Key_Leak", "MEDIUM"),
}

LOW_SIGNAL_TERMS = {
    "example",
    "dummy",
    "sample",
    "test key",
    "lorem ipsum",
}

SEVERITY_ORDER = {
    "LOW": 1,
    "MEDIUM": 2,
    "HIGH": 3,
    "CRITICAL": 4,
}
VALID_SEVERITIES = frozenset(SEVERITY_ORDER)
REQUIRED_BEDROCK_KEYS = frozenset({"is_threat", "threat_type", "severity", "summary"})

BUNDLE_SEPARATOR = "\n\n---\n\n"


class ThreatAnalyzer:
    """Analyzer with optional Bedrock inference and heuristic fallback."""

    def __init__(
        self,
        system_prompt_path: Path | None = None,
        bedrock_model_id: str = "",
        aws_region: str = "us-east-1",
        bedrock_client: Any | None = None,
    ) -> None:
        self.system_prompt_path = system_prompt_path
        self.system_prompt = self._load_prompt(system_prompt_path)
        self.bedrock_model_id = bedrock_model_id
        self.aws_region = aws_region
        self._bedrock_client = bedrock_client

    def analyze(self, threat_input: ThreatInput) -> ThreatVerdict:
        text = threat_input.raw_text.strip()

        if not text:
            return ThreatVerdict(
                is_threat=False,
                threat_type="No_Content",
                severity="LOW",
                summary="Input contained no analyzable text.",
            )

        segments = self._split_segments(text)
        segment_verdicts = [
            self._analyze_single_text(
                ThreatInput(
                    source=threat_input.source,
                    query=threat_input.query,
                    raw_text=segment,
                )
            )
            for segment in segments
        ]
        return self._aggregate_segment_verdicts(segment_verdicts, len(segments))

    def _analyze_single_text(self, threat_input: ThreatInput) -> ThreatVerdict:
        text = threat_input.raw_text.strip()
        normalized = text.lower()

        if any(term in normalized for term in LOW_SIGNAL_TERMS):
            return ThreatVerdict(
                is_threat=False,
                threat_type="Benign_Example",
                severity="LOW",
                summary="Content looks like sample or placeholder data.",
            )

        bedrock_verdict = self._analyze_with_bedrock(threat_input)
        if bedrock_verdict is not None:
            return bedrock_verdict

        for pattern, (threat_type, severity) in HIGH_SIGNAL_PATTERNS.items():
            if pattern.lower() in normalized:
                return ThreatVerdict(
                    is_threat=True,
                    threat_type=threat_type,
                    severity=severity,
                    summary=f"Matched high-signal indicator: {pattern}.",
                )

        return ThreatVerdict(
            is_threat=False,
            threat_type="No_Threat_Detected",
            severity="LOW",
            summary="No high-confidence leak indicators were found.",
        )

    @staticmethod
    def _split_segments(text: str) -> list[str]:
        segments = [segment.strip() for segment in text.split(BUNDLE_SEPARATOR)]
        return [segment for segment in segments if segment]

    @staticmethod
    def _aggregate_segment_verdicts(
        verdicts: list[ThreatVerdict],
        segment_count: int,
    ) -> ThreatVerdict:
        if not verdicts:
            return ThreatVerdict(
                is_threat=False,
                threat_type="No_Content",
                severity="LOW",
                summary="Input contained no analyzable text.",
            )

        top_verdict = max(
            verdicts,
            key=lambda verdict: (
                verdict.is_threat,
                SEVERITY_ORDER.get(verdict.severity, 0),
            ),
        )
        if segment_count <= 1:
            return top_verdict

        threat_count = sum(1 for verdict in verdicts if verdict.is_threat)
        summary = (
            f"Analyzed {segment_count} collected hits; "
            f"{threat_count} potential threat(s). "
            f"Top finding: {top_verdict.summary}"
        )
        return ThreatVerdict(
            is_threat=top_verdict.is_threat,
            threat_type=top_verdict.threat_type,
            severity=top_verdict.severity,
            summary=summary,
        )

    @staticmethod
    def _load_prompt(path: Path | None) -> str:
        if path is None or not path.exists():
            return ""
        return path.read_text(encoding="utf-8")

    def _analyze_with_bedrock(self, threat_input: ThreatInput) -> ThreatVerdict | None:
        if not self.bedrock_model_id:
            return None

        client = self._get_bedrock_client()
        if client is None:
            return None

        try:
            response = client.invoke_model(
                modelId=self.bedrock_model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(self._build_bedrock_request(threat_input)),
            )
            payload = self._read_bedrock_response(response)
            return self._parse_bedrock_verdict(payload)
        except Exception:
            return None

    def _get_bedrock_client(self) -> Any | None:
        if self._bedrock_client is not None:
            return self._bedrock_client

        try:
            import boto3
        except ImportError:
            return None

        self._bedrock_client = boto3.client(
            "bedrock-runtime",
            region_name=self.aws_region,
        )
        return self._bedrock_client

    def _build_bedrock_request(self, threat_input: ThreatInput) -> dict[str, Any]:
        prompt = self.system_prompt or (
            "Classify whether the text contains a real enterprise data leak."
        )
        user_text = (
            f"Source: {threat_input.source}\n"
            f"Query: {threat_input.query}\n"
            f"Content:\n{threat_input.raw_text}"
        )
        return {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 300,
            "temperature": 0,
            "system": prompt,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "Return JSON with keys is_threat, threat_type, "
                                "severity, summary.\n\n"
                                f"{user_text}"
                            ),
                        }
                    ],
                }
            ],
        }

    @staticmethod
    def _read_bedrock_response(response: dict[str, Any]) -> dict[str, Any]:
        body = response.get("body")
        if hasattr(body, "read"):
            raw_body = body.read()
        else:
            raw_body = body

        if isinstance(raw_body, bytes):
            raw_body = raw_body.decode("utf-8")

        return json.loads(raw_body)

    @staticmethod
    def _parse_bedrock_verdict(payload: dict[str, Any]) -> ThreatVerdict | None:
        text_fragments = ThreatAnalyzer._extract_bedrock_text_fragments(payload)
        if not text_fragments:
            return None

        response_text = "\n".join(text_fragments).strip()
        for candidate in ThreatAnalyzer._iter_json_object_candidates(response_text):
            verdict_dict = ThreatAnalyzer._extract_verdict_dict(candidate)
            if verdict_dict is None:
                continue
            try:
                normalized = ThreatAnalyzer._normalize_bedrock_verdict_dict(verdict_dict)
            except ValueError:
                continue
            return ThreatVerdict(**normalized)

        return None

    @staticmethod
    def _extract_bedrock_text_fragments(payload: dict[str, Any]) -> list[str]:
        text_fragments: list[str] = []
        for item in payload.get("content", []):
            if item.get("type") == "text":
                text_fragments.append(item.get("text", ""))
        if text_fragments:
            return text_fragments

        output_text = payload.get("outputText")
        if isinstance(output_text, str):
            return [output_text]

        completion = payload.get("completion")
        if isinstance(completion, str):
            return [completion]

        return []

    @staticmethod
    def _iter_json_object_candidates(text: str) -> list[dict[str, Any]]:
        # Accept common Bedrock shapes:
        # - bare JSON object
        # - fenced ```json ... ```
        # - extra prose before/after JSON
        candidates: list[dict[str, Any]] = []
        for extracted in ThreatAnalyzer._extract_possible_json_objects(text):
            try:
                parsed = json.loads(extracted)
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, dict):
                candidates.append(parsed)
        return candidates

    @staticmethod
    def _extract_possible_json_objects(text: str) -> list[str]:
        stripped = text.strip()
        extracted: list[str] = []

        # If the entire payload is fenced, strip the fences first.
        if stripped.startswith("```") and stripped.endswith("```"):
            lines = stripped.splitlines()
            if len(lines) >= 3 and lines[0].startswith("```") and lines[-1].startswith("```"):
                inner = "\n".join(lines[1:-1]).strip()
                if inner.lower().startswith("json"):
                    inner = inner[4:].strip()
                stripped = inner

        # Scan for balanced JSON objects; collect a few to avoid pathological cases.
        in_string = False
        escape = False
        depth = 0
        start_index: int | None = None

        for index, char in enumerate(stripped):
            if escape:
                escape = False
                continue
            if char == "\\":
                escape = True
                continue
            if char == '"':
                in_string = not in_string
                continue
            if in_string:
                continue

            if char == "{":
                if depth == 0:
                    start_index = index
                depth += 1
            elif char == "}":
                if depth == 0:
                    continue
                depth -= 1
                if depth == 0 and start_index is not None:
                    extracted.append(stripped[start_index : index + 1])
                    start_index = None
                    if len(extracted) >= 3:
                        break

        return extracted

    @staticmethod
    def _extract_verdict_dict(data: dict[str, Any]) -> dict[str, Any] | None:
        if REQUIRED_BEDROCK_KEYS.issubset(data.keys()):
            return data
        verdict = data.get("verdict")
        if isinstance(verdict, dict) and REQUIRED_BEDROCK_KEYS.issubset(verdict.keys()):
            return verdict
        return None

    @staticmethod
    def _coerce_bool(value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"true", "yes", "1"}:
                return True
            if normalized in {"false", "no", "0"}:
                return False
        raise ValueError("Unsupported boolean value.")

    @staticmethod
    def _normalize_bedrock_verdict_dict(data: dict[str, Any]) -> dict[str, Any]:
        if not REQUIRED_BEDROCK_KEYS.issubset(data.keys()):
            raise ValueError("Missing required Bedrock verdict keys.")

        threat_type = data["threat_type"]
        summary = data["summary"]
        severity = data["severity"]

        if not isinstance(threat_type, str) or not threat_type.strip():
            raise ValueError("Invalid threat_type.")
        if not isinstance(summary, str) or not summary.strip():
            raise ValueError("Invalid summary.")
        if not isinstance(severity, str):
            raise ValueError("Invalid severity.")

        normalized_severity = ThreatAnalyzer._normalize_severity(severity)
        if normalized_severity not in VALID_SEVERITIES:
            raise ValueError("Invalid severity.")

        return {
            "is_threat": ThreatAnalyzer._coerce_bool(data["is_threat"]),
            "threat_type": threat_type.strip(),
            "severity": normalized_severity,
            "summary": summary.strip(),
        }

    @staticmethod
    def _normalize_severity(value: str) -> str:
        normalized = value.strip().upper()
        if normalized in VALID_SEVERITIES:
            return normalized
        # Common informal variants from models.
        if "CRIT" in normalized:
            return "CRITICAL"
        if "HIGH" in normalized:
            return "HIGH"
        if "MED" in normalized:
            return "MEDIUM"
        if "LOW" in normalized:
            return "LOW"
        return normalized
