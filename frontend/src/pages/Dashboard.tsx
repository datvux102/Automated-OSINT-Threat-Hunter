import { useEffect, useMemo, useState } from "react";
import { AnalyzeForm } from "../components/AnalyzeForm";
import { AlertsPanel } from "../components/AlertsPanel";
import { HistoryTable } from "../components/HistoryTable";
import { JsonInspector } from "../components/JsonInspector";
import { VerdictCard } from "../components/VerdictCard";
import { analyzeThreat, checkHealth } from "../services/api";
import type {
  AnalyzePayload,
  AnalyzeResponse,
  HealthResponse,
  HistoryItem,
} from "../types/threat";
import { detectHeuristicSignals } from "../utils/heuristicSignals";

const maliciousSample: AnalyzePayload = {
  source: "github",
  query: "acme password",
  raw_text: "AWS_SECRET_ACCESS_KEY=abcd1234example",
};

const benignSample: AnalyzePayload = {
  source: "github",
  query: "docs example",
  raw_text: "Example only: api_key='your_api_key_here'",
};

const emptyForm: AnalyzePayload = {
  source: "github",
  query: "",
  raw_text: "",
};

function formatTime(date: Date): string {
  return new Intl.DateTimeFormat(undefined, {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  }).format(date);
}

export function Dashboard() {
  const [form, setForm] = useState<AnalyzePayload>(maliciousSample);
  const [response, setResponse] = useState<AnalyzeResponse | null>(null);
  const [rawResponse, setRawResponse] = useState<unknown>(null);
  const [analyzedRawText, setAnalyzedRawText] = useState<string | null>(null);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthError, setHealthError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canSubmit = form.raw_text.trim().length > 0;
  const heuristicSignals = useMemo(() => {
    if (!analyzedRawText) return null;
    return detectHeuristicSignals(analyzedRawText);
  }, [analyzedRawText]);

  useEffect(() => {
    let cancelled = false;

    void checkHealth()
      .then((result) => {
        if (!cancelled) {
          setHealth(result);
          setHealthError(null);
        }
      })
      .catch((healthRequestError) => {
        if (!cancelled) {
          setHealth(null);
          setHealthError(
            healthRequestError instanceof Error
              ? healthRequestError.message
              : "Unable to reach backend.",
          );
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const updateField = (field: keyof AnalyzePayload, value: string) => {
    setForm((current) => ({ ...current, [field]: value }));
  };

  const loadSample = (type: "malicious" | "benign") => {
    setForm(type === "malicious" ? maliciousSample : benignSample);
    setError(null);
    setResponse(null);
    setRawResponse(null);
    setAnalyzedRawText(null);
  };

  const clearForm = () => {
    setForm(emptyForm);
    setError(null);
    setResponse(null);
    setRawResponse(null);
    setAnalyzedRawText(null);
  };

  const submit = async () => {
    if (!canSubmit) {
      setError("Please paste raw text before analyzing.");
      return;
    }
    setAnalyzedRawText(form.raw_text);
    setLoading(true);
    setError(null);
    setResponse(null);
    setRawResponse(null);

    try {
      const result = await analyzeThreat(form);
      setResponse(result.normalized);
      setRawResponse(result.raw);
      setHistory((current) => [
        {
          id: `${Date.now()}-${current.length}`,
          time: formatTime(new Date()),
          input: result.normalized.input,
          verdict: result.normalized.verdict,
          alertCount: result.normalized.alerts_sent.length,
        },
        ...current,
      ]);
    } catch (submitError) {
      setError(
        submitError instanceof Error ? submitError.message : "Analysis failed unexpectedly.",
      );
    } finally {
      setLoading(false);
    }
  };

  const statusPillClassName = health?.ok
    ? "bg-emerald-100 text-emerald-800 ring-emerald-200"
    : "bg-amber-100 text-amber-800 ring-amber-200";

  return (
    <main className="relative overflow-hidden">
      <div className="absolute inset-0 -z-10 bg-grid bg-[size:40px_40px] opacity-60" />
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <header className="rounded-[32px] border border-white/70 bg-ink px-6 py-8 text-white shadow-glow">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
            <div className="max-w-2xl">
              <p className="text-xs font-semibold uppercase tracking-[0.32em] text-sky-200">
                CyberSentinel Console
              </p>
              <h1 className="mt-3 text-4xl font-bold sm:text-5xl">
                AI-assisted OSINT leak triage and alerting
              </h1>
              <p className="mt-4 max-w-xl text-sm leading-7 text-slate-300 sm:text-base">
                Paste suspicious public content, classify it with the current Python backend,
                and show a clean verdict, alert trail, and session history for demos.
              </p>
            </div>

            <div className="space-y-3">
              <div
                className={`inline-flex items-center gap-2 rounded-full px-4 py-2 text-sm font-semibold ring-1 ${statusPillClassName}`}
              >
                <span
                  className={`h-2.5 w-2.5 rounded-full ${
                    health?.ok ? "bg-emerald-500" : "bg-amber-500"
                  }`}
                />
                {health?.message ?? "Backend status unknown"}
              </div>
              {healthError ? (
                <p className="max-w-sm text-sm text-amber-200">{healthError}</p>
              ) : null}
            </div>
          </div>
        </header>

        <section className="mt-6 grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
          <AnalyzeForm
            form={form}
            loading={loading}
            canSubmit={canSubmit}
            onChange={updateField}
            onSubmit={submit}
            onLoadSample={loadSample}
            onClear={clearForm}
          />
          <VerdictCard
            response={response}
            loading={loading}
            error={error}
            heuristicSignals={heuristicSignals}
          />
        </section>

        <section className="mt-6 grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
          <AlertsPanel
            alerts={response?.alerts_sent ?? []}
            loading={loading}
            error={error}
          />
          <JsonInspector payload={rawResponse} loading={loading} error={error} />
        </section>

        <section className="mt-6">
          <HistoryTable items={history} />
        </section>
      </div>
    </main>
  );
}
