export type Severity = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

export interface ThreatVerdict {
  is_threat: boolean;
  threat_type: string;
  severity: Severity;
  summary: string;
}

export interface AlertRecord {
  source: string;
  query: string;
  severity: string;
  threat_type: string;
  summary: string;
}

export interface AnalyzeResponse {
  input: {
    source: string;
    query: string;
  };
  verdict: ThreatVerdict;
  alerts_sent: AlertRecord[];
}

export interface AnalyzePayload {
  source: string;
  query: string;
  raw_text: string;
}

export interface HistoryItem {
  id: string;
  time: string;
  input: AnalyzeResponse["input"];
  verdict: ThreatVerdict;
  alertCount: number;
}

export interface HealthResponse {
  ok: boolean;
  message: string;
}
