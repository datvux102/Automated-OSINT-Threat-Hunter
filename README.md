# CyberSentinel AI

CyberSentinel AI is an MVP scaffold for an automated OSINT threat hunting pipeline. It turns the original project brief into a Python-based serverless repository with clear integration boundaries for:

- collecting raw text from public sources
- classifying potential leaks with an LLM-compatible analysis step
- emitting critical alerts through a notifier interface

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

## Bedrock Configuration

Set these environment variables to enable live model classification:

```powershell
$env:AWS_REGION="us-east-1"
$env:CYBERSENTINEL_BEDROCK_MODEL_ID="anthropic.claude-3-haiku-20240307-v1:0"
```

If Bedrock is unavailable, the analyzer falls back to the local heuristic path so local development still works.

## Next Steps

- harden the Bedrock response parsing and model-specific request handling
- implement a real collector client for approved OSINT sources
- wire the notifier to Amazon SNS
- add deployment automation for AWS environments
