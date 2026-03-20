import type { AnalyzePayload } from "../types/threat";

interface AnalyzeFormProps {
  form: AnalyzePayload;
  loading: boolean;
  canSubmit: boolean;
  onChange: (field: keyof AnalyzePayload, value: string) => void;
  onSubmit: () => void;
  onLoadSample: (type: "malicious" | "benign") => void;
  onClear: () => void;
}

export function AnalyzeForm({
  form,
  loading,
  canSubmit,
  onChange,
  onSubmit,
  onLoadSample,
  onClear,
}: AnalyzeFormProps) {
  return (
    <section className="rounded-[28px] border border-white/70 bg-white/80 p-6 shadow-glow backdrop-blur xl:p-7">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.28em] text-steel">
            Analyze Panel
          </p>
          <h2 className="mt-2 text-2xl font-bold text-ink">Submit threat input</h2>
        </div>
        <div className="rounded-full bg-ink px-3 py-1 text-xs font-medium text-white">
          MVP flow
        </div>
      </div>

      <div className="grid gap-5">
        <label className="grid gap-2">
          <span className="text-sm font-semibold text-ink">Source</span>
          <select
            value={form.source}
            onChange={(event) => onChange("source", event.target.value)}
            className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-ink outline-none transition focus:border-emerald-400 focus:ring-4 focus:ring-emerald-100"
          >
            <option value="github">github</option>
          </select>
        </label>

        <label className="grid gap-2">
          <span className="text-sm font-semibold text-ink">Query</span>
          <input
            value={form.query}
            onChange={(event) => onChange("query", event.target.value)}
            placeholder="acme password"
            className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-ink outline-none transition focus:border-sky-400 focus:ring-4 focus:ring-sky-100"
          />
        </label>

        <label className="grid gap-2">
          <span className="text-sm font-semibold text-ink">Raw text</span>
          <textarea
            value={form.raw_text}
            onChange={(event) => onChange("raw_text", event.target.value)}
            rows={8}
            placeholder="Paste suspicious content to classify"
            className="min-h-44 rounded-3xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-ink outline-none transition focus:border-rose-400 focus:ring-4 focus:ring-rose-100"
          />
        </label>
        {!canSubmit && !loading ? (
          <p className="text-xs text-rose-700">Please paste raw text before analyzing.</p>
        ) : null}

        <div className="flex flex-wrap gap-3">
          <button
            type="button"
            onClick={onSubmit}
            disabled={loading || !canSubmit}
            className="rounded-2xl bg-ink px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
          >
            {loading ? "Analyzing..." : "Analyze"}
          </button>
          <button
            type="button"
            onClick={() => onLoadSample("malicious")}
            disabled={loading}
            className="rounded-2xl border border-rose-200 bg-rose-50 px-5 py-3 text-sm font-semibold text-rose-700 transition hover:bg-rose-100 disabled:opacity-50"
          >
            Load malicious sample
          </button>
          <button
            type="button"
            onClick={() => onLoadSample("benign")}
            disabled={loading}
            className="rounded-2xl border border-emerald-200 bg-emerald-50 px-5 py-3 text-sm font-semibold text-emerald-700 transition hover:bg-emerald-100 disabled:opacity-50"
          >
            Load benign sample
          </button>
          <button
            type="button"
            onClick={onClear}
            disabled={loading}
            className="rounded-2xl border border-slate-200 bg-white px-5 py-3 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 disabled:opacity-50"
          >
            Clear
          </button>
        </div>
      </div>
    </section>
  );
}
