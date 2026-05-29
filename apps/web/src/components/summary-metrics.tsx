import { FileWarning, ListChecks, LockKeyhole, ShieldAlert } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import type { QuoteWorkup } from "@/lib/types";

type Accent = "cyan" | "violet" | "amber" | "rose";

const ACCENT: Record<Accent, { ring: string; chip: string; glow: string; icon: string }> = {
  cyan: {
    ring: "from-cyan-400/30 to-transparent",
    chip: "bg-cyan-400/10 text-cyan-200 border-cyan-300/30",
    glow: "shadow-[0_0_40px_-12px_rgba(34,211,238,0.6)]",
    icon: "text-cyan-300",
  },
  violet: {
    ring: "from-violet-400/30 to-transparent",
    chip: "bg-violet-400/10 text-violet-200 border-violet-300/30",
    glow: "shadow-[0_0_40px_-12px_rgba(167,139,250,0.6)]",
    icon: "text-violet-300",
  },
  amber: {
    ring: "from-amber-400/30 to-transparent",
    chip: "bg-amber-400/10 text-amber-200 border-amber-300/30",
    glow: "shadow-[0_0_40px_-12px_rgba(251,191,36,0.55)]",
    icon: "text-amber-300",
  },
  rose: {
    ring: "from-rose-400/30 to-transparent",
    chip: "bg-rose-400/10 text-rose-200 border-rose-300/30",
    glow: "shadow-[0_0_40px_-12px_rgba(251,113,133,0.55)]",
    icon: "text-rose-300",
  },
};

export function MetricCard({
  label,
  value,
  detail,
  icon: Icon,
  accent = "cyan",
}: {
  label: string;
  value: string;
  detail?: string;
  icon: LucideIcon;
  accent?: Accent;
}) {
  const a = ACCENT[accent];
  return (
    <div
      className={`group relative overflow-hidden rounded-2xl border border-white/10 bg-night-800/70 p-5 backdrop-blur-md transition hover:border-white/20 ${a.glow}`}
    >
      <div
        className={`pointer-events-none absolute -right-12 -top-12 h-36 w-36 rounded-full bg-gradient-to-br ${a.ring} blur-2xl`}
      />
      <div className="relative flex items-start justify-between gap-4">
        <div>
          <div className="text-[11px] font-semibold uppercase tracking-[0.16em] text-graphite">{label}</div>
          <div className="mt-2 text-2xl font-semibold text-ink">{value}</div>
          {detail ? (
            <span
              className={`mt-2 inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide backdrop-blur ${a.chip}`}
            >
              {detail}
            </span>
          ) : null}
        </div>
        <div
          className={`grid h-10 w-10 place-items-center rounded-lg border border-white/10 bg-white/[0.04] ${a.icon}`}
        >
          <Icon className="h-5 w-5" />
        </div>
      </div>
    </div>
  );
}

export function SummaryMetrics({ workup }: { workup: QuoteWorkup }) {
  const reviewRequired = workup.register_items.filter((item) => item.review_status === "review_required").length;
  const totalQuote = workup.quote_lines.reduce((sum, line) => sum + (line.total ?? 0), 0);

  const metrics: Array<{
    label: string;
    value: string;
    detail: string;
    icon: LucideIcon;
    accent: Accent;
  }> = [
    {
      label: "Draft quote value",
      value: `$${Math.round(totalQuote).toLocaleString("en-NZ")}`,
      detail: "Not approved",
      icon: ListChecks,
      accent: "cyan",
    },
    {
      label: "Evidence-linked items",
      value: String(workup.register_items.length),
      detail: "Source pages linked",
      icon: FileWarning,
      accent: "violet",
    },
    {
      label: "Review required",
      value: String(reviewRequired),
      detail: "Class A / access risk",
      icon: ShieldAlert,
      accent: "amber",
    },
    {
      label: "Export status",
      value: "Blocked",
      detail: "Human gate open",
      icon: LockKeyhole,
      accent: "rose",
    },
  ];

  return (
    <div className="grid gap-4 md:grid-cols-4">
      {metrics.map((m) => (
        <MetricCard
          key={m.label}
          label={m.label}
          value={m.value}
          detail={m.detail}
          icon={m.icon}
          accent={m.accent}
        />
      ))}
    </div>
  );
}
