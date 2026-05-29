"use client";

import { useCallback, useEffect, useState } from "react";
import { Sparkles } from "lucide-react";
import { getMagicSummary } from "@/lib/api";
import { formatNumber, formatPercent } from "@/lib/format";
import type { MagicExtractionSummary } from "@/lib/types";
import { readWorkupAttachment, type WorkupDocumentAttachment } from "@/lib/workup-documents";
import { Panel, PanelHeader } from "./panel";
import { RiskChip } from "./status-chip";

export function MagicExtractionPanel({ workupId }: { workupId: string }) {
  const [attachment, setAttachment] = useState<WorkupDocumentAttachment | null>(null);
  const [summary, setSummary] = useState<MagicExtractionSummary | null>(null);
  const [message, setMessage] = useState("Loading extracted intelligence…");

  useEffect(() => {
    const attached = readWorkupAttachment(workupId);
    setAttachment(attached);
    function handleAttached(event: Event) {
      const custom = event as CustomEvent<WorkupDocumentAttachment>;
      if (custom.detail.workupId === workupId) {
        setAttachment(custom.detail);
        setSummary(null);
      }
    }
    window.addEventListener("tracequote:workup-document-attached", handleAttached);
    return () => window.removeEventListener("tracequote:workup-document-attached", handleAttached);
  }, [workupId]);

  const loadSummary = useCallback(async () => {
    if (!attachment) {
      return;
    }
    try {
      const result = await getMagicSummary(attachment.documentId);
      setSummary(result);
      setMessage("Structured intelligence extracted from this survey — entities, classifications, and pricing signals.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Extracted intelligence is not ready yet.");
    }
  }, [attachment]);

  // Auto-load once a document is attached — no manual reveal step in the flow.
  useEffect(() => {
    if (attachment) {
      void loadSummary();
    }
  }, [attachment, loadSummary]);

  return (
    <Panel className="mb-6">
      <PanelHeader
        title="Extracted intelligence"
        description="What TraceQuote AI understood from this survey."
        right={
          attachment ? (
            <button onClick={() => void loadSummary()} className="btn-secondary">
              <Sparkles className="h-4 w-4" />
              Refresh
            </button>
          ) : (
            <RiskChip label="Awaiting upload" />
          )
        }
      />
      <div className="border-b border-white/10 bg-white/[0.03] px-5 py-3 text-sm text-graphite">{message}</div>
      {summary ? (
        <div className="space-y-5 p-5">
          <div className="grid gap-3 md:grid-cols-4">
            <Metric label="Survey type" value={summary.survey_type} />
            <Metric label="Pages parsed" value={String(summary.total_pages_parsed)} />
            <Metric label="Extracted rows" value={String(summary.register_items_extracted)} />
            <Metric label="Quote-ready" value={String(summary.quote_ready_items)} />
            <Metric label="Needs review" value={String(summary.review_required_items)} />
            <Metric label="Reference-only" value={String(summary.reference_only_items)} />
            <Metric label="Priced lines" value={String(summary.priced_lines_generated)} />
            <Metric label="Class A" value={String(summary.class_a_items)} />
            <Metric label="Class B" value={String(summary.class_b_items)} />
            <Metric label="No access" value={String(summary.no_access_items)} />
            <Metric label="Limited access" value={String(summary.limited_access_items)} />
            <Metric label="NAD/excluded" value={String(summary.nad_excluded_items)} />
            <Metric label="Extracted sqm" value={formatNumber(summary.total_extracted_sqm)} />
            <Metric label="Avg confidence" value={formatPercent(summary.confidence_summary.average ?? 0)} />
          </div>

          <div>
            <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-ink">
              <Sparkles className="h-4 w-4 text-cyan-300" />
              Magic Entities Detected
            </div>
            <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
              {Object.entries(summary.magic_entities).map(([group, values]) => (
                <div
                  key={group}
                  className="rounded-xl border border-white/10 bg-white/[0.04] p-4 backdrop-blur-sm"
                >
                  <div className="text-[11px] font-semibold uppercase tracking-[0.14em] text-cyan-300">
                    {group.replace("_", " ")}
                  </div>
                  <div className="mt-3 flex flex-wrap gap-1.5">
                    {values.slice(0, 10).map((value) => (
                      <RiskChip key={`${group}-${value}`} label={value} />
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      ) : null}
    </Panel>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="group relative overflow-hidden rounded-xl border border-white/10 bg-night-800/60 p-4 backdrop-blur-sm transition hover:border-cyan-300/30">
      <div className="pointer-events-none absolute -right-10 -top-10 h-28 w-28 rounded-full bg-gradient-to-br from-cyan-400/20 to-transparent blur-2xl" />
      <div className="relative text-[11px] font-semibold uppercase tracking-[0.14em] text-graphite">{label}</div>
      <div className="relative mt-1 truncate text-lg font-semibold text-ink">{value}</div>
    </div>
  );
}
