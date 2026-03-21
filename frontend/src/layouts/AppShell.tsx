import type { ReactNode } from "react";
import { NavBar } from "../components/NavBar";

interface AppShellProps {
  title: string;
  eyebrow: string;
  description: string;
  children: ReactNode;
}

export function AppShell({ title, eyebrow, description, children }: AppShellProps) {
  return (
    <main className="relative min-h-screen overflow-hidden">
      <div className="absolute inset-0 -z-10 bg-grid bg-[size:40px_40px] opacity-60" />
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <header className="rounded-[32px] border border-white/70 bg-ink px-6 py-8 text-white shadow-glow">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
            <div className="max-w-3xl">
              <p className="text-xs font-semibold uppercase tracking-[0.32em] text-sky-200">
                {eyebrow}
              </p>
              <h1 className="mt-3 text-4xl font-bold sm:text-5xl">{title}</h1>
              <p className="mt-4 max-w-2xl text-sm leading-7 text-slate-300 sm:text-base">
                {description}
              </p>
            </div>
            <NavBar />
          </div>
        </header>

        <div className="mt-6">{children}</div>
      </div>
    </main>
  );
}
