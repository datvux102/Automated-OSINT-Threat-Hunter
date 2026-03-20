from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any, Callable
from urllib.parse import quote
from urllib.request import Request, urlopen


@dataclass(slots=True)
class CollectedRecord:
    source: str
    query: str
    raw_text: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


class CollectorClient:
    """GitHub code-search collector for public leak hunting workflows."""

    def __init__(
        self,
        github_token: str = "",
        github_token_secret_arn: str = "",
        github_api_url: str = "https://api.github.com",
        github_api_version: str = "2022-11-28",
        aws_region: str = "us-east-1",
        opener: Callable[..., object] | None = None,
        secrets_client: Any | None = None,
    ) -> None:
        self.github_token = github_token
        self.github_token_secret_arn = github_token_secret_arn
        self.github_api_url = github_api_url.rstrip("/")
        self.github_api_version = github_api_version
        self.aws_region = aws_region
        self._opener = opener or urlopen
        self._secrets_client = secrets_client

    def collect(self, source: str, query: str) -> CollectedRecord:
        if source.lower() != "github":
            raise ValueError(f"Unsupported source: {source}")

        if not self.github_token and self.github_token_secret_arn:
            self.github_token = self._load_github_token_from_secret() or ""

        raw_text = self._collect_from_github(query)
        return CollectedRecord(
            source=source,
            query=query,
            raw_text=raw_text,
        )

    def _collect_from_github(self, query: str) -> str:
        endpoint = (
            f"{self.github_api_url}/search/code"
            f"?q={quote(query)}&per_page=5"
        )
        request = Request(
            endpoint,
            headers=self._build_headers(),
            method="GET",
        )
        with self._opener(request, timeout=15) as response:
            payload = json.loads(response.read().decode("utf-8"))

        snippets: list[str] = []
        for item in payload.get("items", []):
            repository = item.get("repository", {}).get("full_name", "unknown")
            path = item.get("path", "")
            html_url = item.get("html_url", "")
            fragments = [
                fragment.get("fragment", "").strip()
                for fragment in item.get("text_matches", [])
                if fragment.get("fragment")
            ]
            snippet = "\n".join(part for part in fragments if part)
            snippets.append(
                "\n".join(
                    [
                        f"repository: {repository}",
                        f"path: {path}",
                        f"url: {html_url}",
                        f"snippet: {snippet}".strip(),
                    ]
                ).strip()
            )

        return "\n\n---\n\n".join(snippets)

    def _build_headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/vnd.github.text-match+json",
            "User-Agent": "CyberSentinel-AI",
            "X-GitHub-Api-Version": self.github_api_version,
        }
        if self.github_token:
            headers["Authorization"] = f"Bearer {self.github_token}"
        return headers

    def _load_github_token_from_secret(self) -> str | None:
        client = self._get_secrets_client()
        if client is None:
            return None

        try:
            response = client.get_secret_value(SecretId=self.github_token_secret_arn)
        except Exception:
            return None

        secret_string = response.get("SecretString")
        if not secret_string:
            return None

        try:
            secret_payload = json.loads(secret_string)
        except json.JSONDecodeError:
            return secret_string

        if isinstance(secret_payload, dict):
            token = secret_payload.get("token") or secret_payload.get("github_token")
            return str(token) if token else None
        return None

    def _get_secrets_client(self) -> Any | None:
        if self._secrets_client is not None:
            return self._secrets_client

        try:
            import boto3
        except ImportError:
            return None

        self._secrets_client = boto3.client(
            "secretsmanager",
            region_name=self.aws_region,
        )
        return self._secrets_client
