import type {
  AnalyzePayload,
  AnalyzeResponse,
  HealthResponse,
  Severity,
} from "../types/threat";

const ANALYZE_ENDPOINT = "/api/analyze";
const HEALTH_ENDPOINT = "/api/health";
const VALID_SEVERITIES: Severity[] = ["LOW", "MEDIUM", "HIGH", "CRITICAL"];

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function parseJson(text: string): unknown {
  if (!text.trim()) {
    throw new Error("Server returned an empty response.");
  }

  try {
    return JSON.parse(text);
  } catch {
    throw new Error("Server returned invalid JSON.");
  }
}

function unwrapResponseShape(payload: unknown): unknown {
  if (!isRecord(payload)) {
    throw new Error("Unexpected response shape.");
  }

  if ("body" in payload) {
    const body = payload.body;
    if (typeof body === "string") {
      return parseJson(body);
    }
    if (isRecord(body)) {
      return body;
    }
    throw new Error("Response body could not be parsed.");
  }

  return payload;
}

function normalizeAnalyzeResponse(payload: unknown): AnalyzeResponse {
  const unwrapped = unwrapResponseShape(payload);
  if (!isRecord(unwrapped)) {
    throw new Error("Normalized response is not an object.");
  }

  const input = unwrapped.input;
  const verdict = unwrapped.verdict;
  const alertsSent = unwrapped.alerts_sent;

  if (!isRecord(input) || !isRecord(verdict) || !Array.isArray(alertsSent)) {
    throw new Error("Normalized response is missing required fields.");
  }

  const severity = String(verdict.severity ?? "").toUpperCase() as Severity;
  if (!VALID_SEVERITIES.includes(severity)) {
    throw new Error("Server returned an unknown severity.");
  }

  return {
    input: {
      source: String(input.source ?? ""),
      query: String(input.query ?? ""),
    },
    verdict: {
      is_threat: Boolean(verdict.is_threat),
      threat_type: String(verdict.threat_type ?? ""),
      severity,
      summary: String(verdict.summary ?? ""),
    },
    alerts_sent: alertsSent.map((alert) => {
      if (!isRecord(alert)) {
        throw new Error("Alert record is invalid.");
      }

      return {
        source: String(alert.source ?? ""),
        query: String(alert.query ?? ""),
        severity: String(alert.severity ?? ""),
        threat_type: String(alert.threat_type ?? ""),
        summary: String(alert.summary ?? ""),
      };
    }),
  };
}

async function requestJson<T>(input: RequestInfo, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(input, init);
  } catch {
    throw new Error("Network error while contacting CyberSentinel backend.");
  }

  const text = await response.text();
  const parsed = parseJson(text);

  if (!response.ok) {
    const message =
      isRecord(parsed) && typeof parsed.error === "string"
        ? parsed.error
        : `Request failed with status ${response.status}.`;
    throw new Error(message);
  }

  return parsed as T;
}

export async function analyzeThreat(
  payload: AnalyzePayload,
): Promise<{ normalized: AnalyzeResponse; raw: unknown }> {
  const raw = await requestJson<unknown>(ANALYZE_ENDPOINT, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  return {
    normalized: normalizeAnalyzeResponse(raw),
    raw,
  };
}

export async function checkHealth(): Promise<HealthResponse> {
  return requestJson<HealthResponse>(HEALTH_ENDPOINT);
}
