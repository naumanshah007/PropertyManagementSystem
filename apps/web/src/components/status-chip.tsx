import clsx from "clsx";
import type { JobStatus, ReviewStatus } from "@/lib/types";

const jobStatusClasses: Record<JobStatus, string> = {
  uploaded: "border-slate-400/30 bg-slate-400/10 text-slate-200",
  processing: "border-sky-300/30 bg-sky-400/10 text-sky-200",
  priced: "border-cyan-300/30 bg-cyan-400/10 text-cyan-200",
  in_review: "border-amber-300/30 bg-amber-400/10 text-amber-200",
  approved: "border-emerald-300/40 bg-emerald-400/15 text-emerald-100",
  exported: "border-violet-300/40 bg-violet-400/15 text-violet-100",
  rejected: "border-rose-300/30 bg-rose-400/10 text-rose-200",
};

const jobStatusLabels: Record<JobStatus, string> = {
  uploaded: "Uploaded",
  processing: "Processing",
  priced: "Priced",
  in_review: "In review",
  approved: "Approved",
  exported: "Exported",
  rejected: "Rejected",
};

export function JobStatusChip({ status }: { status: JobStatus }) {
  return (
    <span
      className={clsx(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-semibold backdrop-blur",
        jobStatusClasses[status],
      )}
    >
      <span className="h-1.5 w-1.5 rounded-full bg-current shadow-[0_0_8px_currentColor]" />
      {jobStatusLabels[status]}
    </span>
  );
}

const statusClasses: Record<ReviewStatus, string> = {
  ai_draft: "border-slate-400/30 bg-slate-400/10 text-slate-200",
  review_required: "border-amber-300/30 bg-amber-400/10 text-amber-200",
  accepted: "border-emerald-300/30 bg-emerald-400/10 text-emerald-200",
  edited: "border-sky-300/30 bg-sky-400/10 text-sky-200",
  approved: "border-emerald-300/40 bg-emerald-400/15 text-emerald-100",
  blocked: "border-rose-300/30 bg-rose-400/10 text-rose-200",
};

const labelMap: Record<ReviewStatus, string> = {
  ai_draft: "AI draft",
  review_required: "Review required",
  accepted: "Accepted",
  edited: "Edited",
  approved: "Approved",
  blocked: "Blocked",
};

export function StatusChip({ status }: { status: ReviewStatus }) {
  return (
    <span
      className={clsx(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-semibold backdrop-blur",
        statusClasses[status],
      )}
    >
      <span className="h-1.5 w-1.5 rounded-full bg-current shadow-[0_0_8px_currentColor]" />
      {labelMap[status]}
    </span>
  );
}

export function RiskChip({ label }: { label: string }) {
  const key = label.toLowerCase();
  let className = "border-slate-400/30 bg-slate-400/10 text-slate-200";

  if (key.includes("class a")) {
    className = "border-rose-300/40 bg-rose-400/15 text-rose-100";
  } else if (key.includes("class b")) {
    className = "border-emerald-300/40 bg-emerald-400/15 text-emerald-100";
  } else if (key.includes("no access")) {
    className = "border-amber-300/40 bg-amber-400/15 text-amber-100";
  } else if (key.includes("limited")) {
    className = "border-orange-300/40 bg-orange-400/15 text-orange-100";
  } else if (key.includes("presumed")) {
    className = "border-violet-300/40 bg-violet-400/15 text-violet-100";
  } else if (key.includes("positive")) {
    className = "border-sky-300/40 bg-sky-400/15 text-sky-100";
  } else if (key.includes("source-ready") || key === "parsed") {
    className = "border-emerald-300/40 bg-emerald-400/15 text-emerald-100";
  } else if (key.includes("warning") || key.includes("not ready")) {
    className = "border-amber-300/40 bg-amber-400/15 text-amber-100";
  } else if (key === "nad" || key.includes("not detected")) {
    className = "border-white/10 bg-white/5 text-slate-300";
  } else if (key.includes("poa")) {
    className = "border-fuchsia-300/40 bg-fuchsia-400/15 text-fuchsia-100";
  } else if (key.includes("exported") || key.includes("approved")) {
    className = "border-emerald-300/40 bg-emerald-400/15 text-emerald-100";
  }

  return (
    <span
      className={clsx(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-semibold backdrop-blur",
        className,
      )}
    >
      <span className="h-1.5 w-1.5 rounded-full bg-current shadow-[0_0_8px_currentColor]" />
      {label}
    </span>
  );
}

export function EvidenceChip({ page, label }: { page: number; label?: string }) {
  return (
    <span className="inline-flex items-center rounded-md border border-cyan-300/30 bg-cyan-400/10 px-2 py-1 text-xs font-semibold text-cyan-200 backdrop-blur">
      Source p.{page}
      {label ? ` · ${label}` : ""}
    </span>
  );
}
