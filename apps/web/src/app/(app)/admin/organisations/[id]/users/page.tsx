import { PageHeader } from "@/components/page-header";
import { Panel, PanelHeader } from "@/components/panel";
import { RiskChip } from "@/components/status-chip";

const roles = ["organisation_admin", "estimator", "reviewer", "viewer"];

export default async function OrganisationUsersPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return (
    <div>
      <PageHeader eyebrow="Organisation Admin" title="User management" description={`Assign users and roles inside ${id}.`} actions={<RiskChip label="RBAC" />} />
      <Panel>
        <PanelHeader title="Invite user" description="POST /organisations/{org_id}/users persists role assignments." />
        <form className="grid gap-4 p-5 md:grid-cols-3">
          <input placeholder="name" className="rounded-md border border-line px-3 py-2 text-sm" />
          <input placeholder="email" className="rounded-md border border-line px-3 py-2 text-sm" />
          <select className="rounded-md border border-line px-3 py-2 text-sm">
            {roles.map((role) => (
              <option key={role}>{role}</option>
            ))}
          </select>
        </form>
      </Panel>
    </div>
  );
}
