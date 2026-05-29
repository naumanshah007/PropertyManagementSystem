import type { ReactNode } from "react";
import { FileSearch, LockKeyhole, ShieldCheck } from "lucide-react";
import type { QuoteWorkup } from "@/lib/types";
import { StatusChip } from "./status-chip";

export function TraceabilityBanner({ workup }: { workup: QuoteWorkup }) {
  const evidenceCount = workup.source_evidence.length;
  const reviewRequired = workup.register_items.filter((item) => item.review_status === "review_required").length;
  const quoteLines = workup.quote_lines.length;

  return (
    <section className="rounded-lg border border-moss/30 bg-[#eef4ee] p-5 shadow-panel">
      <div className="grid gap-4 lg:grid-cols-[1fr_auto] lg:items-center">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <span className="inline-flex items-center gap-2 rounded-full border border-moss/30 bg-white px-3 py-1 text-xs font-semibold uppercase tracking-wide text-moss">
              <ShieldCheck className="h-3.5 w-3.5" />
              Governed draft
            </span>
            <StatusChip status={workup.export_status === "blocked" ? "blocked" : "accepted"} />
          </div>
          <h2 className="mt-3 text-xl font-semibold tracking-tight text-ink">
            Every quote line stays linked to source evidence, pricing logic, and human review.
          </h2>
          <p className="mt-2 text-sm leading-6 text-graphite">
            Deterministic Phase 1 demo: no ML extraction, no final quote approval, and no export until review-required findings are resolved.
          </p>
        </div>
        <div className="grid min-w-80 gap-2 sm:grid-cols-3">
          <TraceStat label="Evidence" value={String(evidenceCount)} icon={<FileSearch className="h-4 w-4" />} />
          <TraceStat label="Draft lines" value={String(quoteLines)} icon={<ShieldCheck className="h-4 w-4" />} />
          <TraceStat label="Review gates" value={String(reviewRequired)} icon={<LockKeyhole className="h-4 w-4" />} />
        </div>
      </div>
    </section>
  );
}

function TraceStat({ label, value, icon }: { label: string; value: string; icon: ReactNode }) {
  return (
    <div className="rounded-md border border-white bg-white/80 p-3">
      <div className="flex items-center justify-between text-moss">
        <span className="text-xs font-semibold uppercase tracking-wide">{label}</span>
        {icon}
      </div>
      <div className="mt-2 text-2xl font-semibold text-ink">{value}</div>
    </div>
  );
}

