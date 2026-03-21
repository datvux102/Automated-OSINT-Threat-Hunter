import { SeverityBadge } from "./SeverityBadge";
import type { AnalyzeResponse } from "../types/threat";
import type { HeuristicSignals } from "../utils/heuristicSignals";
import { renderHighlightedInputSnippets } from "../utils/highlightText";

interface VerdictCardProps {
  response: AnalyzeResponse | null;
  loading: boolean;
  error: string | null;
  heuristicSignals?: HeuristicSignals | null;
  inputText?: string | null;
}

export function VerdictCard({
  response,
  loading,
  error,
  heuristicSignals,
  inputText,
}: VerdictCardProps) {
  if (loading) {
    return (
      <section className="rounded-[28px] border border-slate-200 bg-white/80 p-6 shadow-glow">
        <p className="text-xs font-semibold uppercase tracking-[0.28em] text-steel">
          Verdict Panel
        </p>
        <div className="mt-5 space-y-3">
          <div className="h-6 w-40 animate-pulse rounded-full bg-slate-200" />
          <div className="h-24 animate-pulse rounded-3xl bg-slate-100" />
        </div>
      </section>
    );
  }

  if (error) {
    return (
      <section className="rounded-[28px] border border-rose-200 bg-rose-50 p-6 shadow-glow">
        <p className="text-xs font-semibold uppercase tracking-[0.28em] text-rose-600">
          Verdict Panel
        </p>
        <h2 className="mt-3 text-xl font-bold text-rose-800">Analysis failed</h2>
        <p className="mt-2 text-sm leading-6 text-rose-700">{error}</p>
      </section>
    );
  }

  if (!response) {
    return (
      <section className="rounded-[28px] border border-dashed border-slate-300 bg-white/65 p-6">
        <p className="text-xs font-semibold uppercase tracking-[0.28em] text-steel">
          Verdict Panel
        </p>
        <h2 className="mt-3 text-xl font-bold text-ink">Awaiting first analysis</h2>
        <p className="mt-2 text-sm leading-6 text-slate-600">
          Submit a payload or load one of the samples to inspect the normalized threat verdict.
        </p>
      </section>
    );
  }

  const { verdict, alerts_sent: alertsSent } = response;
  const isThreat = verdict.is_threat;
  const lowSignalsMatched = Boolean(heuristicSignals?.lowSignals?.length);
  const highSignalsToShow =
    heuristicSignals && !lowSignalsMatched ? heuristicSignals.highSignals : [];
  const highlightTerms = lowSignalsMatched
    ? heuristicSignals?.lowSignals ?? []
    : highSignalsToShow.map((s) => s.pattern);

  return (
    <section
      className={`rounded-[28px] border p-6 shadow-glow transition ${
        isThreat
          ? "border-rose-200 bg-gradient-to-br from-white to-rose-50"
          : "border-emerald-200 bg-gradient-to-br from-white to-emerald-50"
      }`}
    >
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p
            className={`text-xs font-semibold uppercase tracking-[0.28em] ${
              isThreat ? "text-rose-600" : "text-emerald-700"
            }`}
          >
            Verdict Panel
          </p>
          <h2 className="mt-3 text-2xl font-bold text-ink">
            {isThreat ? "Threat detected" : "No threat detected"}
          </h2>
        </div>
        <SeverityBadge severity={verdict.severity} />
      </div>

      <div className="mt-6 grid gap-4 sm:grid-cols-2">
        <div className="rounded-3xl bg-white/80 p-4 ring-1 ring-slate-200">
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-steel">
            Threat type
          </p>
          <p className="mt-2 text-lg font-semibold text-ink">{verdict.threat_type}</p>
        </div>
        <div className="rounded-3xl bg-white/80 p-4 ring-1 ring-slate-200">
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-steel">
            Alert status
          </p>
          <p className="mt-2 text-lg font-semibold text-ink">
            {alertsSent.length > 0 ? `${alertsSent.length} alert sent` : "No alerts sent"}
          </p>
        </div>
      </div>

      <div className="mt-4 rounded-3xl bg-ink p-5 text-mist">
        <p className="text-xs font-semibold uppercase tracking-[0.22em] text-sky-200">
          Summary
        </p>
        <p className="mt-3 text-sm leading-7">{verdict.summary}</p>
      </div>

      {heuristicSignals ? (
        <div className="mt-4 rounded-3xl bg-white/80 p-5 ring-1 ring-slate-200">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-600">
                Matched signals (heuristic)
              </p>
              <p className="mt-1 text-xs text-slate-500">
                Local keyword triage; Bedrock can override the final verdict.
              </p>
            </div>
            {highSignalsToShow.length > 0 ? (
              <div className="text-xs text-slate-600">
                {highSignalsToShow.length} high indicator
                {highSignalsToShow.length > 1 ? "s" : ""}
              </div>
            ) : null}
          </div>

          {lowSignalsMatched ? (
            <div className="mt-4 rounded-3xl bg-amber-50 p-4 ring-1 ring-amber-200">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-amber-800">
                Low-signal terms matched
              </p>
              <div className="mt-3 flex flex-wrap gap-2">
                {heuristicSignals.lowSignals.map((term) => (
                  <span
                    key={term}
                    className="rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold text-amber-900"
                  >
                    {term}
                  </span>
                ))}
              </div>

              {heuristicSignals.highSignals.length > 0 ? (
                <p className="mt-3 text-xs text-amber-900">
                  High indicators are ignored by the low-signal filter (matches backend
                  behavior).
                </p>
              ) : null}
            </div>
          ) : null}

          {highSignalsToShow.length > 0 ? (
            <div className="mt-4">
              <div className="flex flex-wrap gap-3">
                {highSignalsToShow.map((signal) => (
                  <div
                    key={signal.pattern}
                    className="rounded-3xl bg-slate-50 p-4 ring-1 ring-slate-200"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <p className="text-sm font-semibold text-ink">
                        {signal.threat_type}
                      </p>
                      <SeverityBadge severity={signal.severity} />
                    </div>
                    <p className="mt-2 text-xs font-mono text-slate-600">
                      pattern: {signal.pattern}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          ) : lowSignalsMatched ? null : (
            <div className="mt-4 rounded-3xl border border-dashed border-slate-300 bg-slate-50 p-5 text-sm text-slate-600">
              No heuristic indicators matched.
            </div>
          )}

          {inputText ? (
            <details className="mt-4 rounded-3xl bg-slate-950 p-4">
              <summary className="cursor-pointer text-xs font-semibold uppercase tracking-[0.18em] text-sky-200">
                Highlighted input (heuristic)
              </summary>
              {renderHighlightedInputSnippets(
                inputText,
                highlightTerms,
                lowSignalsMatched
                  ? "rounded-sm bg-amber-200 text-amber-950 px-0.5"
                  : "rounded-sm bg-rose-200 text-rose-950 px-0.5",
                {
                  contextChars: 80,
                  maxSnippets: 4,
                  maxSnippetChars: 180,
                },
              )}
            </details>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}
