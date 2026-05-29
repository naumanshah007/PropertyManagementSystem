"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";
import { AppShell } from "./app-shell";
import { readDemoSession } from "@/lib/demo-auth";

/**
 * Client-side auth gate for the app route group.
 * - /login renders bare (no chrome, no auth needed).
 * - Every other route requires a stored session; unauthenticated users are
 *   bounced to /login. (The API layer also enforces this server-side — this is
 *   just for a clean UX, not the security boundary.)
 */
export function AuthedShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const isLogin = pathname?.startsWith("/login") ?? false;
  const [state, setState] = useState<"checking" | "authed" | "anon">("checking");

  useEffect(() => {
    if (isLogin) return;
    if (readDemoSession()) {
      setState("authed");
    } else {
      setState("anon");
      router.replace("/login");
    }
  }, [isLogin, pathname, router]);

  if (isLogin) {
    return <div className="min-h-screen bg-night-900 px-5 py-10">{children}</div>;
  }

  if (state !== "authed") {
    return (
      <div className="flex min-h-screen items-center justify-center bg-night-900 text-graphite">
        <Loader2 className="h-5 w-5 animate-spin text-cyan-300" />
      </div>
    );
  }

  return <AppShell>{children}</AppShell>;
}
