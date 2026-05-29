import { getEvidenceLabel } from "@/lib/demo-data";
import { formatNumber, formatPercent } from "@/lib/format";
import type { QuoteWorkup } from "@/lib/types";
import { EvidenceChip, RiskChip, StatusChip } from "./status-chip";

export function RegisterTable({ workup }: { workup: QuoteWorkup }) {
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-white/10 text-sm">
        <thead className="bg-white/[0.04] text-left text-[11px] font-semibold uppercase tracking-[0.12em] text-graphite">
          <tr>
            <th className="px-4 py-3">Register Item</th>
            <th className="px-4 py-3">Extent</th>
            <th className="px-4 py-3">Risk</th>
            <th className="px-4 py-3">Confidence</th>
            <th className="px-4 py-3">Evidence</th>
            <th className="px-4 py-3">Status</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-white/[0.06]">
          {workup.register_items.map((item) => (
            <tr key={item.id} className="align-top transition-colors hover:bg-white/[0.02]">
              <td className="px-4 py-4">
                <div className="font-semibold text-ink">{item.location}</div>
                <div className="mt-1 text-graphite">{item.material}</div>
                <div className="mt-2 text-xs text-slate-500">{item.recommendation}</div>
              </td>
              <td className="whitespace-nowrap px-4 py-4 text-graphite">
                {formatNumber(item.extent_quantity)} {item.extent_unit}
              </td>
              <td className="px-4 py-4">
                <div className="flex flex-wrap gap-1.5">
                  <RiskChip label={item.friability_class} />
                  <RiskChip label={item.asbestos_result} />
                  {item.access_status !== "Accessible" ? <RiskChip label={item.access_status} /> : null}
                  {item.asbestos_result === "Presumed" ? <RiskChip label="Presumed" /> : null}
                </div>
              </td>
              <td className="whitespace-nowrap px-4 py-4 font-medium text-graphite">{formatPercent(item.confidence)}</td>
              <td className="max-w-sm px-4 py-4 text-xs leading-5 text-graphite">
                {item.source_evidence_ids.map((id) => {
                  const evidence = workup.source_evidence.find((entry) => entry.id === id);
                  return (
                    <div key={id} className="space-y-2 rounded-md border border-white/10 bg-white/[0.04] p-2">
                      {evidence ? <EvidenceChip page={evidence.page_number} label={evidence.evidence_type.replace("_", " ")} /> : null}
                      <div>{getEvidenceLabel(workup, id)}</div>
                    </div>
                  );
                })}
              </td>
              <td className="px-4 py-4">
                <StatusChip status={item.review_status} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
