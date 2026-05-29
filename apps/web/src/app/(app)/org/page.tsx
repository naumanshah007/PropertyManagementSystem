import { Building2, ClipboardList, Settings, Users } from "lucide-react";
import Link from "next/link";
import { PageHeader } from "@/components/page-header";
import { Panel } from "@/components/panel";
import { RiskChip } from "@/components/status-chip";

export default function OrganisationHomePage() {
  return (
    <div>
      <PageHeader
        eyebrow="Organisation Admin"
        title="Demo Asbestos Services Ltd"
        description="Organisation admins manage company users, settings, pricebooks, branding, and estimator workflows."
        actions={<RiskChip label="TraceQuote Demo" />}
      />
      <div className="grid gap-4 md:grid-cols-2">
        {[
          { href: "/admin/organisations/org-demo-asbestos-services/users", title: "Users", icon: Users },
          { href: "/admin/organisations/org-demo-asbestos-services/settings", title: "Settings", icon: Settings },
          { href: "/admin/organisations/org-demo-asbestos-services/pricebook", title: "Pricebook", icon: ClipboardList },
          { href: "/workups", title: "Estimator workups", icon: Building2 },
        ].map((item) => {
          const Icon = item.icon;
          return (
            <Link href={item.href} key={item.href} className="group">
              <Panel className="p-5 transition group-hover:border-moss">
                <Icon className="h-5 w-5 text-moss" />
                <div className="mt-4 font-semibold text-ink">{item.title}</div>
                <p className="mt-1 text-sm text-graphite">Demo organisation scoped view.</p>
              </Panel>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
