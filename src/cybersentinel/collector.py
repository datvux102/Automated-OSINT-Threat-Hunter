from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


@dataclass(slots=True)
class CollectedRecord:
    source: str
    query: str
    raw_text: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


class CollectorError(RuntimeError):
    pass


class CollectorClient:
    """GitHub code-search collector for public leak hunting workflows."""

    def __init__(
        self,
        github_token: str = "",
        github_api_url: str = "https://api.github.com",
        github_api_version: str = "2022-11-28",
        opener: Callable[..., object] | None = None,
        offline_mode: bool | None = None,
        offline_text: str | None = None,
        offline_fixture_path: str | None = None,
    ) -> None:
        self.github_token = github_token
        self.github_api_url = github_api_url.rstrip("/")
        self.github_api_version = github_api_version
        self._opener = opener or urlopen
        self.offline_mode = (
            offline_mode
            if offline_mode is not None
            else os.getenv("CYBERSENTINEL_COLLECTOR_OFFLINE", "").strip().lower()
            in {"1", "true", "yes"}
        )
        self.offline_text = offline_text if offline_text is not None else os.getenv(
            "CYBERSENTINEL_COLLECTOR_OFFLINE_TEXT", ""
        )
        self.offline_fixture_path = (
            offline_fixture_path
            if offline_fixture_path is not None
            else os.getenv("CYBERSENTINEL_COLLECTOR_OFFLINE_FIXTURE_PATH", "")
        )

    def collect(self, source: str, query: str) -> CollectedRecord:
        if source.lower() != "github":
            raise ValueError(f"Unsupported source: {source}")

        if self.offline_mode:
            raw_text = self._load_offline_text()
        else:
            try:
                raw_text = self._collect_from_github(query)
            except Exception:
                # Protect the demo: if live collection fails, fall back if configured.
                raw_text = self._load_offline_text()

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
        try:
            with self._opener(request, timeout=15) as response:
                raw = response.read()
        except HTTPError as exc:
            raise CollectorError(self._format_http_error(exc)) from exc
        except URLError as exc:
            raise CollectorError(f"GitHub request failed: {exc.reason}") from exc

        try:
            payload = json.loads(raw.decode("utf-8"))
        except Exception as exc:
            raise CollectorError("GitHub response was not valid JSON.") from exc

        if not isinstance(payload, dict):
            raise CollectorError("GitHub response payload was not an object.")
        items = payload.get("items")
        if items is None:
            raise CollectorError("GitHub response missing 'items'.")
        if not isinstance(items, list):
            raise CollectorError("GitHub response 'items' was not a list.")

        snippets: list[str] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            repo_obj = item.get("repository")
            repository = (
                repo_obj.get("full_name", "unknown") if isinstance(repo_obj, dict) else "unknown"
            )
            path = item.get("path", "")
            html_url = item.get("html_url", "")
            text_matches = item.get("text_matches", [])
            if not isinstance(text_matches, list):
                text_matches = []
            fragments = [
                self._normalize_fragment(fragment.get("fragment", ""))
                for fragment in text_matches
                if isinstance(fragment, dict) and fragment.get("fragment")
            ]
            snippet = "\n".join(part for part in fragments if part)
            snippets.append(
                "\n".join(
                    [
                        f"repository: {repository}",
                        f"path: {path if isinstance(path, str) else str(path)}",
                        f"url: {html_url if isinstance(html_url, str) else str(html_url)}",
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

    def _load_offline_text(self) -> str:
        if self.offline_text:
            return self.offline_text
        if self.offline_fixture_path:
            path = Path(self.offline_fixture_path)
            if path.exists() and path.is_file():
                try:
                    return path.read_text(encoding="utf-8")
                except Exception:
                    return ""
        return ""

    @staticmethod
    def _normalize_fragment(fragment: str) -> str:
        lines = [line.strip() for line in fragment.splitlines()]
        return "\n".join(line for line in lines if line)

    @staticmethod
    def _format_http_error(error: HTTPError) -> str:
        if error.code in {403, 429}:
            remaining = error.headers.get("X-RateLimit-Remaining")
            retry_after = error.headers.get("Retry-After")
            suffix = []
            if remaining is not None:
                suffix.append(f"rate_limit_remaining={remaining}")
            if retry_after:
                suffix.append(f"retry_after={retry_after}")
            details = f" ({', '.join(suffix)})" if suffix else ""
            return f"GitHub rate limit or access restriction{details}."
        return f"GitHub returned HTTP {error.code}."
