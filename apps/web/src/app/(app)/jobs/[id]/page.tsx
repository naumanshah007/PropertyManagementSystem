"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { AlertTriangle, ArrowLeft, CheckCircle2, Loader2, Sparkles } from "lucide-react";
import { AccessDenied } from "@/components/access-denied";
import { PageHeader } from "@/components/page-header";
import { Panel, PanelHeader } from "@/components/panel";
import { JobStatusChip, RiskChip } from "@/components/status-chip";
import { JobStepper } from "@/components/job-stepper";
import { MagicExtractionPanel } from "@/components/magic-extraction-panel";
import { ExtractedRegisterPanel } from "@/components/extracted-register-panel";
import { QuoteCandidatePanel } from "@/components/quote-candidate-panel";
import { ExportPackagePanel } from "@/components/export-package-panel";
import { ApiError, approveJob, getApprovalReadiness, getJob, processJob } from "@/lib/api";
import { formatCurrency } from "@/lib/format";
import { useActiveOrg } from "@/lib/use-active-org";
import { saveWorkupAttachment } from "@/lib/workup-documents";
import type { ApprovalReadinessResult, Job } from "@/lib/types";

export default function JobWorkspacePage() {
  const params = useParams<{ id: string }>();
  const jobId = params.id;
  const { orgId, ready } = useActiveOrg();

  const [job, setJob] = useState<Job | null>(null);
  const [readiness, setReadiness] = useState<ApprovalReadinessResult | null>(null);
  const [bridged, setBridged] = useState(false);
  const [busy, setBusy] = useState<"processing" | "approving" | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [forbidden, setForbidden] = useState(false);
  // Demo mode = simplified executive view (detailed register collapsed). Persisted.
  const [demoMode, setDemoMode] = useState(true);
  const [detailOpen, setDetailOpen] = useState(false);

  useEffect(() => {
    const saved = typeof window !== "undefined" ? window.localStorage.getItem("tracequote:demoMode") : null;
    const dm = saved === null ? true : saved === "true";
    setDemoMode(dm);
    setDetailOpen(!dm);
  }, []);

  function toggleDemoMode() {
    setDemoMode((prev) => {
      const next = !prev;
      if (typeof window !== "undefined") window.localStorage.setItem("tracequote:demoMode", String(next));
      setDetailOpen(!next);
      return next;
    });
  }

  const refreshReadiness = useCallback(
    async (documentId: string) => {
      try {
        setReadiness(await getApprovalReadiness(documentId));
      } catch {
        setReadiness(null);
      }
    },
    [],
  );

  // Load the job, bridge its document into the panel state, auto-process if new.
  useEffect(() => {
    if (!ready) return;
    let cancelled = false;

    async function load() {
      try {
        let current = await getJob(orgId, jobId);
        if (cancelled) return;

        // Bridge jobId → documentId so the existing data panels resolve real data.
        saveWorkupAttachment({
          workupId: jobId,
          documentId: current.document_id,
          fileName: current.file_name,
          pageCount: 0,
          parserVersion: "",
          ocrStatus: "",
          parsedStatus: "parsed",
          uploadedAt: current.created_at,
        });
        setBridged(true);
        setJob(current);

        // One-click auto-run: freshly uploaded jobs are processed on open.
        if (current.status === "uploaded") {
          setBusy("processing");
          const result = await processJob(orgId, jobId);
          if (cancelled) return;
          current = result.job;
          setJob(current);
          setBusy(null);
        }

        if (["priced", "in_review", "approved"].includes(current.status)) {
          void refreshReadiness(current.document_id);
        }
      } catch (e) {
        if (!cancelled) {
          if (e instanceof ApiError && e.status === 403) {
            setForbidden(true);
          } else {
            setError(e instanceof Error ? e.message : "Failed to load job");
          }
          setBusy(null);
        }
      }
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, [orgId, jobId, ready, refreshReadiness]);

  async function handleApprove() {
    if (!job) return;
    setBusy("approving");
    setError(null);
    try {
      const updated = await approveJob(orgId, jobId);
      setJob(updated);
      void refreshReadiness(updated.document_id);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Approval failed");
    } finally {
      setBusy(null);
    }
  }

  if (forbidden) {
    return (
      <div>
        <BackLink />
        <div className="mt-4">
          <AccessDenied message="You don't have access to this job." />
        </div>
      </div>
    );
  }

  if (error && !job) {
    return (
      <div>
        <BackLink />
        <Panel className="mt-4 p-6 text-sm text-rose-200">{error}</Panel>
      </div>
    );
  }

  if (!job) {
    return (
      <div>
        <BackLink />
        <Panel className="mt-4 flex items-center gap-3 p-6 text-sm text-graphite">
          <Loader2 className="h-4 w-4 animate-spin text-cyan-300" />
          Loading job…
        </Panel>
      </div>
    );
  }

  const isRejected = job.status === "rejected";
  const isProcessing = busy === "processing" || job.status === "processing";
  const canApprove = readiness?.approval_status === "ready_for_approval";
  const showQuote = ["priced", "in_review", "approved", "exported"].includes(job.status);
  const showExport = ["approved", "exported"].includes(job.status);

  return (
    <div>
      <BackLink />

      <div className="mt-3">
        <PageHeader
          eyebrow="Job workspace"
          title={job.client_name || job.file_name}
          description={
            job.site_address
              ? `${formatSurveyType(job.survey_type)} · ${job.site_address}`
              : `${formatSurveyType(job.survey_type)} · ${job.file_name}`
          }
          actions={<JobStatusChip status={job.status} />}
        />
      </div>

      <Panel className="p-5">
        <JobStepper status={job.status} />
      </Panel>

      {/* Status-driven next-action bar */}
      <div className="mt-6">
        {isRejected ? (
          <Panel className="border-rose-300/30 p-5">
            <div className="flex items-start gap-3">
              <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-rose-300" />
              <div>
                <div className="font-semibold text-rose-100">This survey can&apos;t be quoted</div>
                <p className="mt-1 text-sm leading-6 text-graphite">{job.rejected_reason}</p>
                <p className="mt-2 text-sm text-graphite">
                  Management plans don&apos;t contain the sample-level detail needed to price removal works. Upload a
                  management, refurbishment, or demolition survey instead.
                </p>
              </div>
            </div>
          </Panel>
        ) : isProcessing ? (
          <Panel className="p-5">
            <div className="flex items-center gap-3 text-sm text-ink">
              <Loader2 className="h-5 w-5 animate-spin text-cyan-300" />
              <div>
                <div className="font-semibold">Processing survey…</div>
                <div className="text-graphite">Extracting the register, mapping quote candidates, and pricing against your pricebook.</div>
              </div>
            </div>
          </Panel>
        ) : (
          <Panel className="flex flex-col gap-4 p-5 md:flex-row md:items-center md:justify-between">
            <div className="grid grid-cols-3 gap-6">
              <Metric label="Register items" value={String(job.register_items)} />
              <Metric label="Need review" value={String(job.review_required)} accent={job.review_required > 0} />
              <Metric label="Quote total" value={job.total_inc_gst != null ? formatCurrency(job.total_inc_gst) : "—"} />
            </div>
            <div className="flex items-center gap-3">
              {job.status === "approved" || job.status === "exported" ? (
                <span className="inline-flex items-center gap-2 text-sm font-semibold text-emerald-200">
                  <CheckCircle2 className="h-4 w-4" /> Approved — ready to export
                </span>
              ) : canApprove ? (
                <button onClick={() => void handleApprove()} disabled={busy === "approving"} className="btn-primary disabled:opacity-60">
                  {busy === "approving" ? <Loader2 className="h-4 w-4 animate-spin" /> : <CheckCircle2 className="h-4 w-4" />}
                  Approve &amp; continue
                </button>
              ) : (
                <div className="flex items-center gap-2">
                  <RiskChip label={`${job.review_required} review required`} />
                  <span className="text-sm text-graphite">Resolve below to unlock approval</span>
                </div>
              )}
            </div>
          </Panel>
        )}
      </div>

      {error ? <div className="mt-4 text-sm text-rose-200">{error}</div> : null}

      {/* Step content (only meaningful once bridged + processed) */}
      {!isRejected && bridged ? (
        <div className="mt-6 space-y-6">
          <div className="flex items-center justify-end">
            <button
              type="button"
              onClick={toggleDemoMode}
              className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.04] px-3 py-1.5 text-xs font-semibold text-graphite transition hover:text-ink"
              title="Toggle simplified executive view"
            >
              <span
                className={`relative h-4 w-7 rounded-full transition ${demoMode ? "bg-grad-primary" : "bg-white/15"}`}
              >
                <span
                  className={`absolute top-0.5 h-3 w-3 rounded-full bg-night-900 transition ${demoMode ? "left-3.5" : "left-0.5"}`}
                />
              </span>
              Demo mode: {demoMode ? "simplified" : "full detail"}
            </button>
          </div>

          <section>
            <SectionHeading icon={Sparkles} title="Survey review" subtitle="What we extracted from this survey — every item links back to its source page." />
            <MagicExtractionPanel workupId={jobId} />
            {detailOpen ? (
              <ExtractedRegisterPanel workupId={jobId} fallback={<EmptyHint text="Processing the survey will populate the register here." />} />
            ) : (
              <button
                type="button"
                onClick={() => setDetailOpen(true)}
                className="btn-secondary mt-3"
              >
                Show detailed register &amp; evidence
              </button>
            )}
          </section>

          {showQuote ? (
            <section>
              <SectionHeading icon={Sparkles} title="Pricing" subtitle="Draft quote lines priced against your pricebook. Resolve review-required lines to unlock approval." />
              <QuoteCandidatePanel workupId={jobId} simplified={demoMode} fallback={<EmptyHint text="No priced lines yet." />} />
            </section>
          ) : null}

          {showExport ? (
            <section>
              <SectionHeading icon={Sparkles} title="Export" subtitle="Generate the client-ready quote package and Fergus CSV." />
              <ExportPackagePanel
                workupId={jobId}
                orgId={orgId}
                jobId={jobId}
                onExported={() => void getJob(orgId, jobId).then(setJob)}
              />
            </section>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}

function BackLink() {
  return (
    <Link href="/jobs" className="inline-flex items-center gap-1.5 text-sm font-semibold text-graphite hover:text-ink">
      <ArrowLeft className="h-4 w-4" /> All jobs
    </Link>
  );
}

function Metric({ label, value, accent }: { label: string; value: string; accent?: boolean }) {
  return (
    <div>
      <div className="text-[11px] font-semibold uppercase tracking-[0.14em] text-graphite">{label}</div>
      <div className={`mt-1 text-xl font-semibold ${accent ? "text-amber-200" : "text-ink"}`}>{value}</div>
    </div>
  );
}

function SectionHeading({
  icon: Icon,
  title,
  subtitle,
}: {
  icon: typeof Sparkles;
  title: string;
  subtitle: string;
}) {
  return (
    <div className="mb-3 flex items-start gap-2.5">
      <div className="mt-0.5 grid h-7 w-7 place-items-center rounded-lg border border-white/10 bg-white/[0.04] text-cyan-300">
        <Icon className="h-4 w-4" />
      </div>
      <div>
        <h2 className="text-lg font-semibold text-ink">{title}</h2>
        <p className="text-sm text-graphite">{subtitle}</p>
      </div>
    </div>
  );
}

function EmptyHint({ text }: { text: string }) {
  return <div className="px-5 py-6 text-sm text-graphite">{text}</div>;
}

function formatSurveyType(value: string | null): string {
  if (!value) return "Survey";
  return value
    .split("_")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}
