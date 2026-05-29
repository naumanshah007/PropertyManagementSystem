"use client";

import type React from "react";
import { useEffect, useMemo, useState } from "react";
import { AlertTriangle, ChevronDown, ChevronUp, Loader2 } from "lucide-react";
import {
  editPricedQuoteLine,
  generateQuoteCandidates,
  getApprovalReadiness,
  getPricedQuoteLines,
  getQuoteCandidates,
  priceQuoteCandidates,
  resolvePricedQuoteLineReview,
} from "@/lib/api";
import { formatCurrency, formatNumber, formatPercent } from "@/lib/format";
import type {
  ApprovalReadinessResult,
  PricedQuoteLine,
  PricedQuoteResult,
  PricingReviewStatus,
  QuoteCandidateGenerationResult,
  QuoteCandidateReviewStatus,
} from "@/lib/types";
import { readWorkupAttachment, type WorkupDocumentAttachment } from "@/lib/workup-documents";
import { Panel, PanelHeader } from "./panel";
import { EvidenceChip, RiskChip } from "./status-chip";

const sectionOrder = [
  "Site Establishment",
  "Class B Removal",
  "Class A / Friable Removal",
  "Provisional / No Access",
  "Waste / Disposal Placeholder",
  "Excluded / NAD Findings",
];

type LineDraft = {
  quantity: string;
  unitRate: string;
  riskMultiplier: string;
  margin: string;
  editReason: string;
  reviewReason: string;
};

