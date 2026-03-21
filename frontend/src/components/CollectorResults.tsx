import type { CollectRecord } from "../types/collector";
import { CopyButton } from "./CopyButton";

interface CollectorResultsProps {
  record: CollectRecord | null;
  loading: boolean;
  error: string | null;
  onSendToAnalyze: (record: CollectRecord) => void;
  onCopyAll: (record: CollectRecord) => void;
  onCopySnippet: (snippet: string) => void;
}

function splitSnippets(rawText: string): string[] {
  return rawText
    .split("\n\n---\n\n")
    .map((part) => part.trim())
    .filter(Boolean);
}

export function CollectorResults({
  record,
  loading,
  error,
  onSendToAnalyze,
  onCopyAll,
  onCopySnippet,
}: CollectorResultsProps) {
  if (loading) {
    return (
      <section className="rounded-[28px] border border-slate-200 bg-white/80 p-6 shadow-glow">
        <p className="text-xs font-semibold uppercase tracking-[0.28em] text-steel">
          Collector Results
        </p>
        <div className="mt-5 space-y-3">
          <div className="h-6 w-44 animate-pulse rounded-full bg-slate-200" />
          <div className="h-28 animate-pulse rounded-3xl bg-slate-100" />
        </div>
      </section>
    );
  }

  if (error) {
    return (
      <section className="rounded-[28px] border border-rose-200 bg-rose-50 p-6 shadow-glow">
        <p className="text-xs font-semibold uppercase tracking-[0.28em] text-rose-600">
          Collector Results
        </p>
        <h2 className="mt-3 text-xl font-bold text-rose-800">Collection failed</h2>
        <p className="mt-2 text-sm leading-6 text-rose-700">{error}</p>
      </section>
    );
  }

  if (!record) {
    return (
      <section className="rounded-[28px] border border-dashed border-slate-300 bg-white/65 p-6">
        <p className="text-xs font-semibold uppercase tracking-[0.28em] text-steel">
          Collector Results
        </p>
        <h2 className="mt-3 text-xl font-bold text-ink">Awaiting first collection</h2>
        <p className="mt-2 text-sm leading-6 text-slate-600">
          Run a live collector request to inspect the normalized raw snippets coming back from
          the Python bridge.
        </p>
      </section>
    );
  }

  const snippets = splitSnippets(record.raw_text);

  return (
    <section className="rounded-[28px] border border-slate-200 bg-white/80 p-6 shadow-glow">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.28em] text-steel">
            Collector Results
          </p>
          <h2 className="mt-2 text-2xl font-bold text-ink">Collected OSINT snippets</h2>
          <p className="mt-2 text-sm text-slate-600">
            Source: <span className="font-semibold text-ink">{record.source}</span>
            {" · "}
            Query: <span className="font-semibold text-ink">{record.query || "n/a"}</span>
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <CopyButton onCopy={() => onCopyAll(record)} label="Copy payload" />
          <button
            type="button"
            onClick={() => onSendToAnalyze(record)}
            className="rounded-2xl bg-ink px-4 py-2 text-xs font-semibold text-white transition hover:bg-slate-800"
          >
            Send to Analyze
          </button>
        </div>
      </div>

      {snippets.length === 0 ? (
        <div className="mt-6 rounded-3xl border border-dashed border-slate-300 bg-slate-50 p-5 text-sm text-slate-600">
          No results collected for this query.
        </div>
      ) : (
        <div className="mt-6 grid gap-4">
          {snippets.map((snippet, index) => (
            <article
              key={`${record.query}-${index}`}
              className="rounded-3xl bg-slate-950 p-5 text-slate-100"
            >
              <div className="flex items-center justify-between gap-3">
                <p className="text-sm font-semibold text-sky-200">Snippet {index + 1}</p>
                <CopyButton
                  onCopy={() => onCopySnippet(snippet)}
                  label="Copy snippet"
                  className="border-slate-700 bg-slate-900 text-slate-100 hover:bg-slate-800"
                />
              </div>
              <pre className="mt-4 overflow-x-auto whitespace-pre-wrap break-words text-xs leading-6 text-slate-300">
                {snippet}
              </pre>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
