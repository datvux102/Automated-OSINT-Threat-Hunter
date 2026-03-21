import { useEffect, useState } from "react";
import { SystemStatusCard } from "../components/SystemStatusCard";
import { AppShell } from "../layouts/AppShell";
import { checkHealth, getSystemStatus } from "../services/api";
import type { HealthResponse, SystemStatusResponse } from "../types/threat";

export function SettingsPage() {
  const [status, setStatus] = useState<SystemStatusResponse | null>(null);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    void Promise.all([getSystemStatus(), checkHealth()])
      .then(([systemStatus, healthStatus]) => {
        if (cancelled) return;
        setStatus(systemStatus);
        setHealth(healthStatus);
        setError(null);
      })
      .catch((requestError) => {
        if (cancelled) return;
        setError(
          requestError instanceof Error
            ? requestError.message
            : "Unable to load backend status.",
        );
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <AppShell
      eyebrow="CyberSentinel Console"
      title="Inspect real backend and integration status"
      description="This page only reports capabilities that can be derived from the local bridge and current environment configuration. No backend health is fabricated."
    >
      {loading ? (
        <section className="rounded-[28px] border border-slate-200 bg-white/80 p-6 shadow-glow">
          <div className="h-6 w-48 animate-pulse rounded-full bg-slate-200" />
          <div className="mt-4 h-24 animate-pulse rounded-3xl bg-slate-100" />
        </section>
      ) : error ? (
        <section className="rounded-[28px] border border-rose-200 bg-rose-50 p-6 shadow-glow">
          <h2 className="text-xl font-bold text-rose-800">Unable to load system status</h2>
          <p className="mt-3 text-sm leading-6 text-rose-700">{error}</p>
        </section>
      ) : status ? (
        <div className="grid gap-6">
          <section className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
            <SystemStatusCard
              label="Backend Bridge"
              value={status.backend_ok}
              description={health?.message ?? "Backend connected"}
            />
            <SystemStatusCard
              label="Collector"
              value={status.collector_enabled}
              description="GitHub collector is available through the local /api/collect bridge."
            />
            <SystemStatusCard
              label="GitHub Token"
              value={status.github_token_configured}
              description="Indicates whether a GitHub token is configured on the backend for better rate limits."
            />
            <SystemStatusCard
              label="Bedrock"
              value={status.bedrock_enabled}
              description="Shows whether Bedrock inference is enabled via environment configuration."
            />
            <SystemStatusCard
              label="SNS"
              value={status.sns_enabled}
              description="Shows whether SNS alert delivery is configured on the backend."
            />
          </section>

          <section className="rounded-[28px] border border-slate-200 bg-white/80 p-6 shadow-glow">
            <p className="text-xs font-semibold uppercase tracking-[0.28em] text-steel">
              Local Runbook
            </p>
            <div className="mt-4 grid gap-4 text-sm text-slate-600 md:grid-cols-2">
              <div className="rounded-3xl bg-slate-50 p-5 ring-1 ring-slate-200">
                <p className="font-semibold text-ink">Backend bridge</p>
                <pre className="mt-3 whitespace-pre-wrap text-xs leading-6 text-slate-700">
                  python -m cybersentinel.dev_server
                </pre>
              </div>
              <div className="rounded-3xl bg-slate-50 p-5 ring-1 ring-slate-200">
                <p className="font-semibold text-ink">Frontend</p>
                <pre className="mt-3 whitespace-pre-wrap text-xs leading-6 text-slate-700">
                  cd frontend{"\n"}npm install{"\n"}npm run dev
                </pre>
              </div>
              <div className="rounded-3xl bg-slate-50 p-5 ring-1 ring-slate-200">
                <p className="font-semibold text-ink">Optional GitHub token</p>
                <pre className="mt-3 whitespace-pre-wrap text-xs leading-6 text-slate-700">
                  GITHUB_TOKEN=ghp_your_token_here
                </pre>
              </div>
              <div className="rounded-3xl bg-slate-50 p-5 ring-1 ring-slate-200">
                <p className="font-semibold text-ink">Optional cloud integrations</p>
                <pre className="mt-3 whitespace-pre-wrap text-xs leading-6 text-slate-700">
                  CYBERSENTINEL_BEDROCK_MODEL_ID=...
                  {"\n"}CYBERSENTINEL_SNS_TOPIC_ARN=...
                </pre>
              </div>
            </div>
          </section>
        </div>
      ) : null}
    </AppShell>
  );
}
