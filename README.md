# CyberSentinel AI

Hackathon MVP backend for automated OSINT threat hunting.

Core flow: GitHub code search -> analyze -> optional alert.

## What’s Included

- GitHub code-search collector (REST API)
- Heuristic analyzer with optional Bedrock inference
- Optional SNS notifier (best-effort)
- Lambda-style handler plus a local CLI runner

## Project Layout

```text
src/cybersentinel/
  analyzer.py
  cli.py
  collector.py
  config.py
  lambda_handler.py
  models.py
  notifier.py
  pipeline.py
prompts/
  system_prompt.txt
tests/
  test_analyzer.py
  test_cli.py
  test_collector.py
  test_lambda_handler.py
```

## Quick Start

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .[dev]
pytest
```

## CLI Usage

End-to-end (collect + analyze):

```powershell
python -m cybersentinel.cli --source github --query "acme password"
```

Analyze direct text (no collector):

```powershell
python -m cybersentinel.cli --source github --query "acme leak" --raw-text "BEGIN RSA PRIVATE KEY"
```

## GitHub Token (Optional)

For higher rate limits:

```powershell
$env:GITHUB_TOKEN="ghp_your_token_here"
```

## Bedrock (Optional)

```powershell
$env:AWS_REGION="us-east-1"
$env:CYBERSENTINEL_BEDROCK_MODEL_ID="anthropic.claude-3-haiku-20240307-v1:0"
```

If Bedrock is unavailable, analysis falls back to the deterministic heuristic path.

## SNS (Optional)

```powershell
$env:CYBERSENTINEL_SNS_TOPIC_ARN="arn:aws:sns:us-east-1:123456789012:cybersentinel-alerts"
$env:CYBERSENTINEL_ALERT_THRESHOLD="CRITICAL"
```

If SNS or `boto3` is unavailable, alerts are still returned in the handler/CLI output for demo purposes.
