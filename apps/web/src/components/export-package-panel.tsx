"use client";

import { useEffect, useState } from "react";
import { Download, FileArchive, Loader2, LockKeyhole, ShieldCheck } from "lucide-react";
import { API_BASE_URL, exportJob, exportQuote, getApprovalReadiness, getQuoteExport } from "@/lib/api";
import { formatCurrency } from "@/lib/format";
import type { ApprovalReadinessResult, QuoteExportPackage, QuoteExportRequest } from "@/lib/types";
import { readWorkupAttachment, type WorkupDocumentAttachment } from "@/lib/workup-documents";
import { Panel, PanelHeader } from "./panel";
import { RiskChip } from "./status-chip";

export function ExportPackagePanel({
  workupId,
  orgId,
  jobId,
  onExported,
}: {
  workupId: string;
  orgId?: string;
  jobId?: string;
  onExported?: () => void;
}) {
  const [attachment, setAttachment] = useState<WorkupDocumentAttachment | null>(null);
  const [readiness, setReadiness] = useState<ApprovalReadinessResult | null>(null);
  const [exportPackage, setExportPackage] = useState<QuoteExportPackage | null>(null);
  const [details, setDetails] = useState<QuoteExportRequest>({
    client_name: "Tauraroa Area School",
    project_name: "Asbestos removal workup",
    site_address: "Tauraroa Area School, Northland, New Zealand",
    quote_number: "",
    scope_summary: "Reviewed asbestos removal and provisional investigation scope derived from the uploaded asbestos demolition survey.",
  });
  const [status, setStatus] = useState<"idle" | "loading" | "exporting" | "ready" | "blocked" | "exported" | "error">("idle");
  const [message, setMessage] = useState("Attach and review a parsed document before export.");

  useEffect(() => {
    const attached = readWorkupAttachment(workupId);
    setAttachment(attached);

    function handleAttached(event: Event) {
      const custom = event as CustomEvent<WorkupDocumentAttachment>;
      if (custom.detail.workupId === workupId) {
        setAttachment(custom.detail);
        setReadiness(null);
        setExportPackage(null);
      }
    }

    window.addEventListener("tracequote:workup-document-attached", handleAttached);
    return () => window.removeEventListener("tracequote:workup-document-attached", handleAttached);
  }, [workupId]);

  useEffect(() => {
    if (!attachment) {
      return;
    }

    let cancelled = false;
    async function loadExportState() {
      if (!attachment) {
        return;
      }
      setStatus("loading");
      setMessage("Checking approval readiness and existing export package...");
      try {
        const [nextReadiness, existingExport] = await Promise.allSettled([
          getApprovalReadiness(attachment.documentId),
          getQuoteExport(attachment.documentId),
        ]);
        if (cancelled) {
          return;
        }
        if (nextReadiness.status === "fulfilled") {
          setReadiness(nextReadiness.value);
          setStatus(nextReadiness.value.approval_status === "ready_for_approval" ? "ready" : "blocked");
          setMessage(
            nextReadiness.value.approval_status === "ready_for_approval"
              ? "Approval gates have passed. Client-facing quote export is available."
              : "Export is blocked until review gates are resolved in Quote Builder.",
          );
        } else {
          setStatus("blocked");
          setMessage("No priced quote readiness record exists yet. Generate pricing and resolve reviews first.");
        }
        if (existingExport.status === "fulfilled") {
          setExportPackage(existingExport.value);
          setStatus("exported");
          setMessage("Generated quote package is available.");
        }
      } catch (error) {
        if (cancelled) {
          return;
        }
        setStatus("error");
        setMessage(error instanceof Error ? error.message : "Export state check failed.");
      }
    }

    void loadExportState();
    return () => {
      cancelled = true;
    };
  }, [attachment]);

  async function handleExport() {
    if (!attachment) {
      return;
    }
    setStatus("exporting");
    setMessage("Generating client-facing quote package...");
    try {
      const payload = {
        ...details,
        quote_number: details.quote_number?.trim() ? details.quote_number : null,
      };
      // When opened inside a job workspace, export through the job so its
      // status flips to "exported"; otherwise fall back to the raw document export.
      const result =
        orgId && jobId
          ? await exportJob(orgId, jobId, payload)
          : await exportQuote(attachment.documentId, payload);
      setExportPackage(result);
      setStatus("exported");
      setMessage("Quote package generated and stored.");
      onExported?.();
    } catch (error) {
      setStatus("error");
      setMessage(error instanceof Error ? error.message : "Quote export failed.");
    }
  }

  return (
    <Panel>
      <PanelHeader
        title="Client-facing quote package"
        description="Export is allowed only after estimator review gates pass."
        right={status === "loading" || status === "exporting" ? <Loader2 className="h-4 w-4 animate-spin text-moss" /> : <RiskChip label={status === "exported" ? "Exported" : status === "ready" ? "Ready" : "Blocked"} />}
      />
      <div className="border-b border-line bg-slate-50 px-5 py-4 text-sm text-graphite">{message}</div>
      {attachment ? (
        <div className="grid gap-3 border-b border-line p-5 md:grid-cols-4">
          <Metric label="Document" value={attachment.fileName} />
          <Metric label="Pages" value={String(attachment.pageCount)} />
          <Metric label="Parser" value={attachment.parserVersion} />
          <Metric label="Readiness" value={readiness?.approval_status === "ready_for_approval" ? "Ready" : "Blocked"} />
        </div>
      ) : (
        <div className="p-5 text-sm leading-6 text-graphite">Upload and attach a PDF to this workup before exporting a quote package.</div>
      )}

      {readiness ? (
        <div className="border-b border-line p-5">
          <div className="mb-3 text-sm font-semibold text-ink">Approval checklist</div>
          <div className="grid gap-2 md:grid-cols-2">
            {readiness.checks.map((check) => (
              <div key={check.id} className="rounded-md border border-line bg-white p-3">
                <div className="flex items-center gap-2">
                  {check.status === "passed" ? <ShieldCheck className="h-4 w-4 text-verified" /> : <LockKeyhole className="h-4 w-4 text-blocked" />}
                  <span className="text-sm font-semibold text-ink">{check.label}</span>
                </div>
                <p className="mt-1 text-xs leading-5 text-graphite">{check.details}</p>
              </div>
            ))}
          </div>
        </div>
      ) : null}

      <div className="border-b border-line p-5">
        <div className="mb-3 text-sm font-semibold text-ink">Client/project details</div>
        <div className="grid gap-3 md:grid-cols-2">
          <TextField label="Client" value={details.client_name} onChange={(value) => setDetails((current) => ({ ...current, client_name: value }))} />
          <TextField label="Project" value={details.project_name} onChange={(value) => setDetails((current) => ({ ...current, project_name: value }))} />
          <TextField label="Site address" value={details.site_address} onChange={(value) => setDetails((current) => ({ ...current, site_address: value }))} />
          <TextField label="Quote number" value={details.quote_number ?? ""} onChange={(value) => setDetails((current) => ({ ...current, quote_number: value }))} />
          <label className="md:col-span-2 text-xs font-semibold uppercase tracking-wide text-graphite">
            Scope summary
            <textarea
              value={details.scope_summary}
              onChange={(event) => setDetails((current) => ({ ...current, scope_summary: event.target.value }))}
              className="mt-1 min-h-20 w-full rounded-md border border-line px-3 py-2 text-sm normal-case tracking-normal text-ink"
            />
          </label>
        </div>
      </div>

      <div className="space-y-3 p-5">
        <button
          type="button"
          disabled={!attachment || status === "blocked" || status === "loading" || status === "exporting"}
          onClick={() => void handleExport()}
          className="focus-ring flex w-full items-center justify-between rounded-md border border-ink bg-ink px-4 py-3 text-left text-sm font-semibold text-white disabled:cursor-not-allowed disabled:border-line disabled:bg-slate-100 disabled:text-slate-400"
        >
          <span className="flex items-center gap-3">
            <FileArchive className="h-4 w-4" />
            Generate client quote package
          </span>
          {status === "exporting" ? <Loader2 className="h-4 w-4 animate-spin" /> : <Download className="h-4 w-4" />}
        </button>

        {exportPackage ? (
          <div className="rounded-md border border-line bg-slate-50 p-4">
            <div className="grid gap-3 md:grid-cols-4">
              <Metric label="Quote number" value={exportPackage.quote_number} />
              <Metric label="Lines" value={String(exportPackage.line_count)} />
              <Metric label="Total inc GST" value={formatCurrency(exportPackage.total_inc_gst)} />
              <Metric label="Generated" value={new Date(exportPackage.generated_at).toLocaleString("en-NZ")} />
            </div>
            <div className="mt-4 grid gap-2 md:grid-cols-2">
              <a
                href={`${API_BASE_URL}${exportPackage.pdf_download_path}`}
                target="_blank"
                rel="noreferrer"
                className="focus-ring rounded-md border border-line bg-white px-4 py-3 text-sm font-semibold text-ink hover:border-moss"
              >
                Download quote PDF
              </a>
              <div className="rounded-md border border-line bg-white px-4 py-3 text-sm text-graphite">
                Metadata: <span className="font-semibold text-ink">{`${API_BASE_URL}/documents/${exportPackage.document_id}/export-quote`}</span>
              </div>
            </div>
          </div>
        ) : null}
      </div>
    </Panel>
  );
}

function TextField({ label, value, onChange }: { label: string; value: string; onChange: (value: string) => void }) {
  return (
    <label className="text-xs font-semibold uppercase tracking-wide text-graphite">
      {label}
      <input
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="mt-1 w-full rounded-md border border-line px-3 py-2 text-sm normal-case tracking-normal text-ink"
      />
    </label>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-line bg-white p-3">
      <div className="text-xs font-semibold uppercase tracking-wide text-moss">{label}</div>
      <div className="mt-1 truncate text-sm font-semibold text-ink">{value}</div>
    </div>
  );
}
