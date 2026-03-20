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
        )
