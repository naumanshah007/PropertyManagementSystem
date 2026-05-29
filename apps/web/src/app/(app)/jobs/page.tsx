"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowRight, FileText, Loader2, Plus, FolderOpen } from "lucide-react";
import { AccessDenied } from "@/components/access-denied";
import { PageHeader } from "@/components/page-header";
import { Panel } from "@/components/panel";
import { JobStatusChip } from "@/components/status-chip";
import { ApiError, listJobs } from "@/lib/api";
import { formatCurrency } from "@/lib/format";
import { useActiveOrg } from "@/lib/use-active-org";
import type { JobSummary } from "@/lib/types";

export default function JobsPage() {
  const { orgId, ready } = useActiveOrg();
  const [jobs, setJobs] = useState<JobSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [forbidden, setForbidden] = useState(false);

  useEffect(() => {
    if (!ready) return;
    let cancelled = false;
    listJobs(orgId)
      .then((rows) => !cancelled && setJobs(rows))
      .catch((e) => {
        if (cancelled) return;
        if (e instanceof ApiError && e.status === 403) {
          setForbidden(true);
        } else {
          setError(e instanceof Error ? e.message : "Failed to load jobs");
        }
      });
    return () => {
      cancelled = true;
    };
  }, [orgId, ready]);

  if (forbidden) {
    return <AccessDenied message="You don't have access to this organisation's jobs." />;
  }

  return (
    <div>
      <PageHeader
        eyebrow="Jobs"
        title="Quote jobs"
        description="Every uploaded survey becomes a job you can process, review, approve, and export — all in one place."
        actions={
          <Link href="/jobs/new" className="btn-primary">
            <Plus className="h-4 w-4" />
            New job
          </Link>
        }
      />

      {error ? (
        <Panel className="p-5 text-sm text-rose-200">{error}</Panel>
      ) : !jobs ? (
        <Panel className="flex items-center gap-3 p-6 text-sm text-graphite">
          <Loader2 className="h-4 w-4 animate-spin text-cyan-300" />
          Loading jobs…
        </Panel>
      ) : jobs.length === 0 ? (
        <EmptyState />
      ) : (
        <Panel className="overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-white/10 text-sm">
              <thead className="bg-white/[0.04] text-left text-[11px] font-semibold uppercase tracking-[0.12em] text-graphite">
                <tr>
                  <th className="px-5 py-3">Job</th>
                  <th className="px-5 py-3">Survey type</th>
                  <th className="px-5 py-3">Status</th>
                  <th className="px-5 py-3">Quote total</th>
                  <th className="px-5 py-3">Created</th>
                  <th className="px-5 py-3" />
                </tr>
              </thead>
              <tbody className="divide-y divide-white/[0.06]">
                {jobs.map((job) => (
                  <tr key={job.id} className="transition-colors hover:bg-white/[0.02]">
                    <td className="px-5 py-4">
                      <div className="flex items-start gap-3">
                        <FileText className="mt-0.5 h-4 w-4 shrink-0 text-cyan-300" />
                        <div>
                          <div className="font-semibold text-ink">{job.client_name || job.file_name}</div>
                          <div className="mt-0.5 text-xs text-graphite">{job.site_address || job.file_name}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-5 py-4 text-graphite">{formatSurveyType(job.survey_type)}</td>
                    <td className="px-5 py-4">
                      <JobStatusChip status={job.status} />
                    </td>
                    <td className="px-5 py-4 font-semibold text-ink">
                      {job.total_inc_gst != null ? formatCurrency(job.total_inc_gst) : "—"}
                    </td>
                    <td className="px-5 py-4 text-xs text-graphite">
                      {new Date(job.created_at).toLocaleDateString("en-NZ")}
                    </td>
                    <td className="px-5 py-4 text-right">
                      <Link
                        href={`/jobs/${job.id}`}
                        className="inline-flex items-center gap-1.5 text-sm font-semibold text-cyan-300 hover:text-cyan-200"
                      >
                        Open <ArrowRight className="h-4 w-4" />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>
      )}
    </div>
  );
}

function EmptyState() {
  return (
    <Panel className="flex flex-col items-center justify-center px-6 py-16 text-center">
      <div className="grid h-14 w-14 place-items-center rounded-2xl border border-white/10 bg-white/[0.04] text-cyan-300">
        <FolderOpen className="h-7 w-7" />
      </div>
      <h2 className="mt-5 text-lg font-semibold text-ink">No jobs yet</h2>
      <p className="mt-2 max-w-sm text-sm leading-6 text-graphite">
        Upload an asbestos survey to create your first job. We&apos;ll classify it, extract the register, and price a
        draft quote in one pass.
      </p>
      <Link href="/jobs/new" className="btn-primary mt-6">
        <Plus className="h-4 w-4" />
        New job
      </Link>
    </Panel>
  );
}

function formatSurveyType(value: string | null): string {
  if (!value) return "—";
  return value
    .split("_")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}
