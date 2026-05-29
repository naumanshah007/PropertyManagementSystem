import { ArrowRight, Building2, ShieldCheck, Users } from "lucide-react";
import Link from "next/link";
import type { ReactNode } from "react";
import { PageHeader } from "@/components/page-header";
import { Panel, PanelHeader } from "@/components/panel";
import { RiskChip } from "@/components/status-chip";

export default function PlatformAdminPage() {
  return (
    <div>
      <PageHeader
        eyebrow="Platform Admin"
        title="Multi-organisation control plane"
        description="Create organisations, manage SaaS boundaries, and keep estimator workflows separated by company."
        actions={<RiskChip label="SaaS foundation" />}
      />

      <div className="grid gap-4 md:grid-cols-3">
        <AdminMetric title="Organisations" value="Company boundary" icon={<Building2 className="h-5 w-5" />} />
        <AdminMetric title="Users and roles" value="RBAC ready" icon={<Users className="h-5 w-5" />} />
        <AdminMetric title="Pricebooks" value="Per organisation" icon={<ShieldCheck className="h-5 w-5" />} />
      </div>

      <div className="mt-6 grid gap-4 md:grid-cols-2">
        {[
          { title: "Organisation list", href: "/admin/organisations", detail: "Create and inspect customer organisations." },
          { title: "Create organisation", href: "/admin/organisations/new", detail: "Start a new company workspace." },
          { title: "Demo settings", href: "/admin/organisations/org-demo-asbestos-services/settings", detail: "Manage the seeded asbestos demo company settings." },
          { title: "Demo users", href: "/admin/organisations/org-demo-asbestos-services/users", detail: "Assign estimator, reviewer, and admin roles." },
          { title: "Demo pricebook", href: "/admin/organisations/org-demo-asbestos-services/pricebook", detail: "Inspect the demo company pricebook." },
          { title: "Demo profile", href: "/admin/organisations/org-demo-asbestos-services/profile", detail: "Company branding placeholder for TraceQuote Demo." },
        ].map((item) => (
          <Link key={item.href} href={item.href} className="group">
            <Panel className="h-full p-5 transition group-hover:border-moss">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <div className="font-semibold text-ink">{item.title}</div>
                  <p className="mt-1 text-sm leading-5 text-graphite">{item.detail}</p>
                </div>
                <ArrowRight className="h-4 w-4 text-moss" />
              </div>
            </Panel>
          </Link>
        ))}
      </div>

      <Panel className="mt-6">
        <PanelHeader title="Role model" description="Phase 8 defines the SaaS role boundaries used by later auth work." />
        <div className="grid gap-3 p-5 md:grid-cols-5">
          {["platform_admin", "organisation_admin", "estimator", "reviewer", "viewer"].map((role) => (
            <div key={role} className="rounded-md border border-line bg-slate-50 p-3 text-sm font-semibold text-ink">
              {role}
            </div>
          ))}
        </div>
      </Panel>
    </div>
  );
}

function AdminMetric({ title, value, icon }: { title: string; value: string; icon: ReactNode }) {
  return (
    <Panel className="p-5">
      <div className="flex items-center gap-3 text-moss">{icon}</div>
      <div className="mt-4 text-sm font-semibold uppercase tracking-wide text-graphite">{title}</div>
      <div className="mt-1 text-xl font-semibold text-ink">{value}</div>
    </Panel>
  );
}
