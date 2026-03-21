import type { Severity } from "../types/threat";

interface AlertFiltersProps {
  severity: Severity | "ALL";
  source: string;
  sources: string[];
  onSeverityChange: (value: Severity | "ALL") => void;
  onSourceChange: (value: string) => void;
}

const severityOptions: Array<Severity | "ALL"> = ["ALL", "LOW", "MEDIUM", "HIGH", "CRITICAL"];

export function AlertFilters({
  severity,
  source,
  sources,
  onSeverityChange,
  onSourceChange,
}: AlertFiltersProps) {
  return (
    <section className="rounded-[28px] border border-slate-200 bg-white/80 p-6 shadow-glow">
      <div className="flex flex-wrap gap-4">
        <label className="grid min-w-[180px] gap-2">
          <span className="text-xs font-semibold uppercase tracking-[0.22em] text-steel">
            Severity
          </span>
          <select
            value={severity}
            onChange={(event) => onSeverityChange(event.target.value as Severity | "ALL")}
            className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-ink outline-none transition focus:border-sky-400 focus:ring-4 focus:ring-sky-100"
          >
            {severityOptions.map((option) => (
              <option key={option} value={option}>
                {option === "ALL" ? "All severities" : option}
              </option>
            ))}
          </select>
        </label>

        <label className="grid min-w-[180px] gap-2">
          <span className="text-xs font-semibold uppercase tracking-[0.22em] text-steel">
            Source
          </span>
          <select
            value={source}
            onChange={(event) => onSourceChange(event.target.value)}
            className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-ink outline-none transition focus:border-emerald-400 focus:ring-4 focus:ring-emerald-100"
          >
            <option value="ALL">All sources</option>
            {sources.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        </label>
      </div>
    </section>
  );
}
