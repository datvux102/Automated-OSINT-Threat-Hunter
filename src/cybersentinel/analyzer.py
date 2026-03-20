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
        normalized = text.lower()

        if not text:
            return ThreatVerdict(
                is_threat=False,
                threat_type="No_Content",
                severity="LOW",
                summary="Input contained no analyzable text.",
            )

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
        text_fragments: list[str] = []
        for item in payload.get("content", []):
            if item.get("type") == "text":
                text_fragments.append(item.get("text", ""))

        if not text_fragments:
            return None

        response_text = "\n".join(text_fragments).strip()
        json_start = response_text.find("{")
        json_end = response_text.rfind("}")
        if json_start == -1 or json_end == -1 or json_end < json_start:
            return None

        data = json.loads(response_text[json_start : json_end + 1])
        try:
            return ThreatVerdict(
                is_threat=bool(data["is_threat"]),
                threat_type=str(data["threat_type"]),
                severity=str(data["severity"]).upper(),
                summary=str(data["summary"]),
            )
        except KeyError:
            return None
