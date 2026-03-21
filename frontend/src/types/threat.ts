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
  severity: Severity;
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

export interface AnalyzeDraft extends AnalyzePayload {}

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

export interface ArchivedAlert extends AlertRecord {
  id: string;
  timestamp: string;
}

export interface SystemStatusResponse {
  ok: boolean;
  backend_ok: boolean;
  collector_enabled: boolean;
  github_token_configured: boolean;
  bedrock_enabled: boolean;
  sns_enabled: boolean;
}
