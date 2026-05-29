"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import clsx from "clsx";
import { Building2, ClipboardList, FolderOpen, Gauge, Plus, Settings } from "lucide-react";
import { useActiveOrg } from "@/lib/use-active-org";

export function SidebarNav() {
  const pathname = usePathname();
  const { orgId, session } = useActiveOrg();
  const isPlatformAdmin = session?.role === "platform_admin";

  const items = [
    { href: "/dashboard", label: "Dashboard", icon: Gauge },
    { href: "/jobs", label: "Jobs", icon: FolderOpen },
    { href: "/jobs/new", label: "New job", icon: Plus },
    { href: `/admin/organisations/${orgId}/pricebook`, label: "Pricebook", icon: ClipboardList },
    { href: `/admin/organisations/${orgId}/settings`, label: "Settings", icon: Settings },
    ...(isPlatformAdmin ? [{ href: "/admin", label: "Platform Admin", icon: Building2 }] : []),
  ];

  return (
    <nav className="space-y-1 px-4 py-5">
      {items.map((item) => {
        const Icon = item.icon;
        const active = pathname === item.href || (item.href !== "/jobs/new" && pathname.startsWith(item.href) && item.href !== "/dashboard");
        return (
          <Link
            key={item.href}
            href={item.href}
            className={clsx(
              "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition",
              active
                ? "bg-white/10 text-ink"
                : "text-graphite hover:bg-white/5 hover:text-ink",
            )}
          >
            <Icon className="h-4 w-4" />
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
