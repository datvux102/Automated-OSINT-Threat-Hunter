# CyberSentinel AI

CyberSentinel AI is an MVP scaffold for an automated OSINT threat hunting pipeline. It turns the original project brief into a Python-based serverless repository with clear integration boundaries for:

- collecting raw text from public sources
- classifying potential leaks with an LLM-compatible analysis step
- emitting critical alerts through a notifier interface

## Status

This repository is an MVP backend scaffold. It includes:

- a Lambda-style entry point
- heuristic classification with optional Amazon Bedrock inference
- in-memory alert recording with optional Amazon SNS publishing
- GitHub code search collection for one approved OSINT source
- local tests that do not require AWS credentials

## Architecture

1. A collector gathers candidate leak content from an external source.
2. An API-compatible event sends raw text into the Lambda handler.
3. The analyzer classifies the content and produces a normalized threat verdict.
4. Critical findings are passed to the notifier.

The current implementation is deliberately local-first:

- external providers are stubbed behind interfaces
- deterministic heuristics are used by default for analysis
- Bedrock can be enabled through environment variables
- tests run without AWS credentials

## Project Layout

```text
src/cybersentinel/
  analyzer.py
  collector.py
  config.py
  lambda_handler.py
  models.py
  notifier.py
prompts/
  system_prompt.txt
tests/
  test_analyzer.py
  test_lambda_handler.py
template.yaml
```

## Quick Start

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .[dev]
pytest
```

If `pytest` is not installed yet, `pip install -e .[dev]` is required before running the test suite.

## Running Locally

The Lambda handler accepts either:

- a direct event with `source`, `query`, and `raw_text`
- an API Gateway event where the payload is in `body`

Example payload:

```json
{
  "source": "github",
  "query": "acme password",
  "raw_text": "AWS_SECRET_ACCESS_KEY=abcd1234example"
}
```

To collect candidate matches from GitHub code search in code, use `CollectorClient.collect("github", "...")`. The collector is currently limited to GitHub and formats the top few matches into a plain-text bundle for downstream analysis.

## CLI Usage

Run the end-to-end pipeline directly:

```powershell
python -m cybersentinel.cli --source github --query "acme password"
```

Run analysis against direct text without calling the collector:

```powershell
python -m cybersentinel.cli --source github --query "acme leak" --raw-text "BEGIN RSA PRIVATE KEY"
```

If installed with `pip install -e .`, the console command `cybersentinel` is also available.

## Scheduled AWS Execution

The SAM template now includes a scheduled Lambda entry point in [scheduled_handler.py](C:/Users/Gia%20Bao/Documents/D%E1%BB%B1%20%C3%A1n%20c%C3%A1%20nh%C3%A2n/Automated%20OSINT%20Threat%20Hunter/src/cybersentinel/scheduled_handler.py). It runs `collect -> analyze -> alert` on a timer and reads:

```powershell
$env:CYBERSENTINEL_DEFAULT_SOURCE="github"
$env:CYBERSENTINEL_DEFAULT_QUERY="acme password"
```

If `CYBERSENTINEL_DEFAULT_QUERY` is empty, the scheduled handler returns a `400` response instead of running a meaningless collection job.

## Deployment

For local SAM deployment, use [deploy.ps1](C:/Users/Gia%20Bao/Documents/D%E1%BB%B1%20%C3%A1n%20c%C3%A1%20nh%C3%A2n/Automated%20OSINT%20Threat%20Hunter/scripts/deploy.ps1):

```powershell
.\scripts\deploy.ps1 `
  -StackName CyberSentinelAI `
  -S3Bucket your-sam-artifacts-bucket `
  -Region us-east-1 `
  -DefaultQuery "acme password" `
  -GitHubTokenSecretArn "arn:aws:secretsmanager:us-east-1:123456789012:secret:github-token" `
  -AlarmNotificationTopicArn "arn:aws:sns:us-east-1:123456789012:cybersentinel-alarms" `
  -BedrockModelId "anthropic.claude-3-haiku-20240307-v1:0"
```

This script requires the AWS SAM CLI and valid AWS credentials in your shell.

