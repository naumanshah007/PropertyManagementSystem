"use client";

import { Calculator, CheckCircle2, Pencil, Plus, Power, Trash2 } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import {
  activatePricebook,
  addPricebookRule,
  deletePricebookRule,
  listOrganisationPricebooks,
  updatePricebookRule,
} from "@/lib/api";
import { formatCurrency } from "@/lib/format";
import type { CreatePricebookRuleRequest, Pricebook, PricebookRule, UpdatePricebookRuleRequest } from "@/lib/types";
import { Panel, PanelHeader } from "./panel";
import { RiskChip } from "./status-chip";

const defaultRule: CreatePricebookRuleRequest = {
  name: "New pricing rule",
  category: "Class B Removal",
  section: "Class B Removal",
  material_match: "fibre cement sheet",
  class_match: "Class B",
  access_match: "normal",
  pricing_method: "per_sqm",
  unit: "sqm",
  unit_rate: 45,
  risk_multiplier: 1.1,
  margin: 0.2,
  gst_taxable: true,
  minimum_charge: null,
  assumptions: ["Estimator must confirm access and extent before client issue."],
  exclusions: ["Reinstatement and access equipment excluded unless separately listed."],
  review_required: true,
  mandatory: false,
  active: true,
};

export function PricebookManager({ orgId }: { orgId: string }) {
  const [pricebooks, setPricebooks] = useState<Pricebook[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [editingRule, setEditingRule] = useState<PricebookRule | null>(null);
  const [draft, setDraft] = useState<CreatePricebookRuleRequest>(defaultRule);
  const [sampleQuantity, setSampleQuantity] = useState(10);
  const [message, setMessage] = useState("Loading organisation pricebook.");

  const activePricebook = useMemo(() => {
    return pricebooks.find((pricebook) => pricebook.id === selectedId) ?? pricebooks.find((pricebook) => pricebook.active) ?? pricebooks[0];
  }, [pricebooks, selectedId]);

  useEffect(() => {
    void refresh();
  }, [orgId]);

  async function refresh(nextSelectedId?: string) {
    try {
      const result = await listOrganisationPricebooks(orgId);
      setPricebooks(result);
      setSelectedId(nextSelectedId ?? result.find((pricebook) => pricebook.active)?.id ?? result[0]?.id ?? null);
      setMessage(result.length ? "Loaded active organisation pricebook." : "No organisation pricebook exists yet.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Pricebook API unavailable.");
    }
  }

  function startCreate() {
    setEditingRule(null);
    setDraft(defaultRule);
  }

  function startEdit(rule: PricebookRule) {
    setEditingRule(rule);
    setDraft({
      name: rule.name,
      category: rule.category,
      section: rule.section,
      material_match: rule.material_match,
      class_match: rule.class_match,
      access_match: rule.access_match,
      pricing_method: rule.pricing_method,
      unit: rule.unit,
      unit_rate: rule.unit_rate,
      risk_multiplier: rule.risk_multiplier,
      margin: rule.margin,
      gst_taxable: rule.gst_taxable,
      minimum_charge: rule.minimum_charge,
      assumptions: rule.assumptions,
      exclusions: rule.exclusions,
      review_required: rule.review_required,
      mandatory: rule.mandatory,
      active: rule.active,
    });
  }

  async function saveRule() {
    if (!activePricebook) {
      setMessage("No pricebook selected.");
      return;
    }
    try {
      if (editingRule) {
        await updatePricebookRule(orgId, activePricebook.id, editingRule.id, draft as UpdatePricebookRuleRequest);
        setMessage(`Updated rule: ${draft.name}`);
      } else {
        await addPricebookRule(orgId, activePricebook.id, draft);
        setMessage(`Added rule: ${draft.name}`);
      }
      setEditingRule(null);
      await refresh(activePricebook.id);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Pricebook save failed.");
    }
  }

  async function deactivateRule(rule: PricebookRule) {
    if (!activePricebook) {
      return;
    }
    try {
      await deletePricebookRule(orgId, activePricebook.id, rule.id);
      setMessage(`Deactivated rule: ${rule.name}`);
      await refresh(activePricebook.id);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Rule deactivation failed.");
    }
  }

  async function activateSelected() {
    if (!activePricebook) {
      return;
    }
    try {
      await activatePricebook(orgId, activePricebook.id);
      setMessage(`Activated pricebook version ${activePricebook.version}.`);
      await refresh(activePricebook.id);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Pricebook activation failed.");
    }
  }

  const preview = calculatePreview(draft, sampleQuantity);

  return (
    <div className="space-y-6">
      <Panel>
        <PanelHeader
          title="Active pricebook"
          description="Organisation-owned pricing rules used by deterministic quote pricing when this company has an active pricebook."
          right={
            <div className="flex gap-2">
              <button onClick={startCreate} className="focus-ring inline-flex items-center gap-2 rounded-md border border-line bg-white px-3 py-2 text-sm font-semibold text-ink">
                <Plus className="h-4 w-4" />
                Add rule
              </button>
              <button onClick={() => void activateSelected()} className="focus-ring inline-flex items-center gap-2 rounded-md bg-ink px-3 py-2 text-sm font-semibold text-white">
                <Power className="h-4 w-4" />
                Activate
              </button>
            </div>
          }
        />
        <div className="border-b border-line bg-slate-50 px-5 py-3 text-sm text-graphite">{message}</div>
        <div className="grid gap-4 p-5 md:grid-cols-[280px_1fr]">
          <div className="space-y-2">
            {pricebooks.map((pricebook) => (
              <button
                key={pricebook.id}
                onClick={() => setSelectedId(pricebook.id)}
                className={`w-full rounded-md border p-3 text-left text-sm ${
                  activePricebook?.id === pricebook.id ? "border-moss bg-moss/10" : "border-line bg-white"
                }`}
              >
                <div className="font-semibold text-ink">{pricebook.name}</div>
                <div className="mt-1 text-xs text-graphite">Version {pricebook.version}</div>
                <div className="mt-2 flex gap-2">
                  {pricebook.active ? <RiskChip label="active" /> : <RiskChip label="inactive" />}
                  <RiskChip label={`${pricebook.rules.filter((rule) => rule.active).length} rules`} />
                </div>
              </button>
            ))}
          </div>

          <div className="overflow-hidden rounded-md border border-line">
            <table className="min-w-full divide-y divide-line text-sm">
              <thead className="bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-graphite">
                <tr>
                  <th className="px-3 py-3">Rule</th>
                  <th className="px-3 py-3">Match</th>
                  <th className="px-3 py-3">Pricing</th>
                  <th className="px-3 py-3">Controls</th>
                  <th className="px-3 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line bg-white">
                {(activePricebook?.rules ?? []).map((rule) => (
                  <tr key={rule.id} className={!rule.active ? "opacity-55" : undefined}>
                    <td className="px-3 py-3 align-top">
                      <div className="font-semibold text-ink">{rule.name}</div>
                      <div className="mt-1 text-xs text-graphite">{rule.category}</div>
                      <div className="mt-2 flex gap-1.5">
                        {rule.mandatory ? <RiskChip label="mandatory" /> : <RiskChip label="optional" />}
                        {rule.active ? <RiskChip label="active" /> : <RiskChip label="inactive" />}
                      </div>
                    </td>
                    <td className="px-3 py-3 align-top text-xs text-graphite">
                      <div>{rule.material_match || "Any material"}</div>
                      <div className="mt-1">{rule.class_match || "Any class"} / {rule.access_match}</div>
                    </td>
                    <td className="px-3 py-3 align-top text-xs text-graphite">
                      <div>{rule.pricing_method} · {rule.unit}</div>
                      <div className="mt-1">{rule.unit_rate === null ? "No rate" : formatCurrency(rule.unit_rate)}</div>
                      <div className="mt-1">Risk {rule.risk_multiplier} · Margin {(rule.margin * 100).toFixed(0)}%</div>
                    </td>
                    <td className="px-3 py-3 align-top">
                      <div className="flex flex-wrap gap-1.5">
                        {rule.gst_taxable ? <RiskChip label="GST taxable" /> : <RiskChip label="GST exempt" />}
                        {rule.review_required ? <RiskChip label="review required" /> : <RiskChip label="AI draft allowed" />}
                      </div>
                    </td>
                    <td className="px-3 py-3 align-top">
                      <div className="flex justify-end gap-2">
                        <button onClick={() => startEdit(rule)} className="focus-ring rounded-md border border-line p-2 text-ink">
                          <Pencil className="h-4 w-4" />
                        </button>
                        <button onClick={() => void deactivateRule(rule)} className="focus-ring rounded-md border border-line p-2 text-rose-700">
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </Panel>

      <div className="grid gap-6 xl:grid-cols-[1fr_360px]">
        <RuleEditor draft={draft} setDraft={setDraft} editingRule={editingRule} saveRule={saveRule} />
        <Panel>
          <PanelHeader title="Preview calculation" description="Sample deterministic pricing preview before this rule is used on quote candidates." />
          <div className="space-y-4 p-5">
            <label className="block text-sm font-semibold text-ink">
              Sample quantity
              <input
                type="number"
                value={sampleQuantity}
                onChange={(event) => setSampleQuantity(Number(event.target.value))}
                className="mt-2 w-full rounded-md border border-line px-3 py-2 text-sm"
              />
            </label>
            <div className="rounded-md border border-line bg-slate-50 p-4">
              <div className="flex items-center gap-2 text-sm font-semibold text-ink">
                <Calculator className="h-4 w-4 text-moss" />
                Preview
              </div>
              <dl className="mt-4 space-y-2 text-sm">
                <PreviewRow label="Base cost" value={formatCurrency(preview.base)} />
                <PreviewRow label="After risk/margin" value={formatCurrency(preview.subtotal)} />
                <PreviewRow label="GST" value={formatCurrency(preview.gst)} />
                <PreviewRow label="Total" value={formatCurrency(preview.total)} strong />
              </dl>
            </div>
            <div className="rounded-md border border-moss/25 bg-moss/10 p-4 text-sm text-ink">
              <CheckCircle2 className="mb-2 h-4 w-4 text-moss" />
              Active company rules drive pricing. If no active organisation pricebook exists, pricing falls back to the built-in starter rates.
            </div>
          </div>
        </Panel>
      </div>
    </div>
  );
}

function RuleEditor({
  draft,
  setDraft,
  editingRule,
  saveRule,
}: {
  draft: CreatePricebookRuleRequest;
  setDraft: (value: CreatePricebookRuleRequest) => void;
  editingRule: PricebookRule | null;
  saveRule: () => Promise<void>;
}) {
  return (
    <Panel>
      <PanelHeader title={editingRule ? "Edit rule" : "Add rule"} description="Controls how extracted register findings map to deterministic priced quote lines." />
      <div className="grid gap-4 p-5 md:grid-cols-2">
        <TextField label="Rule name" value={draft.name} onChange={(name) => setDraft({ ...draft, name })} />
        <TextField label="Category" value={draft.category} onChange={(category) => setDraft({ ...draft, category, section: category })} />
        <TextField label="Material match" value={draft.material_match ?? ""} onChange={(material_match) => setDraft({ ...draft, material_match })} />
        <SelectField label="Class match" value={draft.class_match ?? ""} onChange={(class_match) => setDraft({ ...draft, class_match: class_match ? (class_match as CreatePricebookRuleRequest["class_match"]) : null })} options={["", "Class A", "Class B", "Unknown"]} />
        <SelectField label="Access match" value={draft.access_match} onChange={(access_match) => setDraft({ ...draft, access_match: access_match as CreatePricebookRuleRequest["access_match"] })} options={["normal", "no-access", "limited-access", "unknown"]} />
        <SelectField label="Pricing method" value={draft.pricing_method} onChange={(pricing_method) => setDraft({ ...draft, pricing_method: pricing_method as CreatePricebookRuleRequest["pricing_method"] })} options={["fixed", "per_sqm", "per_piece", "per_hour", "excluded"]} />
        <TextField label="Unit" value={draft.unit} onChange={(unit) => setDraft({ ...draft, unit })} />
        <NumberField label="Unit rate" value={draft.unit_rate} onChange={(unit_rate) => setDraft({ ...draft, unit_rate })} />
        <NumberField label="Risk multiplier" value={draft.risk_multiplier} onChange={(risk_multiplier) => setDraft({ ...draft, risk_multiplier: risk_multiplier ?? 1 })} />
        <NumberField label="Margin" value={draft.margin} onChange={(margin) => setDraft({ ...draft, margin: margin ?? 0 })} />
        <NumberField label="Minimum charge" value={draft.minimum_charge} onChange={(minimum_charge) => setDraft({ ...draft, minimum_charge })} />
        <div className="grid grid-cols-2 gap-3">
          <CheckField label="GST taxable" checked={draft.gst_taxable} onChange={(gst_taxable) => setDraft({ ...draft, gst_taxable })} />
          <CheckField label="Review required" checked={draft.review_required} onChange={(review_required) => setDraft({ ...draft, review_required })} />
          <CheckField label="Mandatory" checked={draft.mandatory} onChange={(mandatory) => setDraft({ ...draft, mandatory })} />
          <CheckField label="Active" checked={draft.active} onChange={(active) => setDraft({ ...draft, active })} />
        </div>
        <TextArea label="Assumptions" value={draft.assumptions.join("\n")} onChange={(value) => setDraft({ ...draft, assumptions: lines(value) })} />
        <TextArea label="Exclusions" value={draft.exclusions.join("\n")} onChange={(value) => setDraft({ ...draft, exclusions: lines(value) })} />
      </div>
      <div className="border-t border-line px-5 py-4">
        <button onClick={() => void saveRule()} className="focus-ring rounded-md bg-ink px-4 py-2 text-sm font-semibold text-white">
          Save rule
        </button>
      </div>
    </Panel>
  );
}

function TextField({ label, value, onChange }: { label: string; value: string; onChange: (value: string) => void }) {
  return (
    <label className="block text-sm font-semibold text-ink">
      {label}
      <input value={value} onChange={(event) => onChange(event.target.value)} className="mt-2 w-full rounded-md border border-line px-3 py-2 text-sm font-normal" />
    </label>
  );
}

function NumberField({ label, value, onChange }: { label: string; value: number | null; onChange: (value: number | null) => void }) {
  return (
    <label className="block text-sm font-semibold text-ink">
      {label}
      <input
        type="number"
        value={value ?? ""}
        onChange={(event) => onChange(event.target.value === "" ? null : Number(event.target.value))}
        className="mt-2 w-full rounded-md border border-line px-3 py-2 text-sm font-normal"
      />
    </label>
  );
}

function SelectField({ label, value, options, onChange }: { label: string; value: string; options: string[]; onChange: (value: string) => void }) {
  return (
    <label className="block text-sm font-semibold text-ink">
      {label}
      <select value={value} onChange={(event) => onChange(event.target.value)} className="mt-2 w-full rounded-md border border-line px-3 py-2 text-sm font-normal">
        {options.map((option) => (
          <option key={option} value={option}>
            {option || "Any"}
          </option>
        ))}
      </select>
    </label>
  );
}

function TextArea({ label, value, onChange }: { label: string; value: string; onChange: (value: string) => void }) {
  return (
    <label className="block text-sm font-semibold text-ink md:col-span-2">
      {label}
      <textarea value={value} onChange={(event) => onChange(event.target.value)} rows={4} className="mt-2 w-full rounded-md border border-line px-3 py-2 text-sm font-normal" />
    </label>
  );
}

function CheckField({ label, checked, onChange }: { label: string; checked: boolean; onChange: (value: boolean) => void }) {
  return (
    <label className="flex items-center gap-2 rounded-md border border-line px-3 py-2 text-sm font-semibold text-ink">
      <input type="checkbox" checked={checked} onChange={(event) => onChange(event.target.checked)} />
      {label}
    </label>
  );
}

function PreviewRow({ label, value, strong }: { label: string; value: string; strong?: boolean }) {
  return (
    <div className={`flex justify-between ${strong ? "font-semibold text-ink" : "text-graphite"}`}>
      <dt>{label}</dt>
      <dd>{value}</dd>
    </div>
  );
}

function calculatePreview(rule: CreatePricebookRuleRequest, quantity: number) {
  if (rule.pricing_method === "excluded") {
    return { base: 0, subtotal: 0, gst: 0, total: 0 };
  }
  const pricedQuantity = rule.pricing_method === "fixed" ? 1 : quantity;
  const base = pricedQuantity * (rule.unit_rate ?? 0);
  const subtotalBeforeMinimum = base * rule.risk_multiplier * (1 + rule.margin);
  const subtotal = Math.max(subtotalBeforeMinimum, rule.minimum_charge ?? 0);
  const gst = rule.gst_taxable ? subtotal * 0.15 : 0;
  return {
    base,
    subtotal,
    gst,
    total: subtotal + gst,
  };
}

function lines(value: string) {
  return value
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);
}
