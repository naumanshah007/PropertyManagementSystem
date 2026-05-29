"use client";

import type React from "react";
import { useEffect, useState } from "react";
import { AlertTriangle, ChevronDown, ChevronUp, Eye, EyeOff, Loader2 } from "lucide-react";
import { extractRegister, getRegisterExtraction } from "@/lib/api";
import { formatNumber, formatPercent } from "@/lib/format";
import type { ExtractedRegisterItem, RegisterExtractionResult, RegisterReviewStatus } from "@/lib/types";
import { readWorkupAttachment, type WorkupDocumentAttachment } from "@/lib/workup-documents";
import { Panel, PanelHeader } from "./panel";
import { EvidenceChip, RiskChip } from "./status-chip";

export function ExtractedRegisterPanel({
  workupId,
  fallback,
}: {
  workupId: string;
  fallback: React.ReactNode;
}) {
  const [attachment, setAttachment] = useState<WorkupDocumentAttachment | null>(null);
  const [result, setResult] = useState<RegisterExtractionResult | null>(null);
  const [status, setStatus] = useState<"idle" | "loading" | "extracting" | "loaded" | "error">("idle");
  const [message, setMessage] = useState("Upload and parse a PDF to run deterministic register extraction.");
  const [showReference, setShowReference] = useState(false);
  const [showWarnings, setShowWarnings] = useState(false);

  useEffect(() => {
    const attached = readWorkupAttachment(workupId);
    if (attached) {
      setAttachment(attached);
    }

    function handleAttached(event: Event) {
      const custom = event as CustomEvent<WorkupDocumentAttachment>;
      if (custom.detail.workupId === workupId) {
        setAttachment(custom.detail);
        setResult(null);
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
    setStatus("loading");
    setMessage("Checking for existing register extraction...");
    getRegisterExtraction(attachment.documentId)
      .then((extraction) => {
        if (cancelled) {
          return;
        }
        setResult(extraction);
        setStatus("loaded");
        setMessage(`Loaded ${extraction.items.length} extracted register items.`);
      })
      .catch(() => {
        if (cancelled) {
          return;
        }
        setStatus("idle");
        setMessage("Survey attached. Run extraction to populate the register.");
      });

    return () => {
      cancelled = true;
    };
  }, [attachment]);

  async function handleExtract() {
    if (!attachment) {
      return;
    }
    setStatus("extracting");
    setMessage("Extracting register rows and access warnings...");
    try {
      const extraction = await extractRegister(attachment.documentId);
      setResult(extraction);
      setStatus("loaded");
      setMessage(`Extracted ${extraction.items.length} register items with ${extraction.warnings.length} warnings.`);
    } catch (error) {
      setStatus("error");
      setMessage(error instanceof Error ? error.message : "Register extraction failed.");
    }
  }

  if (!result) {
    return (
      <Panel>
        <PanelHeader
          title="Extracted asbestos register"
          description="Asbestos register rows extracted from the survey, with explicit review-required flags."
          right={
            attachment ? (
              <button
                type="button"
                onClick={() => void handleExtract()}
                disabled={status === "extracting"}
                className="focus-ring rounded-md bg-ink px-3 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-60"
              >
                {status === "extracting" ? "Extracting..." : "Run extraction"}
              </button>
            ) : null
          }
        />
        <div className="border-b border-line bg-slate-50 px-5 py-3 text-sm text-graphite">{message}</div>
        {attachment ? (
          <div className="border-b border-line px-5 py-3 text-sm text-graphite">
            Attached document: <span className="font-semibold text-ink">{attachment.fileName}</span> · {attachment.pageCount} pages
          </div>
        ) : null}
        {fallback}
      </Panel>
    );
  }

  const quoteReady = result.items.filter((i) => i.extraction_category === "quote_ready");
  const reviewNeeded = result.items.filter((i) => i.extraction_category === "review_required");
  const referenceOnly = result.items.filter((i) => i.extraction_category === "reference_only");
  const excluded = result.items.filter((i) => i.extraction_category === "excluded_from_pricing");

  return (
    <Panel>
      <PanelHeader
        title="Extracted asbestos register"
        description="Items are grouped by how they feed the quote. Only quote-ready and review-required scope is priced; reference rows stay as traceable evidence."
        right={status === "extracting" ? <Loader2 className="h-4 w-4 animate-spin text-cyan-300" /> : <RiskChip label={`${result.items.length} rows`} />}
      />
      <div className="border-b border-white/10 bg-white/[0.03] px-5 py-3 text-sm text-graphite">{message}</div>
      {result.warnings.length ? (
        <div className="border-b border-white/10">
          <button
            type="button"
            onClick={() => setShowWarnings((v) => !v)}
            className="flex w-full items-center justify-between px-5 py-3 text-sm font-semibold text-graphite transition hover:text-ink"
          >
            <span className="inline-flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-amber-300" />
              Parser warnings · {result.warnings.length}
            </span>
            <span className="inline-flex items-center gap-1.5 text-cyan-300">
              {showWarnings ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
              {showWarnings ? "Hide" : "Show"}
            </span>
          </button>
          {showWarnings ? (
            <ul className="list-disc space-y-1 px-5 pb-4 pl-10 text-sm text-amber-100/90">
              {result.warnings.map((warning, index) => (
                <li key={`${warning.page_number ?? "global"}-${index}`}>
                  {warning.page_number ? `Page ${warning.page_number}: ` : ""}
                  {warning.message}
                </li>
              ))}
            </ul>
          ) : null}
        </div>
      ) : null}

      <RegisterSection
        title="Quote-ready scope"
        subtitle="Clear material, extent, and class — priced directly."
        accent="emerald"
        items={quoteReady}
      />
      <RegisterSection
        title="Needs estimator review"
        subtitle="Class A, no-access, limited-access, or presumed — priced but flagged for human sign-off."
        accent="amber"
        items={reviewNeeded}
      />
      <RegisterSection
        title="Excluded / NAD"
        subtitle="Non-asbestos or no-asbestos-detected — kept as a note, never priced."
        accent="slate"
        items={excluded}
      />

      {referenceOnly.length ? (
        <div className="border-t border-white/10">
          <button
            type="button"
            onClick={() => setShowReference((v) => !v)}
            className="flex w-full items-center justify-between px-5 py-3 text-sm font-semibold text-graphite transition hover:text-ink"
          >
            <span>
              Reference evidence
              <span className="ml-2 font-normal text-graphite">
                · {referenceOnly.length} duplicate / TBC / unknown rows hidden from pricing
              </span>
            </span>
            <span className="inline-flex items-center gap-1.5 text-cyan-300">
              {showReference ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              {showReference ? "Hide" : "Show all extracted evidence"}
            </span>
          </button>
          {showReference ? <RegisterRows items={referenceOnly} /> : null}
        </div>
      ) : null}
    </Panel>
  );
}

function RegisterSection({
  title,
  subtitle,
  accent,
  items,
}: {
  title: string;
  subtitle: string;
  accent: "emerald" | "amber" | "slate";
  items: ExtractedRegisterItem[];
}) {
  if (!items.length) return null;
  const dot =
    accent === "emerald" ? "bg-emerald-300" : accent === "amber" ? "bg-amber-300" : "bg-slate-400";
  return (
    <div className="border-t border-white/10">
      <div className="flex items-center justify-between gap-3 px-5 py-3">
        <div className="flex items-start gap-2.5">
          <span className={`mt-1.5 h-2 w-2 rounded-full ${dot} shadow-[0_0_8px_currentColor]`} />
          <div>
            <div className="text-sm font-semibold text-ink">
              {title} <span className="text-graphite">· {items.length}</span>
            </div>
            <div className="text-xs text-graphite">{subtitle}</div>
          </div>
        </div>
      </div>
      <RegisterRows items={items} />
    </div>
  );
}

function RegisterRows({ items }: { items: ExtractedRegisterItem[] }) {
  // Source evidence is collapsed by default — kept fully available on demand
  // so the demo stays clean without losing traceability.
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const toggle = (id: string) =>
    setExpanded((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-white/10 text-sm">
        <thead className="bg-white/[0.04] text-left text-[11px] font-semibold uppercase tracking-[0.12em] text-graphite">
          <tr>
            <th className="px-4 py-3">Location / Item</th>
            <th className="px-4 py-3">Material</th>
            <th className="px-4 py-3">Extent</th>
            <th className="px-4 py-3">Risk</th>
            <th className="px-4 py-3">Confidence</th>
            <th className="px-4 py-3">Pricing signal</th>
            <th className="px-4 py-3">Source</th>
            <th className="px-4 py-3">Review</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-white/[0.06]">
          {items.map((item) => {
            const isOpen = expanded.has(item.id);
            return (
              <tr key={item.id} className="align-top transition-colors hover:bg-white/[0.02]">
                <td className="min-w-72 px-4 py-4">
                  <div className="font-semibold text-ink">
                    {[item.building, item.location].filter(Boolean).join(" · ")}
                  </div>
                  <div className="mt-1 text-graphite">{item.item}</div>
                  {item.recommendation ? <div className="mt-2 text-xs leading-5 text-slate-400">{item.recommendation}</div> : null}
                </td>
                <td className="min-w-56 px-4 py-4 text-graphite">{item.material}</td>
                <td className="whitespace-nowrap px-4 py-4 text-graphite">
                  {item.extent_quantity === null ? "TBC" : `${formatNumber(item.extent_quantity)} ${item.extent_unit ?? ""}`}
                </td>
                <td className="min-w-52 px-4 py-4">
                  <div className="flex flex-wrap gap-1.5">
                    <RiskChip label={item.friability_class} />
                    <RiskChip label={item.asbestos_result} />
                    <RiskChip label={item.access_status.replace("_", " ")} />
                  </div>
                </td>
                <td className="whitespace-nowrap px-4 py-4 font-medium text-graphite">{formatPercent(item.confidence)}</td>
                <td className="min-w-64 px-4 py-4 text-xs leading-5 text-graphite">
                  <div className="font-semibold text-ink">{whyPricingMatters(item)}</div>
                  <div className="mt-1 text-slate-400">{mappedQuoteAction(item)}</div>
                </td>
                <td className="min-w-60 px-4 py-4 text-xs leading-5 text-graphite">
                  <div className="flex items-center gap-2">
                    <EvidenceChip page={item.source_page} label="source" />
                    <button
                      type="button"
                      onClick={() => toggle(item.id)}
                      className="inline-flex items-center gap-1 font-semibold text-cyan-300 hover:text-cyan-200"
                    >
                      {isOpen ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
                      {isOpen ? "Hide" : "View full evidence"}
                    </button>
                  </div>
                  {isOpen ? (
                    <div className="mt-2 rounded-md border border-white/10 bg-white/[0.04] p-2 leading-5">
                      {item.source_evidence.text}
                    </div>
                  ) : null}
                </td>
                <td className="px-4 py-4">
                  <RegisterReviewChip status={item.review_status} />
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function whyPricingMatters(item: RegisterExtractionResult["items"][number]) {
  if (item.asbestos_result === "NAD") {
    return "Excluded from asbestos pricing";
  }
  if (item.access_status === "no_access") {
    return "Requires provisional investigation allowance";
  }
  if (item.friability_class === "Class A") {
    return "Triggers friable/Class A review and allowance";
  }
  if (item.friability_class === "Class B") {
    return "Maps to controlled non-friable removal";
  }
  return "Requires estimator classification";
}

function mappedQuoteAction(item: RegisterExtractionResult["items"][number]) {
  if (item.asbestos_result === "NAD") {
    return "Show under Excluded / NAD Findings";
  }
  if (item.access_status === "no_access") {
    return "Create Provisional / No Access line";
  }
  if (item.friability_class === "Class A") {
    return "Create Class A / Friable Removal line";
  }
  if (item.friability_class === "Class B") {
    return "Create Class B Removal line";
  }
  return "Create estimator review candidate";
}

function RegisterReviewChip({ status }: { status: RegisterReviewStatus }) {
  const classes =
    status === "review_required"
      ? "border-amber-400 bg-amber-50 text-amber-900"
      : status === "excluded_from_pricing"
        ? "border-slate-300 bg-white text-slate-700"
        : "border-slate-300 bg-slate-50 text-slate-800";
  const label =
    status === "review_required"
      ? "Review required"
      : status === "excluded_from_pricing"
        ? "Excluded from pricing"
        : "AI draft";
  return <span className={`inline-flex rounded-full border px-2.5 py-1 text-xs font-semibold ${classes}`}>{label}</span>;
}
