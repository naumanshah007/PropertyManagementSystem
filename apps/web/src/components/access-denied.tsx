import Link from "next/link";
import { ShieldX } from "lucide-react";
import { Panel } from "./panel";

export function AccessDenied({
  message = "You don't have permission to view this. Ask an administrator if you think this is a mistake.",
}: {
  message?: string;
}) {
  return (
    <Panel className="flex flex-col items-center justify-center px-6 py-16 text-center">
      <div className="grid h-14 w-14 place-items-center rounded-2xl border border-rose-300/30 bg-rose-400/10 text-rose-300">
        <ShieldX className="h-7 w-7" />
      </div>
      <h2 className="mt-5 text-lg font-semibold text-ink">Access denied</h2>
      <p className="mt-2 max-w-sm text-sm leading-6 text-graphite">{message}</p>
      <Link href="/dashboard" className="btn-secondary mt-6">
        Back to dashboard
      </Link>
    </Panel>
  );
}
