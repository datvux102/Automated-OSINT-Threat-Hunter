interface CopyButtonProps {
  onCopy: () => void | Promise<void>;
  label: string;
  className?: string;
}

export function CopyButton({ onCopy, label, className }: CopyButtonProps) {
  return (
    <button
      type="button"
      onClick={onCopy}
      className={`rounded-2xl border border-slate-200 bg-white px-4 py-2 text-xs font-semibold text-slate-700 transition hover:bg-slate-50 ${className ?? ""}`}
    >
      {label}
    </button>
  );
}
