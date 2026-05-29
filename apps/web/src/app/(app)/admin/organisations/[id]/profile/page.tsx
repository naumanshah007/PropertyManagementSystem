import { PageHeader } from "@/components/page-header";
import { Panel, PanelHeader } from "@/components/panel";
import { RiskChip } from "@/components/status-chip";

export default async function OrganisationProfilePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return (
    <div>
      <PageHeader eyebrow="Organisation Admin" title="Company profile and branding" description={`Branding placeholder for ${id}.`} actions={<RiskChip label="Branding" />} />
      <Panel>
        <PanelHeader title="Profile fields" description="Company profile data will feed quote templates and exports." />
        <div className="grid gap-4 p-5 md:grid-cols-2">
          {["Legal name", "Trading name", "Email", "Phone", "Website", "Address", "Logo"].map((field) => (
            <label key={field} className="text-xs font-semibold uppercase tracking-wide text-graphite">
              {field}
              <input className="mt-1 w-full rounded-md border border-line px-3 py-2 text-sm normal-case tracking-normal text-ink" />
            </label>
          ))}
        </div>
      </Panel>
    </div>
  );
}
