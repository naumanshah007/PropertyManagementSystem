"use client";

import { useEffect, useState } from "react";
import { getActiveOrgId } from "./api";
import { readDemoSession } from "./demo-auth";
import type { DemoAuthSession } from "./types";

/**
 * The org the current operator works within, resolved from the logged-in
 * session. Platform admins (no org) fall back to the seeded demo org so the
 * workflow stays operable. `ready` flips true once the client has read
 * localStorage (avoids SSR/first-paint fl/null mismatches).
 */
export function useActiveOrg(): { orgId: string; session: DemoAuthSession | null; ready: boolean } {
  const [session, setSession] = useState<DemoAuthSession | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    setSession(readDemoSession());
    setReady(true);
  }, []);

  return { orgId: getActiveOrgId(session?.organisation_id), session, ready };
}
