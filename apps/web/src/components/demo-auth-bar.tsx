"use client";

import { LogOut } from "lucide-react";
import { useEffect, useState } from "react";
import { clearDemoSession, readDemoSession } from "@/lib/demo-auth";
import type { DemoAuthSession } from "@/lib/types";

export function DemoAuthBar() {
  const [session, setSession] = useState<DemoAuthSession | null>(null);

  useEffect(() => {
    setSession(readDemoSession());
  }, []);

  function logout() {
    clearDemoSession();
    window.location.href = "/login";
  }

  if (!session) {
    return (
      <a href="/login" className="focus-ring rounded-md border border-line bg-white px-3 py-2 text-sm font-semibold text-ink shadow-sm hover:bg-slate-50">
        Demo login
      </a>
    );
  }

  return (
    <div className="flex items-center gap-3">
      <div className="text-right">
        <div className="text-sm font-semibold text-ink">{session.name}</div>
        <div className="text-xs text-graphite">{session.role}</div>
      </div>
      <button onClick={logout} className="focus-ring rounded-md border border-line bg-white p-2 text-ink shadow-sm hover:bg-slate-50" title="Logout">
        <LogOut className="h-4 w-4" />
      </button>
    </div>
  );
}
