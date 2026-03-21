const escapeRegExp = (value: string): string =>
  value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

import type { ReactNode } from "react";

function renderHighlightedInRawText(
  rawText: string,
  regex: RegExp,
  highlightClassName: string,
): ReactNode[] {
  const nodes: ReactNode[] = [];
  let lastIndex = 0;
  let idx = 0;

  for (const match of rawText.matchAll(regex)) {
    const startIndex = match.index ?? 0;
    const matchedText = match[0] ?? "";

    if (startIndex > lastIndex) {
      nodes.push(rawText.slice(lastIndex, startIndex));
    }

    nodes.push(
      <mark key={`h-${idx++}`} className={highlightClassName}>
        {matchedText}
      </mark>,
    );

    lastIndex = startIndex + matchedText.length;
  }

  if (lastIndex < rawText.length) {
    nodes.push(rawText.slice(lastIndex));
  }

  return nodes;
}

export function renderHighlightedText(
  rawText: string,
  terms: string[],
  highlightClassName: string,
): ReactNode {
  const cleaned = terms.map((t) => t.trim()).filter(Boolean);
  const unique = Array.from(new Set(cleaned));
  if (unique.length === 0) return rawText;

  unique.sort((a, b) => b.length - a.length);
  const regex = new RegExp(unique.map(escapeRegExp).join("|"), "gi");

  return renderHighlightedInRawText(rawText, regex, highlightClassName);
}

export type HighlightSnippetOptions = {
  contextChars?: number;
  maxSnippets?: number;
  maxSnippetChars?: number;
};

export function renderHighlightedInputSnippets(
  rawText: string,
  terms: string[],
  highlightClassName: string,
  options?: HighlightSnippetOptions,
): ReactNode {
  const cleaned = terms.map((t) => t.trim()).filter(Boolean);
  const unique = Array.from(new Set(cleaned));
  if (unique.length === 0) return rawText;

  unique.sort((a, b) => b.length - a.length);
  const regex = new RegExp(unique.map(escapeRegExp).join("|"), "gi");

  const contextChars = options?.contextChars ?? 80;
  const maxSnippets = options?.maxSnippets ?? 4;
  const maxSnippetChars = options?.maxSnippetChars ?? 180;

  const snippets: { start: number; end: number }[] = [];
  let matchesSeen = 0;

  for (const match of rawText.matchAll(regex)) {
    const matchIndex = match.index ?? 0;
    const matchText = match[0] ?? "";
    const matchLen = matchText.length || 1;

    matchesSeen += 1;

    const approxStart = Math.max(0, matchIndex - contextChars);
    const approxEnd = Math.min(rawText.length, matchIndex + matchLen + contextChars);

    // If snippet overlaps previous snippet, skip to keep output compact.
    const last = snippets[snippets.length - 1];
    if (last && approxStart <= last.end) continue;

    // Center + clamp to maxSnippetChars
    const half = Math.floor(maxSnippetChars / 2);
    const centerStart = Math.max(0, Math.min(matchIndex - half, rawText.length - maxSnippetChars));
    const start = centerStart;
    const end = Math.min(rawText.length, start + maxSnippetChars);

    snippets.push({ start, end });
    if (snippets.length >= maxSnippets) break;
  }

  if (snippets.length === 0) return rawText.slice(0, 220);

  return (
    <div className="mt-3 space-y-3">
      {snippets.map((s, i) => {
        const snippetRaw = rawText.slice(s.start, s.end);
        return (
          <div
            key={`${s.start}-${s.end}-${i}`}
            className="rounded-3xl bg-slate-900/30 p-3 ring-1 ring-slate-200"
          >
            <pre className="whitespace-pre-wrap break-words text-xs leading-5 text-slate-100">
              {renderHighlightedInRawText(snippetRaw, regex, highlightClassName)}
            </pre>
          </div>
        );
      })}
      {matchesSeen > snippets.length ? (
        <p className="text-xs text-slate-500">
          Showing {snippets.length} of {matchesSeen} heuristic matches.
        </p>
      ) : null}
    </div>
  );
}

