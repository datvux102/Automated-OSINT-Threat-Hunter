import { useEffect, useMemo, useState } from "react";
import { AlertFilters } from "../components/AlertFilters";
import { SeverityBadge } from "../components/SeverityBadge";
import { AppShell } from "../layouts/AppShell";
import type { ArchivedAlert, Severity } from "../types/threat";

interface AlertsPageProps {
  alerts: ArchivedAlert[];
  onClearAlerts: () => void;
}

export function AlertsPage({ alerts, onClearAlerts }: AlertsPageProps) {
  const [selectedSeverity, setSelectedSeverity] = useState<Severity | "ALL">("ALL");
  const [selectedSource, setSelectedSource] = useState<string>("ALL");
  const [selectedAlertId, setSelectedAlertId] = useState<string | null>(alerts[0]?.id ?? null);

  const sources = useMemo(
    () => Array.from(new Set(alerts.map((alert) => alert.source))).sort(),
    [alerts],
  );

  const filteredAlerts = useMemo(
    () =>
      alerts.filter((alert) => {
        const severityMatches =
          selectedSeverity === "ALL" || alert.severity === selectedSeverity;
        const sourceMatches = selectedSource === "ALL" || alert.source === selectedSource;
        return severityMatches && sourceMatches;
      }),
    [alerts, selectedSeverity, selectedSource],
  );

  useEffect(() => {
    if (!filteredAlerts.some((alert) => alert.id === selectedAlertId)) {
      setSelectedAlertId(filteredAlerts[0]?.id ?? null);
    }
  }, [filteredAlerts, selectedAlertId]);

  const selectedAlert =
    filteredAlerts.find((alert) => alert.id === selectedAlertId) ?? filteredAlerts[0] ?? null;

  return (
    <AppShell
      eyebrow="CyberSentinel Console"
      title="Review locally archived alert history"
      description="Alert Center keeps a browser-local archive of alerts that were actually emitted by the analyze flow. It is demo-friendly persistence, not backend storage."
    >
      <div className="grid gap-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <AlertFilters
            severity={selectedSeverity}
            source={selectedSource}
            sources={sources}
            onSeverityChange={setSelectedSeverity}
            onSourceChange={setSelectedSource}
          />
          <button
            type="button"
            onClick={onClearAlerts}
            className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
          >
            Clear local archive
          </button>
        </div>

        {filteredAlerts.length === 0 ? (
          <section className="rounded-[28px] border border-dashed border-slate-300 bg-white/70 p-8 text-sm text-slate-600">
            No locally archived alerts match the current filters.
          </section>
        ) : (
          <section className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
            <div className="grid gap-4">
              {filteredAlerts.map((alert) => (
                <button
                  type="button"
                  key={alert.id}
                  onClick={() => setSelectedAlertId(alert.id)}
                  className={`rounded-[28px] border p-5 text-left shadow-glow transition ${
                    selectedAlert?.id === alert.id
                      ? "border-sky-300 bg-sky-50"
                      : "border-slate-200 bg-white/80 hover:bg-white"
                  }`}
                >
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <p className="text-sm font-semibold text-ink">{alert.threat_type}</p>
                    <SeverityBadge severity={alert.severity} />
                  </div>
                  <p className="mt-3 text-sm leading-6 text-slate-600">{alert.summary}</p>
                  <div className="mt-4 flex flex-wrap gap-3 text-xs text-slate-500">
                    <span>{alert.source}</span>
                    <span>{alert.query || "n/a"}</span>
                    <span>{new Date(alert.timestamp).toLocaleString()}</span>
                  </div>
                </button>
              ))}
            </div>

            <section className="rounded-[28px] border border-slate-200 bg-white/80 p-6 shadow-glow">
              {selectedAlert ? (
                <>
                  <div className="flex flex-wrap items-center justify-between gap-4">
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-[0.28em] text-steel">
                        Alert Detail
                      </p>
                      <h2 className="mt-2 text-2xl font-bold text-ink">
                        {selectedAlert.threat_type}
                      </h2>
                    </div>
                    <SeverityBadge severity={selectedAlert.severity} />
                  </div>

                  <div className="mt-6 grid gap-4 sm:grid-cols-2">
                    <div className="rounded-3xl bg-slate-50 p-4 ring-1 ring-slate-200">
                      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-steel">
                        Source
                      </p>
                      <p className="mt-2 text-sm font-semibold text-ink">
                        {selectedAlert.source}
                      </p>
                    </div>
                    <div className="rounded-3xl bg-slate-50 p-4 ring-1 ring-slate-200">
                      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-steel">
                        Query
                      </p>
                      <p className="mt-2 text-sm font-semibold text-ink">
                        {selectedAlert.query || "n/a"}
                      </p>
                    </div>
                  </div>

                  <div className="mt-4 rounded-3xl bg-ink p-5 text-mist">
                    <p className="text-xs font-semibold uppercase tracking-[0.18em] text-sky-200">
                      Summary
                    </p>
                    <p className="mt-3 text-sm leading-7">{selectedAlert.summary}</p>
                  </div>

                  <p className="mt-4 text-xs text-slate-500">
                    Archived locally at {new Date(selectedAlert.timestamp).toLocaleString()}.
                  </p>
                </>
              ) : null}
            </section>
          </section>
        )}
      </div>
    </AppShell>
  );
}
