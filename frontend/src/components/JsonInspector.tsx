interface JsonInspectorProps {
  payload: unknown;
  loading?: boolean;
  error?: string | null;
  onCopy?: () => void;
}

export function JsonInspector({ payload, loading, error, onCopy }: JsonInspectorProps) {
  return (
    <section className="rounded-[28px] border border-slate-200 bg-white/80 p-6 shadow-glow">
      <div className="flex items-center justify-between gap-3">
        <p className="text-xs font-semibold uppercase tracking-[0.28em] text-steel">
          Raw JSON Inspector
        </p>
        {onCopy ? (
          <button
            type="button"
            onClick={onCopy}
            className="rounded-2xl border border-slate-200 bg-white px-4 py-2 text-xs font-semibold text-slate-700 transition hover:bg-slate-50"
          >
            Copy JSON
          </button>
        ) : null}
      </div>
      {loading ? (
        <div className="mt-4 rounded-3xl bg-slate-950 p-5 text-slate-100">
          <div className="h-6 w-56 animate-pulse rounded-full bg-slate-800" />
          <pre className="mt-4 overflow-x-auto whitespace-pre-wrap text-xs leading-6 text-slate-300">
            Loading backend response...
          </pre>
        </div>
      ) : error ? (
        <div className="mt-4 rounded-3xl border border-rose-200 bg-rose-50 p-5 text-sm text-rose-800">
          Analysis failed; no backend response to inspect.
        </div>
      ) : (
        <details className="mt-4 rounded-3xl bg-slate-950 p-5 text-slate-100">
          <summary className="cursor-pointer text-sm font-semibold text-sky-200">
            Toggle backend response
          </summary>
          <pre className="mt-4 overflow-x-auto whitespace-pre-wrap text-xs leading-6 text-slate-300">
            {payload ? JSON.stringify(payload, null, 2) : "No response yet."}
          </pre>
        </details>
      )}
    </section>
  );
}
