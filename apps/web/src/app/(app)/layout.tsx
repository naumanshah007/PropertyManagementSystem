import type { ReactNode } from "react";
import { AuthedShell } from "@/components/authed-shell";

export default function AppGroupLayout({ children }: { children: ReactNode }) {
  return <AuthedShell>{children}</AuthedShell>;
}
