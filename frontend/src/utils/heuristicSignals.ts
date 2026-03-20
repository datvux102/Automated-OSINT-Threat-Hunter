import type { Severity } from "../types/threat";

// Keep this in sync with `src/cybersentinel/analyzer.py` heuristic dictionaries.
const HIGH_SIGNAL_PATTERNS: Record<
  string,
  { threat_type: string; severity: Severity }
> = {
  "AWS_SECRET_ACCESS_KEY": { threat_type: "Cloud_Credential_Leak", severity: "CRITICAL" },
  "BEGIN RSA PRIVATE KEY": { threat_type: "Private_Key_Leak", severity: "CRITICAL" },
  "ghp_": { threat_type: "GitHub_Token_Leak", severity: "HIGH" },
  "password=": { threat_type: "Credential_Leak", severity: "HIGH" },
  "api_key": { threat_type: "API_Key_Leak", severity: "MEDIUM" },
};

const LOW_SIGNAL_TERMS = new Set<string>([
  "example",
  "dummy",
  "sample",
  "test key",
  "lorem ipsum",
]);

export type HeuristicHighSignal = {
  pattern: string;
  threat_type: string;
  severity: Severity;
};

export type HeuristicSignals = {
  lowSignals: string[];
  highSignals: HeuristicHighSignal[];
};

export function detectHeuristicSignals(rawText: string): HeuristicSignals {
  const normalized = rawText.toLowerCase();

  const lowSignals: string[] = [];
  for (const term of LOW_SIGNAL_TERMS) {
    if (term && normalized.includes(term)) {
      lowSignals.push(term);
    }
  }

  const highSignals: HeuristicHighSignal[] = [];
  for (const [pattern, meta] of Object.entries(HIGH_SIGNAL_PATTERNS)) {
    if (pattern && normalized.includes(pattern.toLowerCase())) {
      highSignals.push({
        pattern,
        threat_type: meta.threat_type,
        severity: meta.severity,
      });
    }
  }

  return { lowSignals, highSignals };
}

