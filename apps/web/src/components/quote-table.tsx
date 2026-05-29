import clsx from "clsx";
import { getEvidenceLabel } from "@/lib/demo-data";
import { formatCurrency, formatNumber, formatPercent } from "@/lib/format";
import type { QuoteWorkup } from "@/lib/types";
import { EvidenceChip, StatusChip } from "./status-chip";

export function QuoteTable({ workup }: { workup: QuoteWorkup }) {
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-white/10 text-sm">
        <thead className="bg-white/[0.04] text-left text-[11px] font-semibold uppercase tracking-[0.12em] text-graphite">
          <tr>
            <th className="px-4 py-3">Line Item</th>
            <th className="px-4 py-3">Qty</th>
            <th className="px-4 py-3">Unit</th>
            <th className="px-4 py-3">Rate</th>
            <th className="px-4 py-3">Base</th>
            <th className="px-4 py-3">Risk</th>
            <th className="px-4 py-3">Margin</th>
            <th className="px-4 py-3">Ex GST</th>
            <th className="px-4 py-3">GST</th>
            <th className="px-4 py-3">Total</th>
            <th className="px-4 py-3">Evidence</th>
            <th className="px-4 py-3">Review</th>
            <th className="px-4 py-3">Approval</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-white/[0.06]">
          {workup.quote_lines.map((line) => {
            const exGst =
              line.base_cost === null ? null : line.base_cost * line.risk_multiplier * (1 + line.margin);

            return (
              <tr
                key={line.id}
                className={clsx(
                  "align-top transition-colors",
                  line.review_status === "review_required" ? "bg-amber-400/[0.06]" : "hover:bg-white/[0.02]",
                )}
              >
                <td className="min-w-80 border-l-4 border-l-transparent px-4 py-4 data-[review=true]:border-l-amber-400" data-review={line.review_status === "review_required"}>
                  <div className="inline-flex rounded-md border border-cyan-300/20 bg-cyan-400/10 px-2 py-1 text-xs font-semibold uppercase tracking-wide text-cyan-200">
                    {line.section}
                  </div>
                  <div className="mt-1 font-semibold text-ink">{line.description}</div>
                  <div className="mt-2 rounded-md border border-white/10 bg-white/[0.04] p-2 text-xs leading-5 text-graphite">
                    <span className="font-semibold text-ink">Pricing logic: </span>
                    {line.why}
                  </div>
                </td>
                <td className="whitespace-nowrap px-4 py-4 text-graphite">{formatNumber(line.quantity)}</td>
                <td className="whitespace-nowrap px-4 py-4 text-graphite">{line.unit}</td>
                <td className="whitespace-nowrap px-4 py-4 text-graphite">{formatCurrency(line.unit_rate)}</td>
                <td className="whitespace-nowrap px-4 py-4 text-graphite">{formatCurrency(line.base_cost)}</td>
                <td className="whitespace-nowrap px-4 py-4 text-graphite">{line.risk_multiplier.toFixed(2)}x</td>
                <td className="whitespace-nowrap px-4 py-4 text-graphite">{formatPercent(line.margin)}</td>
                <td className="whitespace-nowrap px-4 py-4 font-medium text-ink">{formatCurrency(exGst)}</td>
                <td className="whitespace-nowrap px-4 py-4 text-graphite">{formatCurrency(line.gst)}</td>
                <td className="whitespace-nowrap px-4 py-4 font-semibold text-ink">{formatCurrency(line.total)}</td>
                <td className="min-w-72 px-4 py-4 text-xs leading-5 text-graphite">
                  <div className="space-y-2">
                    {line.source_evidence_ids.map((id) => {
                      const evidence = workup.source_evidence.find((entry) => entry.id === id);
                      return (
                        <div key={id} className="rounded-md border border-white/10 bg-white/[0.04] p-2">
                          {evidence ? <EvidenceChip page={evidence.page_number} label="quote source" /> : null}
                          <div className="mt-2">{getEvidenceLabel(workup, id)}</div>
                        </div>
                      );
                    })}
                  </div>
                </td>
                <td className="px-4 py-4">
                  <StatusChip status={line.review_status} />
                </td>
                <td className="px-4 py-4">
                  <span className="inline-flex whitespace-nowrap rounded-full border border-white/15 bg-white/5 px-2.5 py-1 text-xs font-semibold text-graphite">
                    {line.approval_status === "not_ready" ? "Not ready" : line.approval_status}
                  </span>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