For GitHub-based manual deploys, use [.github/workflows/deploy.yml](C:/Users/Gia%20Bao/Documents/D%E1%BB%B1%20%C3%A1n%20c%C3%A1%20nh%C3%A2n/Automated%20OSINT%20Threat%20Hunter/.github/workflows/deploy.yml). It expects repository secrets:

- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`

The deploy path now supports storing the GitHub token in AWS Secrets Manager instead of plain environment variables. Pass the secret ARN as `GitHubTokenSecretArn` and store either:

- a raw token string
- a JSON object with `token` or `github_token`

The stack now also provisions dead-letter queues for both Lambda functions and CloudWatch alarms for scheduled-job failures and DLQ depth. To receive alarm notifications, pass `AlarmNotificationTopicArn`.

## Bedrock Configuration

Set these environment variables to enable live model classification:

```powershell
$env:AWS_REGION="us-east-1"
$env:CYBERSENTINEL_BEDROCK_MODEL_ID="anthropic.claude-3-haiku-20240307-v1:0"
```

If Bedrock is unavailable, the analyzer falls back to the local heuristic path so local development still works.

## SNS Configuration

Set a topic ARN to publish alerts for findings at or above the configured threshold:

```powershell
$env:CYBERSENTINEL_SNS_TOPIC_ARN="arn:aws:sns:us-east-1:123456789012:cybersentinel-alerts"
$env:CYBERSENTINEL_ALERT_THRESHOLD="CRITICAL"
```

If SNS is unavailable or `boto3` is missing, alerts are still returned in the handler response for local verification.

## GitHub Collector Configuration

For higher rate limits and private access control, set a token before using the collector:

```powershell
$env:GITHUB_TOKEN="ghp_your_token_here"
```

For deployed AWS environments, prefer Secrets Manager instead:

```powershell
$env:CYBERSENTINEL_GITHUB_TOKEN_SECRET_ARN="arn:aws:secretsmanager:us-east-1:123456789012:secret:github-token"
```

Retry behavior is configurable for transient GitHub failures:

```powershell
$env:CYBERSENTINEL_GITHUB_MAX_ATTEMPTS="3"
$env:CYBERSENTINEL_GITHUB_BACKOFF_SECONDS="1.0"
```

The collector retries on transient HTTP failures such as `429`, `503`, and similar upstream errors, and raises clearer errors for rate-limit exhaustion.

Pagination is also configurable:

```powershell
$env:CYBERSENTINEL_GITHUB_PER_PAGE="5"
$env:CYBERSENTINEL_GITHUB_MAX_PAGES="3"
```

Collected GitHub hits are normalized into stable text blocks with repository, path, URL, and cleaned snippet content before analysis.

Optional overrides:

```powershell
$env:CYBERSENTINEL_GITHUB_API_URL="https://api.github.com"
$env:CYBERSENTINEL_GITHUB_API_VERSION="2022-11-28"
```

The collector uses GitHub code search and currently keeps only a small number of top matches for downstream classification.

## CI

GitHub Actions CI is defined in [.github/workflows/ci.yml](C:/Users/Gia%20Bao/Documents/D%E1%BB%B1%20%C3%A1n%20c%C3%A1%20nh%C3%A2n/Automated%20OSINT%20Threat%20Hunter/.github/workflows/ci.yml). On pushes to `main` and pull requests, it:

- installs Python 3.11
- installs the project with dev dependencies
- runs `pytest`
- runs `python -m compileall src tests`

## Operations

Runtime logs are now emitted as structured JSON lines from [logging_utils.py](C:/Users/Gia%20Bao/Documents/D%E1%BB%B1%20%C3%A1n%20c%C3%A1%20nh%C3%A2n/Automated%20OSINT%20Threat%20Hunter/src/cybersentinel/logging_utils.py), which makes CloudWatch log filtering simpler for collection and analysis events.

## Next Steps

- harden the Bedrock response parsing and model-specific request handling
- add richer operational dashboards and alarm coverage for analyzer/notification failures
- add source-specific normalization for additional collectors beyond GitHub
