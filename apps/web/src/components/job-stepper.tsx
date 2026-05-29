import clsx from "clsx";
import { Check, Loader2 } from "lucide-react";
import type { JobStatus } from "@/lib/types";

const STEPS = ["Upload", "Process", "Review", "Approve", "Export"] as const;

// How far through the 5-step flow each status sits (index of the *current* step).
const CURRENT_INDEX: Record<JobStatus, number> = {
  uploaded: 1,
  processing: 1,
  priced: 2,
  in_review: 2,
  approved: 4,
  exported: 5,
  rejected: 1,
};

export function JobStepper({ status }: { status: JobStatus }) {
  const current = CURRENT_INDEX[status];
  const isRejected = status === "rejected";
  const isProcessing = status === "processing";

  return (
    <div className="grid gap-3 md:grid-cols-5">
      {STEPS.map((step, index) => {
        const done = index < current && !isRejected;
        const isCurrent = index === current && !isRejected;
        const failed = isRejected && index === 1;

        return (
          <div
            key={step}
            className={clsx(
              "relative overflow-hidden rounded-xl border px-3 py-3 transition",
              failed
                ? "border-rose-300/40 bg-rose-400/10 text-rose-100"
                : isCurrent
                  ? "border-amber-300/40 bg-amber-400/10 text-amber-100 shadow-[0_0_24px_-8px_rgba(251,191,36,0.6)]"
                  : done
                    ? "border-cyan-300/40 bg-cyan-400/10 text-cyan-100 shadow-[0_0_24px_-10px_rgba(34,211,238,0.6)]"
                    : "border-white/10 bg-white/[0.03] text-graphite",
            )}
          >
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-semibold uppercase tracking-[0.16em] opacity-80">
                Step {index + 1}
              </span>
              <span
                className={clsx(
                  "grid h-5 w-5 place-items-center rounded-full text-[10px] font-bold",
                  failed
                    ? "bg-rose-300 text-night-900"
                    : isCurrent
                      ? "bg-amber-300 text-night-900"
                      : done
                        ? "bg-grad-primary text-night-900"
                        : "border border-white/15 bg-white/5 text-graphite",
                )}
              >
                {done ? (
                  <Check className="h-3 w-3" />
                ) : isCurrent && isProcessing ? (
                  <Loader2 className="h-3 w-3 animate-spin" />
                ) : (
                  index + 1
                )}
              </span>
            </div>
            <div className="mt-1.5 text-sm font-semibold">{step}</div>
          </div>
        );
      })}
    </div>
  );
}
