interface JsonInspectorProps {
  payload: unknown;
}

export function JsonInspector({ payload }: JsonInspectorProps) {
  return (
    <section className="rounded-[28px] border border-slate-200 bg-white/80 p-6 shadow-glow">
      <p className="text-xs font-semibold uppercase tracking-[0.28em] text-steel">
        Raw JSON Inspector
      </p>
      <details className="mt-4 rounded-3xl bg-slate-950 p-5 text-slate-100">
        <summary className="cursor-pointer text-sm font-semibold text-sky-200">
          Toggle backend response
        </summary>
        <pre className="mt-4 overflow-x-auto whitespace-pre-wrap text-xs leading-6 text-slate-300">
          {payload ? JSON.stringify(payload, null, 2) : "No response yet."}
        </pre>
      </details>
    </section>
  );
}
