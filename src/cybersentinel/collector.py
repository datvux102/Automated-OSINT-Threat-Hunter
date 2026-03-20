from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Callable
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
        github_api_url: str = "https://api.github.com",
        github_api_version: str = "2022-11-28",
        opener: Callable[..., object] | None = None,
    ) -> None:
        self.github_token = github_token
        self.github_api_url = github_api_url.rstrip("/")
        self.github_api_version = github_api_version
        self._opener = opener or urlopen

    def collect(self, source: str, query: str) -> CollectedRecord:
        if source.lower() != "github":
            raise ValueError(f"Unsupported source: {source}")

        raw_text = self._collect_from_github(query)
        return CollectedRecord(
            source=source,
            query=query,
            raw_text=raw_text,
        )

    def _collect_from_github(self, query: str) -> str:
        endpoint = f"{self.github_api_url}/search/code?q={quote(query)}&per_page=5&page=1"
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
                self._normalize_fragment(fragment.get("fragment", ""))
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
                        f"snippet:\n{snippet}" if snippet else "snippet:",
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

    @staticmethod
    def _normalize_fragment(fragment: str) -> str:
        lines = [line.strip() for line in fragment.splitlines()]
        return "\n".join(line for line in lines if line)
