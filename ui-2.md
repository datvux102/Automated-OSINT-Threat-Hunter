You are a senior product engineer working inside the repository "Automated-OSINT-Threat-Hunter".

Your task is to evolve the current single-page demo into a clean, hackathon-ready multi-page UI without breaking the existing backend contracts.

First, inspect the repository before making changes.

Current ground truth you must respect:
- The project is a hackathon MVP for automated OSINT threat hunting.
- The current core flow is: GitHub code search -> analyze -> optional alert.
- The frontend already exists and currently supports a single dashboard around analysis.
- The local backend bridge currently exposes:
  - GET /api/health
  - POST /api/analyze
- The analyze payload is:
  {
    "source": "github",
    "query": "acme password",
    "raw_text": "..."
  }
- The normalized analyze response is:
  {
    "input": {
      "source": "...",
      "query": "..."
    },
    "verdict": {
      "is_threat": true,
      "threat_type": "Cloud_Credential_Leak",
      "severity": "CRITICAL",
      "summary": "..."
    },
    "alerts_sent": [...]
  }
- Severity values are exactly: LOW, MEDIUM, HIGH, CRITICAL.
- Do not invent fields such as confidence, recommended_action, owner, incident_id, or evidence_count unless you also implement them properly across the backend and frontend.
- Do not add auth, database, queues, or enterprise admin features.
- Keep the system demo-friendly and easy for a 2-person team to maintain.

Product goal:
Turn the app into a small but coherent SOC-style console with 3–4 routes:
1. "/" -> Triage Dashboard
2. "/collector" -> Hunt & Collect
3. "/alerts" -> Alert Center
4. "/settings" -> System / Integration Health

Important backend reality:
- Collector functionality already exists in Python code, but it is not yet exposed through the current dev server API.
- Alert persistence does not exist yet.
- Health endpoint is basic.
- Any new page that depends on missing backend capabilities must either:
  1. add a minimal backend adapter endpoint, or
  2. use clearly-labeled local/session-only data.
- Do not fake live backend functionality.

Implementation rules:
- Use React + TypeScript + Tailwind.
- Preserve the current visual design language.
- Build incrementally and keep the app runnable after each step.
- Prefer route-based architecture using react-router if not already present.
- Add only minimal backend changes needed to support the new UI.
- Keep all changes modular and easy to review.

Required implementation plan:

Phase 0 - Inspect and summarize
- Read the current frontend structure and backend bridge.
- Summarize existing routes, components, types, and API contracts.
- Identify any inconsistencies before editing.

Phase 1 - App shell and routing
- Add a shared app shell with navigation.
- Convert the current dashboard into the "/" route.
- Preserve all current dashboard functionality.

Phase 2 - Collector page
- Add a new page at "/collector".
- Backend: add a minimal POST /api/collect endpoint that wraps the existing Python collector.
- Frontend collector page should include:
  - source selector, default github
  - query input
  - collect button
  - result cards/snippets
  - empty/loading/error states
  - “Send to Analyze” action that routes data into the existing analyze flow
- Do not expose GitHub tokens in the browser.
- Do not fake collector results.

Phase 3 - Alert Center
- Add a new page at "/alerts".
- Start with session-only or localStorage-backed alert history.
- Show:
  - severity
  - threat type
  - source
  - query
  - summary
  - timestamp if available locally
- Add filtering by severity and source.
- Add a detail drawer or detail panel.
- Clearly label persistence as local/session if no backend storage exists.

Phase 4 - Settings / System Health
- Add a new page at "/settings".
- Backend: add a minimal GET /api/system-status endpoint.
- It should report only real capabilities derived from current config, such as:
  - backend_ok
  - collector_enabled
  - github_token_configured
  - bedrock_enabled
  - sns_enabled
- Frontend should render these as status cards/checks.
- Include a small “How to run locally” help section if useful.

Phase 5 - UX polish
- Improve loading, empty, and error states across all pages.
- Keep layout responsive for laptop demo screens.
- Add copy actions where useful:
  - copy raw JSON
  - copy snippet
  - copy payload
- Avoid clutter and keep the UI fast.

Suggested file structure:
- frontend/src/App.tsx
- frontend/src/router.tsx or routing inside App.tsx
- frontend/src/layouts/AppShell.tsx
- frontend/src/pages/Dashboard.tsx
- frontend/src/pages/CollectorPage.tsx
- frontend/src/pages/AlertsPage.tsx
- frontend/src/pages/SettingsPage.tsx
- frontend/src/components/NavBar.tsx
- frontend/src/components/CollectorResults.tsx
- frontend/src/components/AlertFilters.tsx
- frontend/src/components/SystemStatusCard.tsx
- frontend/src/services/api.ts
- frontend/src/types/threat.ts
- frontend/src/types/collector.ts
- src/cybersentinel/dev_server.py
- src/cybersentinel/collector.py
- src/cybersentinel/config.py

Minimal new backend contracts to add:

POST /api/collect
Request:
{
  "source": "github",
  "query": "acme password"
}

Response:
{
  "ok": true,
  "record": {
    "source": "github",
    "query": "acme password",
    "raw_text": "..."
  }
}

GET /api/system-status
Response:
{
  "ok": true,
  "backend_ok": true,
  "collector_enabled": true,
  "github_token_configured": true,
  "bedrock_enabled": false,
  "sns_enabled": false
}

Important constraints:
- Do not rewrite the whole backend.
- Do not break /api/analyze or /api/health.
- Do not add database persistence.
- Do not invent unsupported cloud behavior.
- Keep the README and developer workflow accurate.
- If you change contracts, update frontend types and README together.
- If there is a conflict between visual ambition and backend truth, prefer backend truth.

Definition of done:
- Existing dashboard still works.
- App has navigation and multiple pages.
- Collector page is real and uses a backend endpoint.
- Alerts page is useful even if local/session-backed only.
- Settings page reflects real backend capability state.
- Types are clean and consistent.
- The app remains demo-ready and hackathon-appropriate.

Now start by:
1. inspecting the current repo,
2. summarizing what already exists,
3. proposing the smallest safe implementation order,
4. then implementing phase by phase.