import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { CollectorResults } from "../components/CollectorResults";
import { CopyButton } from "../components/CopyButton";
import { AppShell } from "../layouts/AppShell";
import { collectThreatSource } from "../services/api";
import type { CollectPayload, CollectRecord } from "../types/collector";
import type { AnalyzeDraft } from "../types/threat";
import { copyText } from "../utils/clipboard";

interface CollectorPageProps {
  onSendToAnalyzeDraft: (draft: AnalyzeDraft) => void;
}

const emptyCollectForm: CollectPayload = {
  source: "github",
  query: "",
};

export function CollectorPage({ onSendToAnalyzeDraft }: CollectorPageProps) {
  const navigate = useNavigate();
  const [form, setForm] = useState<CollectPayload>(emptyCollectForm);
  const [record, setRecord] = useState<CollectRecord | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canSubmit = form.query.trim().length > 0;

  const updateField = (field: keyof CollectPayload, value: string) => {
    setForm((current) => ({ ...current, [field]: value }));
  };

  const submit = async () => {
    if (!canSubmit) {
      setError("Please enter a GitHub search query before collecting.");
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const result = await collectThreatSource(form);
      setRecord(result.record);
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Collector request failed unexpectedly.",
      );
      setRecord(null);
    } finally {
      setLoading(false);
    }
  };

  const handleSendToAnalyze = (nextRecord: CollectRecord) => {
    onSendToAnalyzeDraft({
      source: nextRecord.source,
      query: nextRecord.query,
      raw_text: nextRecord.raw_text,
    });
    navigate("/");
  };

  return (
    <AppShell
      eyebrow="CyberSentinel Console"
      title="Hunt suspicious public snippets before analysis"
      description="Run the real GitHub-backed collector through the local Python bridge, inspect the returned snippets, and hand the result off to triage when you see something worth analyzing."
    >
      <section className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
        <section className="rounded-[28px] border border-white/70 bg-white/80 p-6 shadow-glow backdrop-blur xl:p-7">
          <div className="mb-6 flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.28em] text-steel">
                Collector Control
              </p>
              <h2 className="mt-2 text-2xl font-bold text-ink">Hunt & Collect</h2>
            </div>
            <div className="rounded-full bg-ink px-3 py-1 text-xs font-medium text-white">
              Live backend
            </div>
          </div>

          <div className="grid gap-5">
            <label className="grid gap-2">
              <span className="text-sm font-semibold text-ink">Source</span>
              <select
                value={form.source}
                onChange={(event) => updateField("source", event.target.value)}
                className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-ink outline-none transition focus:border-emerald-400 focus:ring-4 focus:ring-emerald-100"
              >
                <option value="github">github</option>
              </select>
            </label>

            <label className="grid gap-2">
              <span className="text-sm font-semibold text-ink">Query</span>
              <input
                value={form.query}
                onChange={(event) => updateField("query", event.target.value)}
                placeholder="acme password"
                className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-ink outline-none transition focus:border-sky-400 focus:ring-4 focus:ring-sky-100"
              />
            </label>

            <div className="rounded-3xl bg-slate-50 p-5 ring-1 ring-slate-200">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-600">
                Notes
              </p>
              <p className="mt-3 text-sm leading-6 text-slate-600">
                The browser never receives GitHub credentials directly. It only talks to the
                local `/api/collect` bridge.
              </p>
            </div>

            {error && !loading ? (
              <p className="text-xs text-rose-700">{error}</p>
            ) : null}

            <div className="flex flex-wrap gap-3">
              <button
                type="button"
                onClick={submit}
                disabled={loading || !canSubmit}
                className="rounded-2xl bg-ink px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
              >
                {loading ? "Collecting..." : "Collect"}
              </button>
              <CopyButton
                onCopy={() => copyText(JSON.stringify(form, null, 2))}
                label="Copy payload"
              />
            </div>
          </div>
        </section>

        <CollectorResults
          record={record}
          loading={loading}
          error={error}
          onSendToAnalyze={handleSendToAnalyze}
          onCopyAll={(nextRecord) => copyText(JSON.stringify(nextRecord, null, 2))}
          onCopySnippet={(snippet) => copyText(snippet)}
        />
      </section>
    </AppShell>
  );
}
