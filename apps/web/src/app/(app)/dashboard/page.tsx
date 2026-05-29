"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  ArrowRight,
  ClipboardList,
  FileText,
  FolderOpen,
  Loader2,
  Plus,
  Settings,
  ShieldCheck,
  TimerReset,
} from "lucide-react";
import { PageHeader } from "@/components/page-header";
import { Panel, PanelHeader } from "@/components/panel";
import { JobStatusChip } from "@/components/status-chip";
import { MetricCard } from "@/components/summary-metrics";
import { listJobs } from "@/lib/api";
import { formatCurrency } from "@/lib/format";
import { useActiveOrg } from "@/lib/use-active-org";
import type { JobSummary } from "@/lib/types";

export default function DashboardPage() {
  const { orgId, ready } = useActiveOrg();
  const [jobs, setJobs] = useState<JobSummary[] | null>(null);

  useEffect(() => {
    if (!ready) return;
    let cancelled = false;
    listJobs(orgId)
      .then((rows) => !cancelled && setJobs(rows))
      .catch(() => !cancelled && setJobs([]));
    return () => {
      cancelled = true;
    };
  }, [orgId, ready]);

  const open = jobs?.filter((j) => !["exported", "rejected"].includes(j.status)) ?? [];
  const needReview = jobs?.filter((j) => j.status === "in_review").length ?? 0;
  const pipeline = jobs?.reduce((sum, j) => sum + (j.total_inc_gst ?? 0), 0) ?? 0;

  return (
    <div>
      <PageHeader
        eyebrow="Workspace"
        title="Estimator dashboard"
        description="Turn asbestos surveys into evidence-linked quote drafts — processed automatically, approved by you."
        actions={
          <Link href="/jobs/new" className="btn-primary">
            <Plus className="h-4 w-4" />
            New job
          </Link>
        }
      />

      <div className="grid gap-4 md:grid-cols-4">
        <MetricCard label="Open jobs" value={String(open.length)} detail="In progress" icon={FileText} accent="cyan" />
        <MetricCard label="Awaiting review" value={String(needReview)} detail="Need a human" icon={TimerReset} accent="amber" />
        <MetricCard
          label="Quoted pipeline"
          value={formatCurrency(pipeline)}
          detail="All jobs (inc GST)"
          icon={ShieldCheck}
          accent="violet"
        />
        <MetricCard
          label="Total jobs"
          value={jobs ? String(jobs.length) : "—"}
          detail="This organisation"
          icon={ClipboardList}
          accent="rose"
        />
      </div>

      <div className="mt-6 grid gap-6 xl:grid-cols-[1.4fr_0.6fr]">
        <Panel>
          <PanelHeader
            title="Recent jobs"
            description="Your most recent surveys and where each one sits in the workflow."
            right={
              <Link href="/jobs" className="inline-flex items-center gap-1.5 text-sm font-semibold text-cyan-300 hover:text-cyan-200">
                View all <ArrowRight className="h-4 w-4" />
              </Link>
            }
          />
          {!jobs ? (
            <div className="flex items-center gap-3 px-5 py-8 text-sm text-graphite">
              <Loader2 className="h-4 w-4 animate-spin text-cyan-300" />
              Loading jobs…
            </div>
          ) : jobs.length === 0 ? (
            <div className="flex flex-col items-center px-5 py-12 text-center">
              <div className="grid h-12 w-12 place-items-center rounded-xl border border-white/10 bg-white/[0.04] text-cyan-300">
                <FolderOpen className="h-6 w-6" />
              </div>
              <div className="mt-4 font-semibold text-ink">No jobs yet</div>
              <p className="mt-1 max-w-xs text-sm text-graphite">Upload your first survey to see it processed into a quote draft.</p>
              <Link href="/jobs/new" className="btn-primary mt-5">
                <Plus className="h-4 w-4" />
                New job
              </Link>
            </div>
          ) : (
            <div className="divide-y divide-white/[0.06]">
              {jobs.slice(0, 6).map((job) => (
                <Link
                  key={job.id}
                  href={`/jobs/${job.id}`}
                  className="flex items-center justify-between gap-4 px-5 py-4 transition hover:bg-white/[0.02]"
                >
                  <div className="flex items-start gap-3">
                    <FileText className="mt-0.5 h-4 w-4 shrink-0 text-cyan-300" />
                    <div>
                      <div className="font-semibold text-ink">{job.client_name || job.file_name}</div>
                      <div className="mt-0.5 text-xs text-graphite">{job.site_address || job.file_name}</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <span className="hidden text-sm font-semibold text-ink sm:inline">
                      {job.total_inc_gst != null ? formatCurrency(job.total_inc_gst) : "—"}
                    </span>
                    <JobStatusChip status={job.status} />
                  </div>
                </Link>
              ))}
            </div>
          )}
        </Panel>

        <div className="space-y-4">
          <Link href="/jobs/new" className="group block">
            <Panel className="p-5 transition group-hover:border-cyan-300/40">
              <Plus className="h-5 w-5 text-cyan-300" />
              <div className="mt-3 font-semibold text-ink">Start a new job</div>
              <p className="mt-1 text-sm text-graphite">Upload a survey and get a priced draft automatically.</p>
            </Panel>
          </Link>
          <Link href="/jobs" className="group block">
            <Panel className="p-5 transition group-hover:border-cyan-300/40">
              <FolderOpen className="h-5 w-5 text-cyan-300" />
              <div className="mt-3 font-semibold text-ink">All jobs</div>
              <p className="mt-1 text-sm text-graphite">Browse, resume, and export every quote job.</p>
            </Panel>
          </Link>
          <Link href={`/admin/organisations/${orgId}/pricebook`} className="group block">
            <Panel className="p-5 transition group-hover:border-cyan-300/40">
              <Settings className="h-5 w-5 text-cyan-300" />
              <div className="mt-3 font-semibold text-ink">Pricebook</div>
              <p className="mt-1 text-sm text-graphite">Tune the rates this organisation prices against.</p>
            </Panel>
          </Link>
        </div>
      </div>
    </div>
  );
}
