import clsx from "clsx";
import { Check } from "lucide-react";

const steps = ["Intake", "Extraction", "Evidence Review", "Quote Draft", "Approval", "Export"];

export function WorkflowTimeline({ active = 4 }: { active?: number }) {
  return (
    <div className="grid gap-3 md:grid-cols-6">
      {steps.map((step, index) => {
        const isDone = index < active;
        const isActive = index === active;
        return (
          <div
            key={step}
            className={clsx(
              "relative overflow-hidden rounded-xl border px-3 py-3 transition",
              isActive
                ? "border-amber-300/40 bg-amber-400/10 text-amber-100 shadow-[0_0_24px_-8px_rgba(251,191,36,0.6)]"
                : isDone
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
                  isActive
                    ? "bg-amber-300 text-night-900"
                    : isDone
                      ? "bg-grad-primary text-night-900"
                      : "border border-white/15 bg-white/5 text-graphite",
                )}
              >
                {isDone ? <Check className="h-3 w-3" /> : index + 1}
              </span>
            </div>
            <div className="mt-1.5 text-sm font-semibold">{step}</div>
          </div>
        );
      })}
    </div>
  );
}
