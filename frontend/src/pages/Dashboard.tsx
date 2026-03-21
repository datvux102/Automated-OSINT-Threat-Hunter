import { useEffect, useMemo, useState } from "react";
import { AnalyzeForm } from "../components/AnalyzeForm";
import { AlertsPanel } from "../components/AlertsPanel";
import { CopyButton } from "../components/CopyButton";
import { HistoryTable } from "../components/HistoryTable";
import { JsonInspector } from "../components/JsonInspector";
import { VerdictCard } from "../components/VerdictCard";
import { AppShell } from "../layouts/AppShell";
import { analyzeThreat, checkHealth } from "../services/api";
import type {
  AnalyzeDraft,
  AnalyzeResponse,
  HealthResponse,
  HistoryItem,
} from "../types/threat";
import { copyText } from "../utils/clipboard";
import { detectHeuristicSignals } from "../utils/heuristicSignals";

const maliciousSample: AnalyzeDraft = {
  source: "github",
  query: "acme password",
  raw_text: "AWS_SECRET_ACCESS_KEY=abcd1234example",
};

const benignSample: AnalyzeDraft = {
  source: "github",
  query: "docs example",
  raw_text: "Example only: api_key='your_api_key_here'",
};

const emptyForm: AnalyzeDraft = {
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

interface DashboardProps {
  draft: AnalyzeDraft;
  onDraftChange: (draft: AnalyzeDraft) => void;
  onAnalyzeSuccess: (response: AnalyzeResponse) => void;
}

export function Dashboard({ draft, onDraftChange, onAnalyzeSuccess }: DashboardProps) {
  const [form, setForm] = useState<AnalyzeDraft>(draft);
  const [response, setResponse] = useState<AnalyzeResponse | null>(null);
  const [rawResponse, setRawResponse] = useState<unknown>(null);
  const [analyzedRawText, setAnalyzedRawText] = useState<string | null>(null);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthError, setHealthError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setForm(draft);
  }, [draft]);

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

  const updateField = (field: keyof AnalyzeDraft, value: string) => {
    setForm((current) => {
      const next = { ...current, [field]: value };
      onDraftChange(next);
      return next;
    });
  };

  const loadSample = (type: "malicious" | "benign") => {
    const sample = type === "malicious" ? maliciousSample : benignSample;
    setForm(sample);
    onDraftChange(sample);
    setError(null);
    setResponse(null);
    setRawResponse(null);
    setAnalyzedRawText(null);
  };

  const clearForm = () => {
    setForm(emptyForm);
    onDraftChange(emptyForm);
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
      onAnalyzeSuccess(result.normalized);
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
    <AppShell
      eyebrow="CyberSentinel Console"
      title="AI-assisted OSINT leak triage and alerting"
      description="Paste suspicious public content, classify it with the current Python backend, and inspect the verdict, alert trail, and session history from a triage-first dashboard."
    >
      <section className="rounded-[28px] border border-white/70 bg-ink p-5 text-white shadow-glow">
        <div className="flex flex-wrap items-center justify-between gap-4">
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
          <CopyButton
            onCopy={() => copyText(JSON.stringify(form, null, 2))}
            label="Copy analyze payload"
            className="border-white/20 bg-white/10 text-white hover:bg-white/20"
          />
        </div>
        {healthError ? <p className="mt-3 max-w-sm text-sm text-amber-200">{healthError}</p> : null}
      </section>

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
          inputText={analyzedRawText}
        />
      </section>

      <section className="mt-6 grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <AlertsPanel alerts={response?.alerts_sent ?? []} loading={loading} error={error} />
        <JsonInspector
          payload={rawResponse}
          loading={loading}
          error={error}
          onCopy={
            rawResponse ? () => copyText(JSON.stringify(rawResponse, null, 2)) : undefined
          }
        />
      </section>

      <section className="mt-6">
        <HistoryTable items={history} />
      </section>
    </AppShell>
  );
}
