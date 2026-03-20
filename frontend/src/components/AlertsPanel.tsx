import type { AlertRecord } from "../types/threat";

interface AlertsPanelProps {
  alerts: AlertRecord[];
  loading?: boolean;
  error?: string | null;
}

export function AlertsPanel({ alerts, loading, error }: AlertsPanelProps) {
  return (
    <section className="rounded-[28px] border border-slate-200 bg-white/80 p-6 shadow-glow">
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.28em] text-steel">
            Alerts Panel
          </p>
          <h2 className="mt-2 text-2xl font-bold text-ink">Triggered notifications</h2>
        </div>
        <div className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">
          {loading ? "..." : `${alerts.length} total`}
        </div>
      </div>

      {loading ? (
        <div className="mt-6 space-y-3">
          <div className="h-8 w-2/3 animate-pulse rounded-full bg-slate-200" />
          <div className="h-24 animate-pulse rounded-3xl bg-slate-100" />
        </div>
      ) : error ? (
        <div className="mt-6 rounded-3xl border border-rose-200 bg-rose-50 p-5 text-sm text-rose-800">
          Analysis failed. No alerts available.
        </div>
      ) : alerts.length === 0 ? (
        <div className="mt-6 rounded-3xl border border-dashed border-slate-300 bg-slate-50 p-5 text-sm text-slate-600">
          No alerts sent.
        </div>
      ) : (
        <div className="mt-6 grid gap-4">
          {alerts.map((alert, index) => (
            <article
              key={`${alert.query}-${index}`}
              className="rounded-3xl bg-slate-950 p-5 text-slate-100"
            >
              <div className="flex flex-wrap items-center justify-between gap-3">
                <p className="text-sm font-semibold">{alert.threat_type}</p>
                <span className="rounded-full bg-rose-500/20 px-3 py-1 text-xs font-semibold text-rose-200">
                  {alert.severity}
                </span>
              </div>
              <p className="mt-3 text-sm leading-6 text-slate-300">{alert.summary}</p>
              <div className="mt-4 flex flex-wrap gap-3 text-xs text-slate-400">
                <span>Source: {alert.source}</span>
                <span>Query: {alert.query}</span>
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
