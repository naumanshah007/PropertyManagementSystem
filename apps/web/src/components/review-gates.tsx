import { Ban, CheckCircle2, ShieldAlert } from "lucide-react";
import type { QuoteWorkup } from "@/lib/types";
import { Panel, PanelHeader } from "./panel";
import { StatusChip } from "./status-chip";

export const reviewGates = [
  {
    label: "No-access items reviewed",
    description: "Power box and power board box remain provisional until access is confirmed.",
    done: false,
  },
  {
    label: "Class A/friable item confirmed",
    description: "Chimney AIB requires specialist estimator review before final pricing.",
    done: false,
  },
  {
    label: "Presumed asbestos accepted as provisional",
    description: "Presumed items must not be presented as confirmed final scope.",
    done: false,
  },
  {
    label: "Assumptions and exclusions checked",
    description: "Commercial conditions are visible in the quote package.",
    done: true,
  },
  {
    label: "Estimator sign-off completed",
    description: "Human approval is required before final export.",
    done: false,
  },
];

export function ReviewGates({ workup }: { workup: QuoteWorkup }) {
  const openCount = reviewGates.filter((gate) => !gate.done).length;

  return (
    <Panel>
      <PanelHeader
        title="Review gates"
        description={`${openCount} gates block export for ${workup.client_name}.`}
        right={<StatusChip status="blocked" />}
      />
      <div className="divide-y divide-line">
        {reviewGates.map((gate) => (
          <div key={gate.label} className="flex gap-3 px-5 py-4">
            {gate.done ? (
              <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-verified" />
            ) : (
              <Ban className="mt-0.5 h-5 w-5 shrink-0 text-blocked" />
            )}
            <div className="min-w-0 flex-1">
              <div className="flex flex-wrap items-center gap-2">
                <div className="font-semibold text-ink">{gate.label}</div>
                <StatusChip status={gate.done ? "accepted" : "blocked"} />
              </div>
              <p className="mt-1 text-sm leading-5 text-graphite">{gate.description}</p>
            </div>
          </div>
        ))}
      </div>
      <div className="border-t border-line bg-rose-50/60 px-5 py-4">
        <div className="flex gap-3 text-sm text-rose-900">
          <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0" />
          <span>Export remains disabled because this is an AI draft without completed estimator approval.</span>
        </div>
      </div>
    </Panel>
  );
}
