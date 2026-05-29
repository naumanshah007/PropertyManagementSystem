import { ArrowRight, FileText, ListChecks, LockKeyhole } from "lucide-react";
import type { QuoteWorkup } from "@/lib/types";
import { Panel } from "./panel";
import { RiskChip, StatusChip } from "./status-chip";

export function VendorStory({ workup }: { workup: QuoteWorkup }) {
  return (
    <Panel className="overflow-hidden">
      <div className="grid gap-0 lg:grid-cols-[1fr_auto_1fr]">
        <div className="p-5">
          <div className="flex items-center gap-2 text-sm font-semibold text-graphite">
            <FileText className="h-4 w-4 text-hazard" />
            Before TraceQuote AI
          </div>
          <h2 className="mt-3 text-xl font-semibold tracking-tight text-ink">Manual survey read-through before pricing</h2>
          <p className="mt-2 text-sm leading-6 text-graphite">
            Estimator reads a 50-page asbestos demolition survey, finds register items, checks access warnings, builds quote lines, and manually tracks assumptions.
          </p>
        </div>
        <div className="hidden items-center border-x border-line bg-slate-50 px-5 lg:flex">
          <ArrowRight className="h-5 w-5 text-moss" />
        </div>
        <div className="border-t border-line p-5 lg:border-t-0">
          <div className="flex items-center gap-2 text-sm font-semibold text-moss">
            <ListChecks className="h-4 w-4" />
            Phase 1 demo outcome
          </div>
          <h2 className="mt-3 text-xl font-semibold tracking-tight text-ink">Evidence-linked quote draft with blocked export gate</h2>
          <p className="mt-2 text-sm leading-6 text-graphite">
            {workup.register_items.length} register items and {workup.quote_lines.length} draft lines are visible with source pages, pricing rationale, and review status.
          </p>
          <div className="mt-4 flex flex-wrap gap-2">
            <RiskChip label="Class A" />
            <RiskChip label="No Access" />
            <RiskChip label="Limited Access" />
            <RiskChip label="Presumed" />
            <StatusChip status="blocked" />
          </div>
        </div>
      </div>
      <div className="border-t border-line bg-rose-50 px-5 py-3 text-sm font-medium text-rose-950">
        <span className="inline-flex items-center gap-2">
          <LockKeyhole className="h-4 w-4" />
          No client-facing final quote can be exported until review gates and estimator sign-off are complete.
        </span>
      </div>
    </Panel>
  );
}

