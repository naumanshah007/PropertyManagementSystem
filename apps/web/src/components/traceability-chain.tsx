import { ArrowRight, ClipboardCheck, FileSearch, FileText, ShieldCheck } from "lucide-react";
import type { QuoteWorkup } from "@/lib/types";
import { Panel, PanelHeader } from "./panel";
import { StatusChip } from "./status-chip";

const chain = [
  { label: "Source survey", detail: "50-page asbestos survey retained", icon: FileText },
  { label: "Register evidence", detail: "5 extracted items with page references", icon: FileSearch },
  { label: "Quote logic", detail: "7 draft lines linked to pricing rules", icon: ClipboardCheck },
  { label: "Human gate", detail: "Export blocked until estimator approval", icon: ShieldCheck },
];

export function TraceabilityChain({ workup }: { workup: QuoteWorkup }) {
  return (
    <Panel>
      <PanelHeader
        title="Traceability chain"
        description="Every commercial line stays connected to source evidence and review status."
        right={<StatusChip status={workup.export_status === "blocked" ? "blocked" : "accepted"} />}
      />
      <div className="grid gap-3 p-5 lg:grid-cols-4">
        {chain.map((step, index) => {
          const Icon = step.icon;
          return (
            <div key={step.label} className="relative rounded-md border border-line bg-slate-50 p-4">
              <div className="flex items-start gap-3">
                <div className="rounded-md bg-white p-2 text-moss shadow-sm">
                  <Icon className="h-4 w-4" />
                </div>
                <div>
                  <div className="text-sm font-semibold text-ink">{step.label}</div>
                  <div className="mt-1 text-xs leading-5 text-graphite">{step.detail}</div>
                </div>
              </div>
              {index < chain.length - 1 ? (
                <ArrowRight className="absolute -right-5 top-1/2 hidden h-4 w-4 -translate-y-1/2 text-moss lg:block" />
              ) : null}
            </div>
          );
        })}
      </div>
    </Panel>
  );
}

