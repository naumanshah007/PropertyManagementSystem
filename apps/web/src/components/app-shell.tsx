import { Sparkles } from "lucide-react";
import Link from "next/link";
import type { ReactNode } from "react";
import { DemoAuthBar } from "./demo-auth-bar";
import { SidebarNav } from "./sidebar-nav";

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="relative min-h-screen bg-night-900 text-ink">
      <div
        aria-hidden
        className="pointer-events-none fixed inset-0 -z-10 overflow-hidden"
      >
        <div className="absolute -top-32 left-1/3 h-[420px] w-[820px] -translate-x-1/2 rounded-full bg-cyan-500/10 blur-[140px]" />
        <div className="absolute top-[60%] right-0 h-[360px] w-[560px] rounded-full bg-violet-500/10 blur-[140px]" />
        <div className="absolute inset-0 surface-grid [mask-image:radial-gradient(ellipse_at_center,black_30%,transparent_75%)]" />
      </div>

      <aside className="fixed inset-y-0 left-0 hidden w-72 border-r border-white/5 bg-night-900/80 backdrop-blur-xl lg:block">
        <div className="border-b border-white/5 px-6 py-6">
          <Link href="/" className="flex items-center gap-2.5">
            <span className="grid h-9 w-9 place-items-center rounded-lg bg-grad-primary shadow-glow">
              <Sparkles className="h-4 w-4 text-night-900" />
            </span>
            <div>
              <div className="text-base font-semibold tracking-tight text-ink">TraceQuote AI</div>
              <div className="text-[11px] uppercase tracking-[0.16em] text-graphite">Survey → Quote</div>
            </div>
          </Link>
          <div className="mt-4 inline-flex items-center gap-2 rounded-full border border-emerald-300/30 bg-emerald-400/10 px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.16em] text-emerald-200">
            <span className="h-1 w-1 rounded-full bg-emerald-300 shadow-[0_0_8px_rgba(110,231,183,0.9)]" />
            Human-approved exports
          </div>
        </div>
        <SidebarNav />
        <div className="absolute bottom-0 left-0 right-0 border-t border-white/5 p-5">
          <div className="rounded-xl border border-white/10 bg-white/[0.04] p-4 text-xs leading-5 text-graphite backdrop-blur">
            AI prepares drafts. Estimators approve final quote packages.
          </div>
        </div>
      </aside>

      <div className="lg:pl-72">
        <header className="sticky top-0 z-20 border-b border-white/5 bg-night-900/70 px-5 py-4 backdrop-blur-xl lg:px-8">
          <div className="flex items-center justify-between gap-4">
            <div>
              <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-cyan-300">
                Enterprise workspace
              </div>
              <div className="mt-1 text-sm text-graphite">Evidence-linked draft quote workflow</div>
            </div>
            <div className="flex items-center gap-2">
              <Link
                href="/jobs/new"
                className="hidden rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm font-semibold text-ink backdrop-blur transition hover:bg-white/10 md:inline-flex"
              >
                New job
              </Link>
              <DemoAuthBar />
            </div>
          </div>
        </header>
        <main className="px-5 py-8 lg:px-10">{children}</main>
      </div>
    </div>
  );
}
