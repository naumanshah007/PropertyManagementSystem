import { Bot, ArrowRight } from "lucide-react";
import Link from "next/link";
import { PageHeader } from "@/components/page-header";
import { Panel, PanelHeader } from "@/components/panel";
import { RiskChip } from "@/components/status-chip";

export default async function OrganisationSettingsPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return (
    <div className="space-y-6">
      <PageHeader eyebrow="Organisation Admin" title="Organisation settings" description={`Settings boundary for ${id}.`} actions={<RiskChip label="Org scoped" />} />

      <Link
        href={`/admin/organisations/${id}/llm-settings`}
        className="focus-ring block rounded-lg border border-line bg-white p-5 shadow-sm hover:border-moss"
      >
        <div className="flex items-start gap-4">
          <div className="rounded-md bg-moss/10 p-2">
            <Bot className="h-5 w-5 text-moss" />
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <h3 className="font-semibold text-ink">LLM register extraction</h3>
              <RiskChip label="Phase C" />
            </div>
            <p className="mt-1 text-sm text-graphite">
              Choose between Anthropic Claude, OpenAI, and Google Gemini for survey-to-register extraction. Configure the API key for your organisation.
            </p>
          </div>
          <ArrowRight className="h-5 w-5 text-graphite" />
        </div>
      </Link>

      <Panel>
        <PanelHeader title="Quote and compliance defaults" description="Stored per organisation through /organisations/{org_id}/settings." />
        <div className="grid gap-4 p-5 md:grid-cols-2">
          <Setting label="GST rate" value="0.15" />
          <Setting label="Default margin" value="0.20" />
          <Setting label="Currency" value="NZD" />
          <Setting label="Quote prefix" value="TQ" />
          <Setting label="Class A review required" value="true" />
          <Setting label="No-access review required" value="true" />
        </div>
      </Panel>
    </div>
  );
}

function Setting({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-line bg-slate-50 p-4">
      <div className="text-xs font-semibold uppercase tracking-wide text-moss">{label}</div>
      <div className="mt-1 text-sm font-semibold text-ink">{value}</div>
    </div>
  );
}
