import type { Severity } from "../types/threat";

const severityStyles: Record<Severity, string> = {
  LOW: "bg-slate-200 text-slate-700 ring-slate-300",
  MEDIUM: "bg-amber-100 text-amber-800 ring-amber-300",
  HIGH: "bg-orange-100 text-orange-800 ring-orange-300",
  CRITICAL: "bg-rose-100 text-rose-800 ring-rose-300",
};

interface SeverityBadgeProps {
  severity: Severity;
}

export function SeverityBadge({ severity }: SeverityBadgeProps) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-bold tracking-[0.24em] ring-1 ${severityStyles[severity]}`}
    >
      {severity}
    </span>
  );
}
