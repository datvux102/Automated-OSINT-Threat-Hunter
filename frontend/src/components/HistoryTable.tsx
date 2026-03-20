import type { HistoryItem } from "../types/threat";

interface HistoryTableProps {
  items: HistoryItem[];
}

export function HistoryTable({ items }: HistoryTableProps) {
  return (
    <section className="rounded-[28px] border border-slate-200 bg-white/80 p-6 shadow-glow">
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.28em] text-steel">
            Session History
          </p>
          <h2 className="mt-2 text-2xl font-bold text-ink">Recent analyses</h2>
        </div>
        <div className="rounded-full bg-sky-50 px-3 py-1 text-xs font-semibold text-sky-700">
          In-memory only
        </div>
      </div>

      {items.length === 0 ? (
        <div className="mt-6 rounded-3xl border border-dashed border-slate-300 bg-slate-50 p-5 text-sm text-slate-600">
          Successful analyses will appear here during this session.
        </div>
      ) : (
        <div className="mt-6 overflow-hidden rounded-3xl border border-slate-200">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
              <thead className="bg-slate-50 text-slate-600">
                <tr>
                  <th className="px-4 py-3 font-semibold">Time</th>
                  <th className="px-4 py-3 font-semibold">Source</th>
                  <th className="px-4 py-3 font-semibold">Query</th>
                  <th className="px-4 py-3 font-semibold">Severity</th>
                  <th className="px-4 py-3 font-semibold">Threat type</th>
                  <th className="px-4 py-3 font-semibold">Alerts</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 bg-white">
                {items.map((item) => (
                  <tr key={item.id} className="text-slate-700">
                    <td className="px-4 py-3">{item.time}</td>
                    <td className="px-4 py-3">{item.input.source}</td>
                    <td className="px-4 py-3">{item.input.query || "n/a"}</td>
                    <td className="px-4 py-3 font-semibold">{item.verdict.severity}</td>
                    <td className="px-4 py-3">{item.verdict.threat_type}</td>
                    <td className="px-4 py-3">{item.alertCount}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </section>
  );
}