export function QuoteCandidatePanel({
  workupId,
  fallback,
  simplified = true,
}: {
  workupId: string;
  fallback: React.ReactNode;
  simplified?: boolean;
}) {
  const [attachment, setAttachment] = useState<WorkupDocumentAttachment | null>(null);
  const [result, setResult] = useState<QuoteCandidateGenerationResult | null>(null);
  const [pricedResult, setPricedResult] = useState<PricedQuoteResult | null>(null);
  const [readiness, setReadiness] = useState<ApprovalReadinessResult | null>(null);
  const [lineDrafts, setLineDrafts] = useState<Record<string, LineDraft>>({});
  const [status, setStatus] = useState<"idle" | "loading" | "generating" | "pricing" | "loaded" | "priced" | "error">("idle");
  const [message, setMessage] = useState("Upload, parse, and extract a PDF to generate quote candidates.");
  const [expandedEvidence, setExpandedEvidence] = useState<Set<string>>(new Set());
  const [showPricingWarnings, setShowPricingWarnings] = useState(false);
  const [forceDetail, setForceDetail] = useState(false);
  // In simplified (demo) mode the detailed editable workbench is hidden behind a
  // toggle; technical reviewers see it directly.
  const showDetail = forceDetail || !simplified;
  const toggleEvidence = (id: string) =>
    setExpandedEvidence((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });

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
        setPricedResult(null);
        setReadiness(null);
        setLineDrafts({});
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
    async function loadQuoteState() {
      if (!attachment) {
        return;
      }
      setStatus("loading");
      setMessage("Checking for priced draft lines and generated quote candidates...");
      try {
        const priced = await getPricedQuoteLines(attachment.documentId);
        if (cancelled) {
          return;
        }
        setPricedResult(priced);
        setLineDrafts((drafts) => seedLineDrafts(priced, drafts));
        setStatus("priced");
        setMessage(`Loaded ${priced.lines.length} priced draft lines. Approval remains blocked until estimator review.`);
        void refreshReadiness(attachment.documentId);
        return;
      } catch {
        // Fall through to candidate lookup. A missing priced result is normal before Phase 5 pricing is run.
      }

      try {
        const candidates = await getQuoteCandidates(attachment.documentId);
        if (cancelled) {
          return;
        }
        setResult(candidates);
        setStatus("loaded");
        setMessage(`Loaded ${candidates.candidates.length} quote candidates.`);
      } catch {
        if (cancelled) {
          return;
        }
        setStatus("idle");
        setMessage("No generated candidates yet. Run mapping after register extraction.");
      }
    }

    void loadQuoteState();

    return () => {
      cancelled = true;
    };
  }, [attachment]);

  async function handleGenerate() {
    if (!attachment) {
      return;
    }
    setStatus("generating");
    setMessage("Mapping extracted register items to quote candidates...");
    try {
      const candidates = await generateQuoteCandidates(attachment.documentId);
      setResult(candidates);
      setPricedResult(null);
      setStatus("loaded");
      setMessage(`Generated ${candidates.candidates.length} quote candidates for estimator review.`);
    } catch (error) {
      setStatus("error");
      setMessage(error instanceof Error ? error.message : "Quote candidate generation failed.");
    }
  }

  async function handlePrice() {
    if (!attachment) {
      return;
    }
    setStatus("pricing");
    setMessage("Applying your company pricebook rates...");
    try {
      const priced = await priceQuoteCandidates(attachment.documentId);
      setPricedResult(priced);
      setLineDrafts((drafts) => seedLineDrafts(priced, drafts));
      setStatus("priced");
      setMessage(`Generated ${priced.lines.length} priced draft lines. Approval remains blocked until estimator review.`);
      void refreshReadiness(attachment.documentId);
    } catch (error) {
      setStatus("error");
      setMessage(error instanceof Error ? error.message : "Quote pricing failed.");
    }
  }

  async function refreshReadiness(documentId: string) {
    try {
      const nextReadiness = await getApprovalReadiness(documentId);
      setReadiness(nextReadiness);
    } catch {
      setReadiness(null);
    }
  }

  function updateLineDraft(line: PricedQuoteLine, patch: Partial<LineDraft>) {
    setLineDrafts((drafts) => ({
      ...drafts,
      [line.id]: {
        ...draftForLine(line),
        ...drafts[line.id],
        ...patch,
      },
    }));
  }

  async function handleEditLine(line: PricedQuoteLine) {
    if (!attachment) {
      return;
    }
    const draft = lineDrafts[line.id] ?? draftForLine(line);
    if (!draft.editReason.trim()) {
      setMessage("A reason is required before saving estimator pricing edits.");
      return;
    }

    setStatus("pricing");
    try {
      const updated = await editPricedQuoteLine(attachment.documentId, line.id, {
        quantity: numberOrNull(draft.quantity),
        unit_rate: numberOrNull(draft.unitRate),
        risk_multiplier: numberOrNull(draft.riskMultiplier),
        margin: numberOrNull(draft.margin),
        reason: draft.editReason.trim(),
      });
      setPricedResult(updated);
      setLineDrafts((drafts) => seedLineDrafts(updated, drafts));
      setStatus("priced");
      setMessage("Estimator edit saved and audit history updated.");
      void refreshReadiness(attachment.documentId);
    } catch (error) {
      setStatus("error");
      setMessage(error instanceof Error ? error.message : "Priced line edit failed.");
    }
  }

  async function handleResolveReview(line: PricedQuoteLine) {
    if (!attachment) {
      return;
    }
    const draft = lineDrafts[line.id] ?? draftForLine(line);
    if (!draft.reviewReason.trim()) {
      setMessage("A review reason is required before resolving a review gate.");
      return;
    }

    setStatus("pricing");
    try {
      const updated = await resolvePricedQuoteLineReview(attachment.documentId, line.id, {
        reason: draft.reviewReason.trim(),
        assumptions_accepted: true,
        exclusions_accepted: true,
      });
      setPricedResult(updated);
      setLineDrafts((drafts) => seedLineDrafts(updated, drafts));
      setStatus("priced");
      setMessage("Review gate resolved. Approval readiness has been rechecked.");
      void refreshReadiness(attachment.documentId);
    } catch (error) {
      setStatus("error");
      setMessage(error instanceof Error ? error.message : "Review resolution failed.");
    }
  }

  const grouped = useMemo(() => {
    if (!result) {
      return [];
    }
    return sectionOrder
      .map((section) => ({
        section,
        rows: result.candidates.filter((candidate) => candidate.section === section),
      }))
      .filter((group) => group.rows.length > 0);
  }, [result]);

  const pricedGrouped = useMemo(() => {
    if (!pricedResult) {
      return [];
    }
    return sectionOrder
      .map((section) => ({
        section,
        rows: pricedResult.lines.filter((line) => line.section === section),
      }))
      .filter((group) => group.rows.length > 0);
  }, [pricedResult]);

  if (!result) {
    return (
      <Panel>
        <PanelHeader
          title="Generated quote candidates"
          description="Static demo quote table remains visible until deterministic candidate mapping has been run."
          right={
            attachment ? (
              <button
                type="button"
                onClick={() => void handleGenerate()}
                disabled={status === "generating"}
                className="focus-ring rounded-md bg-ink px-3 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-60"
              >
                {status === "generating" ? "Generating..." : "Generate Quote Draft"}
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

  if (pricedResult) {
    return (
      <Panel>
        <PanelHeader
          title="Priced draft quote lines"
          description="Priced against your company pricebook. Human review is required before approval or export."
          right={
            status === "pricing" ? (
              <Loader2 className="h-4 w-4 animate-spin text-moss" />
            ) : (
              <RiskChip label={readiness?.approval_status === "ready_for_approval" ? "Ready" : "Blocked"} />
            )
          }
        />
        <div className="grid gap-3 border-b border-line bg-slate-50 px-5 py-4 md:grid-cols-4">
          <TotalBlock label="Subtotal ex GST" value={formatCurrency(pricedResult.subtotal_ex_gst)} />
          <TotalBlock label="GST" value={formatCurrency(pricedResult.gst)} />
          <TotalBlock label="Total inc GST" value={formatCurrency(pricedResult.total_inc_gst)} strong />
          <TotalBlock label="Approval gate" value={readiness?.approval_status === "ready_for_approval" ? "Ready for approval" : "Blocked"} />
        </div>

        {/* Executive view first: clean section cards before the detailed workbench. */}
        <div className="border-b border-white/10 px-5 py-4">
          <div className="mb-3 text-[11px] font-semibold uppercase tracking-[0.14em] text-cyan-300">Quote sections</div>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {pricedGrouped.map((group) => {
              const subtotal = group.rows.reduce((sum, l) => sum + (l.subtotal_ex_gst ?? 0), 0);
              const needsReview = group.rows.filter((l) => l.review_status === "review_required").length;
              const excluded = group.section.toLowerCase().includes("excluded");
              return (
                <div
                  key={`card-${group.section}`}
                  className="rounded-xl border border-white/10 bg-white/[0.04] p-4 backdrop-blur-sm"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="text-sm font-semibold text-ink">{group.section}</div>
                    <span className="text-[11px] font-semibold uppercase tracking-wide text-graphite">
                      {group.rows.length} {group.rows.length === 1 ? "line" : "lines"}
                    </span>
                  </div>
                  <div className="mt-2 text-lg font-semibold text-ink">
                    {excluded ? "Excluded" : formatCurrency(subtotal)}
                  </div>
                  <div className="mt-1 text-xs text-graphite">{excluded ? "Not priced" : "Subtotal ex GST"}</div>
                  {needsReview > 0 ? (
                    <div className="mt-3">
                      <RiskChip label={`${needsReview} need review`} />
                    </div>
                  ) : null}
                </div>
              );
            })}
          </div>
        </div>

        {readiness ? <ApprovalChecklist readiness={readiness} /> : null}
        <div className="border-b border-white/10 bg-amber-400/10 px-5 py-3 text-sm font-medium text-amber-100">
          {message}
        </div>
        {pricedResult.warnings.length ? (
          <div className="border-b border-white/10">
            <button
              type="button"
              onClick={() => setShowPricingWarnings((v) => !v)}
              className="flex w-full items-center justify-between px-5 py-3 text-sm font-semibold text-graphite transition hover:text-ink"
            >
              <span className="inline-flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 text-amber-300" />
                Pricing warnings · {pricedResult.warnings.length}
              </span>
              <span className="inline-flex items-center gap-1.5 text-cyan-300">
                {showPricingWarnings ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                {showPricingWarnings ? "Hide" : "Show"}
              </span>
            </button>
            {showPricingWarnings ? (
              <ul className="list-disc space-y-1 px-5 pb-4 pl-10 text-sm text-amber-100/90">
                {pricedResult.warnings.map((warning, index) => (
                  <li key={`${warning.quote_candidate_id ?? "global"}-${index}`}>{warning.message}</li>
                ))}
              </ul>
            ) : null}
          </div>
        ) : null}
        {!showDetail ? (
          <div className="p-5">
            <button
              type="button"
              onClick={() => setForceDetail(true)}
              className="btn-secondary w-full justify-center"
            >
              Show detailed pricing evidence
            </button>
          </div>
        ) : (
        <div className="space-y-5 p-5">
          {simplified ? (
            <div className="flex justify-end">
              <button
                type="button"
                onClick={() => setForceDetail(false)}
                className="inline-flex items-center gap-1.5 text-xs font-semibold text-cyan-300 hover:text-cyan-200"
              >
                <ChevronUp className="h-3.5 w-3.5" /> Hide detailed pricing
              </button>
            </div>
          ) : null}
          {pricedGrouped.map((group) => (
            <section key={group.section} className="rounded-md border border-line">
              <div className="border-b border-line bg-slate-50 px-4 py-3">
                <h2 className="text-sm font-semibold text-ink">{group.section}</h2>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-line text-sm">
                  <thead className="bg-white text-left text-xs font-semibold uppercase tracking-wide text-graphite">
                    <tr>
                      <th className="px-4 py-3">Draft line</th>
                      <th className="px-4 py-3">Estimator pricing</th>
                      <th className="px-4 py-3">Risk / margin</th>
                      <th className="px-4 py-3">Subtotal</th>
                      <th className="px-4 py-3">GST</th>
                      <th className="px-4 py-3">Total</th>
                      <th className="px-4 py-3">Evidence</th>
                      <th className="px-4 py-3">Review</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-line bg-white">
                    {group.rows.map((line) => (
                      <tr key={line.id} className="align-top">
                        <td className="min-w-96 px-4 py-4">
                          <div className="font-semibold text-ink">{line.description}</div>
                          <p className="mt-2 text-xs leading-5 text-graphite">
                            <span className="font-semibold text-ink">Pricing: </span>
                            {line.pricing_explanation}
                          </p>
                          <div className="mt-3 grid gap-2 lg:grid-cols-2">
                            <ListBlock title="Assumptions" values={line.assumptions} />
                            <ListBlock title="Exclusions" values={line.exclusions} />
                          </div>
                        </td>
                        <td className="min-w-56 px-4 py-4 text-graphite">
                          <NumberField
                            label={`Quantity ${line.unit ?? ""}`.trim()}
                            value={(lineDrafts[line.id] ?? draftForLine(line)).quantity}
                            disabled={line.excluded_from_pricing}
                            onChange={(value) => updateLineDraft(line, { quantity: value })}
                          />
                          <NumberField
                            label="Unit rate"
                            value={(lineDrafts[line.id] ?? draftForLine(line)).unitRate}
                            disabled={line.excluded_from_pricing}
                            onChange={(value) => updateLineDraft(line, { unitRate: value })}
                          />
                          <textarea
                            value={(lineDrafts[line.id] ?? draftForLine(line)).editReason}
                            disabled={line.excluded_from_pricing}
                            onChange={(event) => updateLineDraft(line, { editReason: event.target.value })}
                            placeholder="Reason required for edits"
                            className="mt-2 min-h-16 w-full rounded-md border border-line px-2 py-1.5 text-xs text-ink disabled:bg-slate-100"
                          />
                          <button
                            type="button"
                            disabled={line.excluded_from_pricing || status === "pricing"}
                            onClick={() => void handleEditLine(line)}
                            className="focus-ring mt-2 rounded-md border border-ink px-2.5 py-1.5 text-xs font-semibold text-ink disabled:cursor-not-allowed disabled:opacity-50"
                          >
                            Save edit
                          </button>
                        </td>
                        <td className="min-w-44 px-4 py-4 text-graphite">
                          <NumberField
                            label="Risk multiplier"
                            value={(lineDrafts[line.id] ?? draftForLine(line)).riskMultiplier}
                            disabled={line.excluded_from_pricing}
                            onChange={(value) => updateLineDraft(line, { riskMultiplier: value })}
                          />
                          <NumberField
                            label="Margin"
                            value={(lineDrafts[line.id] ?? draftForLine(line)).margin}
                            disabled={line.excluded_from_pricing}
                            onChange={(value) => updateLineDraft(line, { margin: value })}
                          />
                        </td>
                        <td className="whitespace-nowrap px-4 py-4 text-graphite">{formatCurrency(line.subtotal_ex_gst)}</td>
                        <td className="whitespace-nowrap px-4 py-4 text-graphite">{formatCurrency(line.gst)}</td>
                        <td className="whitespace-nowrap px-4 py-4 font-semibold text-ink">{formatCurrency(line.total_inc_gst)}</td>
                        <td className="min-w-60 px-4 py-4 text-xs leading-5 text-graphite">
                          {line.source_evidence.length > 3 ? (
                            // Aggregate lines (Site Establishment / Waste) link to many
                            // scope items — summarise rather than list every page.
                            <div className="font-medium text-ink">
                              Linked to {line.source_evidence.length} extracted scope items
                            </div>
                          ) : (
                            <div className="flex flex-wrap items-center gap-1.5">
                              {line.source_pages.map((page) => (
                                <EvidenceChip key={`${line.id}-p${page}`} page={page} />
                              ))}
                            </div>
                          )}
                          {line.source_evidence.length ? (
                            <>
                              <button
                                type="button"
                                onClick={() => toggleEvidence(line.id)}
                                className="mt-2 inline-flex items-center gap-1 font-semibold text-cyan-300 hover:text-cyan-200"
                              >
                                {expandedEvidence.has(line.id) ? (
                                  <ChevronUp className="h-3.5 w-3.5" />
                                ) : (
                                  <ChevronDown className="h-3.5 w-3.5" />
                                )}
                                {expandedEvidence.has(line.id)
                                  ? "Hide"
                                  : line.source_evidence.length > 3
                                    ? "View linked evidence"
                                    : `View full evidence (${line.source_evidence.length})`}
                              </button>
                              {expandedEvidence.has(line.id) ? (
                                <div className="mt-2 space-y-2">
                                  {line.source_evidence.map((evidence) => (
                                    <div
                                      key={`${line.id}-${evidence.register_item_id}`}
                                      className="rounded-md border border-white/10 bg-white/[0.04] p-2"
                                    >
                                      <EvidenceChip page={evidence.page_number} label={evidence.register_item_id} />
                                      <div className="mt-2">{evidence.text}</div>
                                    </div>
                                  ))}
                                </div>
                              ) : null}
                            </>
                          ) : null}
                        </td>
                        <td className="px-4 py-4">
                          <PricingStatus status={line.review_status} />
                          <div className="mt-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
                            {line.approval_status === "ready_for_approval" ? "Ready for approval" : "Not approved"}
                          </div>
                          {!line.excluded_from_pricing ? (
                            <div className="mt-3">
                              <textarea
                                value={(lineDrafts[line.id] ?? draftForLine(line)).reviewReason}
                                onChange={(event) => updateLineDraft(line, { reviewReason: event.target.value })}
                                placeholder="Reason required to resolve review"
                                className="min-h-16 w-full rounded-md border border-line px-2 py-1.5 text-xs text-ink"
                              />
                              <button
                                type="button"
                                disabled={line.review_status === "accepted" || status === "pricing"}
                                onClick={() => void handleResolveReview(line)}
                                className="focus-ring mt-2 rounded-md bg-ink px-2.5 py-1.5 text-xs font-semibold text-white disabled:cursor-not-allowed disabled:opacity-50"
                              >
                                {line.review_status === "accepted" ? "Resolved" : "Resolve review"}
                              </button>
                            </div>
                          ) : null}
                          <EditHistory edits={pricedResult.estimator_edits} lineId={line.id} />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          ))}
        </div>
        )}
      </Panel>
    );
  }

  return (
    <Panel>
      <PanelHeader
        title="Generated quote candidates"
        description="Candidate lines preserve source evidence and review status. Apply your company pricebook to create priced draft lines."
        right={
          <div className="flex items-center gap-2">
            {status === "generating" || status === "pricing" ? <Loader2 className="h-4 w-4 animate-spin text-moss" /> : <RiskChip label={`${result.candidates.length} candidates`} />}
            {attachment ? (
              <button
                type="button"
                onClick={() => void handlePrice()}
                disabled={status === "pricing"}
                className="focus-ring rounded-md bg-ink px-3 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-60"
              >
                {status === "pricing" ? "Pricing..." : "Apply Company Pricebook"}
              </button>
            ) : null}
          </div>
        }
      />
      <div className="border-b border-line bg-slate-50 px-5 py-3 text-sm text-graphite">{message}</div>
      {result.warnings.length ? (
        <div className="border-b border-line bg-amber-50 px-5 py-4">
          <div className="flex items-start gap-2 text-sm font-semibold text-amber-950">
            <AlertTriangle className="mt-0.5 h-4 w-4" />
            Mapping warnings
          </div>
          <ul className="mt-2 list-disc space-y-1 pl-6 text-sm text-amber-950">
            {result.warnings.map((warning, index) => (
              <li key={`${warning.register_item_id ?? "global"}-${index}`}>{warning.message}</li>
            ))}
          </ul>
        </div>
      ) : null}
      <div className="space-y-5 p-5">
        {grouped.map((group) => (
          <section key={group.section} className="rounded-md border border-line">
            <div className="border-b border-line bg-slate-50 px-4 py-3">
              <h2 className="text-sm font-semibold text-ink">{group.section}</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-line text-sm">
                <thead className="bg-white text-left text-xs font-semibold uppercase tracking-wide text-graphite">
                  <tr>
                    <th className="px-4 py-3">Candidate</th>
                    <th className="px-4 py-3">Qty</th>
                    <th className="px-4 py-3">Confidence</th>
                    <th className="px-4 py-3">Evidence</th>
                    <th className="px-4 py-3">Review</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-line bg-white">
                  {group.rows.map((candidate) => (
                    <tr key={candidate.id} className="align-top">
                      <td className="min-w-96 px-4 py-4">
                        <div className="font-semibold text-ink">{candidate.description}</div>
                        <p className="mt-2 text-xs leading-5 text-graphite">
                          <span className="font-semibold text-ink">Reason: </span>
                          {candidate.reason}
                        </p>
                        <div className="mt-3 grid gap-2 lg:grid-cols-2">
                          <ListBlock title="Assumptions" values={candidate.assumptions} />
                          <ListBlock title="Exclusions" values={candidate.exclusions} />
                        </div>
                      </td>
                      <td className="whitespace-nowrap px-4 py-4 text-graphite">
                        {formatNumber(candidate.quantity)} {candidate.unit ?? ""}
                      </td>
                      <td className="whitespace-nowrap px-4 py-4 font-medium text-graphite">{formatPercent(candidate.confidence)}</td>
                      <td className="min-w-60 px-4 py-4 text-xs leading-5 text-graphite">
                        {candidate.source_evidence.length > 3 ? (
                          <div className="font-medium text-ink">
                            Linked to {candidate.source_evidence.length} extracted scope items
                          </div>
                        ) : (
                          <div className="flex flex-wrap items-center gap-1.5">
                            {candidate.source_pages.map((page) => (
                              <EvidenceChip key={`${candidate.id}-p${page}`} page={page} />
                            ))}
                          </div>
                        )}
                        <button
                          type="button"
                          onClick={() => toggleEvidence(candidate.id)}
                          className="mt-2 inline-flex items-center gap-1 font-semibold text-cyan-300 hover:text-cyan-200"
                        >
                          {expandedEvidence.has(candidate.id) ? (
                            <ChevronUp className="h-3.5 w-3.5" />
                          ) : (
                            <ChevronDown className="h-3.5 w-3.5" />
                          )}
                          {expandedEvidence.has(candidate.id) ? "Hide" : "View full evidence"}
                        </button>
                        {expandedEvidence.has(candidate.id) ? (
                          <div className="mt-2 space-y-2">
                            {candidate.source_evidence.map((evidence) => (
                              <div key={`${candidate.id}-${evidence.register_item_id}`} className="rounded-md border border-white/10 bg-white/[0.04] p-2">
                                <EvidenceChip page={evidence.page_number} label={evidence.register_item_id} />
                                <div className="mt-2">{evidence.text}</div>
                              </div>
                            ))}
                          </div>
                        ) : null}
                      </td>
                      <td className="px-4 py-4">
                        <CandidateStatus status={candidate.review_status} />
                        <div className="mt-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
                          {candidate.approval_status === "not_ready" ? "Not approved" : "Approved"}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        ))}
      </div>
    </Panel>
  );
}

function ListBlock({ title, values }: { title: string; values: string[] }) {
  return (
    <div className="rounded-md border border-line bg-slate-50 p-2">
      <div className="text-xs font-semibold uppercase tracking-wide text-moss">{title}</div>
      <ul className="mt-1 list-disc space-y-1 pl-4 text-xs leading-5 text-graphite">
        {values.map((value) => (
          <li key={value}>{value}</li>
        ))}
      </ul>
    </div>
  );
}

function CandidateStatus({ status }: { status: QuoteCandidateReviewStatus }) {
  const className =
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
  return <span className={`inline-flex rounded-full border px-2.5 py-1 text-xs font-semibold ${className}`}>{label}</span>;
}

function PricingStatus({ status }: { status: PricingReviewStatus }) {
  const className =
    status === "review_required"
      ? "border-amber-400 bg-amber-50 text-amber-900"
      : status === "accepted"
        ? "border-emerald-400 bg-emerald-50 text-emerald-900"
      : status === "excluded_from_pricing"
        ? "border-slate-300 bg-white text-slate-700"
        : "border-slate-300 bg-slate-50 text-slate-800";
  const label =
    status === "review_required"
      ? "Review required"
      : status === "accepted"
        ? "Accepted"
      : status === "excluded_from_pricing"
        ? "Excluded"
        : "AI draft";
  return <span className={`inline-flex rounded-full border px-2.5 py-1 text-xs font-semibold ${className}`}>{label}</span>;
}

function TotalBlock({ label, value, strong = false }: { label: string; value: string; strong?: boolean }) {
  return (
    <div className="rounded-md border border-line bg-white p-3">
      <div className="text-xs font-semibold uppercase tracking-wide text-graphite">{label}</div>
      <div className={`mt-1 ${strong ? "text-xl" : "text-lg"} font-semibold text-ink`}>{value}</div>
    </div>
  );
}

function NumberField({
  label,
  value,
  disabled,
  onChange,
}: {
  label: string;
  value: string;
  disabled?: boolean;
  onChange: (value: string) => void;
}) {
  return (
    <label className="mb-2 block text-xs font-semibold uppercase tracking-wide text-graphite">
      {label}
      <input
        type="number"
        step="0.01"
        value={value}
        disabled={disabled}
        onChange={(event) => onChange(event.target.value)}
        className="mt-1 w-full rounded-md border border-line px-2 py-1.5 text-sm font-medium normal-case tracking-normal text-ink disabled:bg-slate-100"
      />
    </label>
  );
}

function ApprovalChecklist({ readiness }: { readiness: ApprovalReadinessResult }) {
  return (
    <div className="border-b border-line bg-white px-5 py-4">
      <div className="mb-3 flex items-center justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold text-ink">Approval checklist</h3>
          <p className="text-xs text-graphite">Export remains blocked until every review gate passes.</p>
        </div>
        <RiskChip label={readiness.approval_status === "ready_for_approval" ? "Ready" : "Blocked"} />
      </div>
      <div className="grid gap-2 md:grid-cols-2">
        {readiness.checks.map((check) => (
          <div key={check.id} className="rounded-md border border-line bg-slate-50 p-3">
            <div className="flex items-center justify-between gap-3">
              <span className="text-sm font-semibold text-ink">{check.label}</span>
              <span
                className={`rounded-full border px-2 py-0.5 text-xs font-semibold ${
                  check.status === "passed"
                    ? "border-emerald-400 bg-emerald-50 text-emerald-900"
                    : "border-amber-400 bg-amber-50 text-amber-900"
                }`}
              >
                {check.status === "passed" ? "Passed" : "Blocked"}
              </span>
            </div>
            <p className="mt-1 text-xs leading-5 text-graphite">{check.details}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

function EditHistory({ edits, lineId }: { edits: PricedQuoteResult["estimator_edits"]; lineId: string }) {
  const lineEdits = edits.filter((edit) => edit.entity_id === lineId).slice(-4).reverse();
  if (!lineEdits.length) {
    return <div className="mt-3 text-xs text-slate-500">No estimator edits recorded.</div>;
  }

  return (
    <div className="mt-3 rounded-md border border-line bg-slate-50 p-2">
      <div className="text-xs font-semibold uppercase tracking-wide text-moss">Edit history</div>
      <ul className="mt-2 space-y-1 text-xs leading-5 text-graphite">
        {lineEdits.map((edit) => (
          <li key={edit.id}>
            <span className="font-semibold text-ink">{edit.field_name}</span>: {String(edit.previous_value)} to {String(edit.new_value)}
            <span className="block text-slate-500">{edit.reason}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function draftForLine(line: PricedQuoteLine): LineDraft {
  return {
    quantity: line.quantity === null ? "" : String(line.quantity),
    unitRate: line.unit_rate === null ? "" : String(line.unit_rate),
    riskMultiplier: String(line.risk_multiplier),
    margin: String(line.margin),
    editReason: "",
    reviewReason: line.review_resolution_reason ?? "",
  };
}

function seedLineDrafts(result: PricedQuoteResult, existing: Record<string, LineDraft>): Record<string, LineDraft> {
  const next: Record<string, LineDraft> = {};
  for (const line of result.lines) {
    next[line.id] = {
      ...draftForLine(line),
      editReason: existing[line.id]?.editReason ?? "",
      reviewReason: line.review_resolution_reason ?? existing[line.id]?.reviewReason ?? "",
    };
  }
  return next;
}

function numberOrNull(value: string): number | null {
  if (!value.trim()) {
    return null;
  }
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}
