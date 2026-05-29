import { Plus } from "lucide-react";
import Link from "next/link";
import { PageHeader } from "@/components/page-header";
import { Panel, PanelHeader } from "@/components/panel";
import { RiskChip } from "@/components/status-chip";

const organisations = [
  {
    id: "org-demo-tracequote",
    name: "TraceQuote Demo Organisation",
    role: "platform_admin",
    status: "active",
  },
  {
    id: "org-demo-asbestos-services",
    name: "Demo Asbestos Services Ltd",
    role: "organisation_admin",
    status: "active",
  },
];

export default function OrganisationsPage() {
  return (
    <div>
      <PageHeader
        eyebrow="Platform Admin"
        title="Organisations"
        description="Each organisation owns its users, settings, pricebooks, documents, quote lines, edits, and exports."
        actions={
          <Link href="/admin/organisations/new" className="focus-ring inline-flex items-center gap-2 rounded-md bg-ink px-4 py-2 text-sm font-semibold text-white">
            <Plus className="h-4 w-4" />
            Create organisation
          </Link>
        }
      />
      <Panel>
        <PanelHeader title="Organisation directory" description="Platform admin view across seeded local demo organisations." />
        <div className="divide-y divide-line">
          {organisations.map((org) => (
            <div key={org.id} className="grid gap-3 px-5 py-4 md:grid-cols-[1fr_auto] md:items-center">
              <div>
                <div className="font-semibold text-ink">{org.name}</div>
                <div className="mt-1 text-sm text-graphite">{org.id}</div>
              </div>
              <div className="flex gap-2">
                <RiskChip label={org.status} />
                <Link href={`/admin/organisations/${org.id}/settings`} className="focus-ring rounded-md border border-line bg-white px-3 py-2 text-sm font-semibold text-ink">
                  Manage
                </Link>
              </div>
            </div>
          ))}
        </div>
      </Panel>
    </div>
  );
}
