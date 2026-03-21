interface SystemStatusCardProps {
  label: string;
  value: boolean;
  description: string;
}

export function SystemStatusCard({ label, value, description }: SystemStatusCardProps) {
  return (
    <article className="rounded-[28px] border border-slate-200 bg-white/80 p-6 shadow-glow">
      <div className="flex items-center justify-between gap-4">
        <h2 className="text-lg font-bold text-ink">{label}</h2>
        <span
          className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-bold tracking-[0.2em] ring-1 ${
            value
              ? "bg-emerald-100 text-emerald-800 ring-emerald-200"
              : "bg-slate-100 text-slate-600 ring-slate-200"
          }`}
        >
          {value ? "ON" : "OFF"}
        </span>
      </div>
      <p className="mt-3 text-sm leading-6 text-slate-600">{description}</p>
    </article>
  );
}
