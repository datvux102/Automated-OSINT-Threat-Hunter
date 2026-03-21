import type { AnalyzeResponse, ArchivedAlert } from "../types/threat";

const ALERT_STORAGE_KEY = "cybersentinel.local-alerts";

function isStoredAlert(value: unknown): value is ArchivedAlert {
  if (typeof value !== "object" || value === null) return false;
  const record = value as Record<string, unknown>;
  return (
    typeof record.id === "string" &&
    typeof record.timestamp === "string" &&
    typeof record.source === "string" &&
    typeof record.query === "string" &&
    typeof record.severity === "string" &&
    typeof record.threat_type === "string" &&
    typeof record.summary === "string"
  );
}

export function loadArchivedAlerts(): ArchivedAlert[] {
  if (typeof window === "undefined") return [];

  try {
    const raw = window.localStorage.getItem(ALERT_STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed.filter(isStoredAlert);
  } catch {
    return [];
  }
}

export function saveArchivedAlerts(alerts: ArchivedAlert[]): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(ALERT_STORAGE_KEY, JSON.stringify(alerts));
}

export function buildArchivedAlerts(response: AnalyzeResponse, timestamp: string): ArchivedAlert[] {
  return response.alerts_sent.map((alert, index) => ({
    id: `${timestamp}-${index}-${alert.source}-${alert.query}`,
    timestamp,
    source: alert.source,
    query: alert.query,
    severity: alert.severity,
    threat_type: alert.threat_type,
    summary: alert.summary,
  }));
}
