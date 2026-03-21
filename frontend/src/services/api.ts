import type { CollectPayload, CollectResponse } from "../types/collector";
import type {
  AnalyzePayload,
  AnalyzeResponse,
  HealthResponse,
  Severity,
  SystemStatusResponse,
} from "../types/threat";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";
const normalizedBase = API_BASE_URL.replace(/\/+$/, "");
const ANALYZE_ENDPOINT = `${normalizedBase}/api/analyze`;
const HEALTH_ENDPOINT = `${normalizedBase}/api/health`;
const COLLECT_ENDPOINT = `${normalizedBase}/api/collect`;
const SYSTEM_STATUS_ENDPOINT = `${normalizedBase}/api/system-status`;
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

      const alertSeverity = String(alert.severity ?? "").toUpperCase() as Severity;
      if (!VALID_SEVERITIES.includes(alertSeverity)) {
        throw new Error("Alert record severity is invalid.");
      }

      return {
        source: String(alert.source ?? ""),
        query: String(alert.query ?? ""),
        severity: alertSeverity,
        threat_type: String(alert.threat_type ?? ""),
        summary: String(alert.summary ?? ""),
      };
    }),
  };
}

function normalizeCollectResponse(payload: unknown): CollectResponse {
  const unwrapped = unwrapResponseShape(payload);
  if (!isRecord(unwrapped) || !isRecord(unwrapped.record)) {
    throw new Error("Collector response is missing the record payload.");
  }

  return {
    ok: Boolean(unwrapped.ok),
    record: {
      source: String(unwrapped.record.source ?? ""),
      query: String(unwrapped.record.query ?? ""),
      raw_text: String(unwrapped.record.raw_text ?? ""),
    },
  };
}

function normalizeSystemStatus(payload: unknown): SystemStatusResponse {
  const unwrapped = unwrapResponseShape(payload);
  if (!isRecord(unwrapped)) {
    throw new Error("System status response is invalid.");
  }

  return {
    ok: Boolean(unwrapped.ok),
    backend_ok: Boolean(unwrapped.backend_ok),
    collector_enabled: Boolean(unwrapped.collector_enabled),
    github_token_configured: Boolean(unwrapped.github_token_configured),
    bedrock_enabled: Boolean(unwrapped.bedrock_enabled),
    sns_enabled: Boolean(unwrapped.sns_enabled),
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

export async function collectThreatSource(
  payload: CollectPayload,
): Promise<CollectResponse> {
  const raw = await requestJson<unknown>(COLLECT_ENDPOINT, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  return normalizeCollectResponse(raw);
}

export async function getSystemStatus(): Promise<SystemStatusResponse> {
  const raw = await requestJson<unknown>(SYSTEM_STATUS_ENDPOINT);
  return normalizeSystemStatus(raw);
}
