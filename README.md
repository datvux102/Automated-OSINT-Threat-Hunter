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

## Demo UI

A demo-ready frontend lives in `frontend/` and talks to the existing handler through a tiny local bridge server.

Backend bridge:

```powershell
python -m cybersentinel.dev_server
```

Frontend:

```powershell
cd frontend
npm install
npm run dev
```

The Vite app proxies `/api/*` requests to `http://127.0.0.1:8000`, and the backend bridge exposes:

- `GET /api/health`
- `POST /api/analyze`
- `POST /api/collect`
- `GET /api/system-status`

Frontend routes:

- `/` - Triage Dashboard
- `/collector` - Hunt & Collect
- `/alerts` - Alert Center
- `/settings` - System / Integration Health

Notes:

- Alert Center is browser-local only and uses local storage for demo persistence
- Collector results are real backend responses from the Python GitHub collector bridge
- `Send to Analyze` prefills the dashboard with collected data but does not auto-run analysis

## Backend Bridge Contracts

Health:

```json
{
  "ok": true,
  "message": "Backend connected"
}
```

Collect:

```json
POST /api/collect
{
  "source": "github",
  "query": "acme password"
}
```

```json
{
  "ok": true,
  "record": {
    "source": "github",
    "query": "acme password",
    "raw_text": "..."
  }
}
```

System status:

```json
{
  "ok": true,
  "backend_ok": true,
  "collector_enabled": true,
  "github_token_configured": false,
  "bedrock_enabled": false,
  "sns_enabled": false
}
```

## Deploy (Public Web URL)

Easiest path is deploying the included `Dockerfile` (builds the Vite UI + serves it from the same Python server):

- Entry point: `python -m cybersentinel.web_server`
- Health check: `/api/health`
- Port: from `$PORT` (defaults to `8000`)

Render (recommended):

1. Push this repo to GitHub.
2. In Render: **New** → **Blueprint** → select the repo (it will detect `render.yaml`).
3. Deploy and open the generated URL.

## Bedrock Configuration

## Production-Like E2E Check

Run a one-command smoke flow that validates backend API behavior and frontend build output:

```bash
./scripts/run_prod_e2e.sh
```

What it does:

- builds frontend assets
- starts backend bridge locally on `127.0.0.1:8000`
- runs smoke checks for:
  - `GET /api/health`
  - `POST /api/analyze` (benign sample)
  - `POST /api/analyze` (critical sample)

You can override defaults:

```bash
PYTHON_BIN=python3 BACKEND_PORT=8000 ./scripts/run_prod_e2e.sh
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
