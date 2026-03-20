from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


DEFAULT_PROMPT_PATH = Path("prompts/system_prompt.txt")


@dataclass(slots=True)
class Settings:
    alert_threshold: str = "CRITICAL"
    system_prompt_path: Path = DEFAULT_PROMPT_PATH
    bedrock_model_id: str = ""
    aws_region: str = "us-east-1"
    sns_topic_arn: str = ""
    github_token: str = ""
    github_token_secret_arn: str = ""
    github_api_url: str = "https://api.github.com"
    github_api_version: str = "2022-11-28"
    github_max_attempts: int = 3
    github_backoff_seconds: float = 1.0
    default_source: str = "github"
    default_query: str = ""

    @classmethod
    def from_env(cls) -> "Settings":
        prompt_path = Path(
            os.getenv("CYBERSENTINEL_SYSTEM_PROMPT_PATH", str(DEFAULT_PROMPT_PATH))
        )
        return cls(
            alert_threshold=os.getenv("CYBERSENTINEL_ALERT_THRESHOLD", "CRITICAL"),
            system_prompt_path=prompt_path,
            bedrock_model_id=os.getenv("CYBERSENTINEL_BEDROCK_MODEL_ID", ""),
            aws_region=os.getenv("AWS_REGION", os.getenv("AWS_DEFAULT_REGION", "us-east-1")),
            sns_topic_arn=os.getenv("CYBERSENTINEL_SNS_TOPIC_ARN", ""),
            github_token=os.getenv("GITHUB_TOKEN", ""),
            github_token_secret_arn=os.getenv("CYBERSENTINEL_GITHUB_TOKEN_SECRET_ARN", ""),
            github_api_url=os.getenv("CYBERSENTINEL_GITHUB_API_URL", "https://api.github.com"),
            github_api_version=os.getenv("CYBERSENTINEL_GITHUB_API_VERSION", "2022-11-28"),
            github_max_attempts=int(os.getenv("CYBERSENTINEL_GITHUB_MAX_ATTEMPTS", "3")),
            github_backoff_seconds=float(
                os.getenv("CYBERSENTINEL_GITHUB_BACKOFF_SECONDS", "1.0")
            ),
            default_source=os.getenv("CYBERSENTINEL_DEFAULT_SOURCE", "github"),
            default_query=os.getenv("CYBERSENTINEL_DEFAULT_QUERY", ""),
        )
