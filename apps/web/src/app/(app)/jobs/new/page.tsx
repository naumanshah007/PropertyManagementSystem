"use client";

import { useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, FileUp, Loader2 } from "lucide-react";
import { PageHeader } from "@/components/page-header";
import { Panel, PanelHeader } from "@/components/panel";
import { createJob } from "@/lib/api";
import { useActiveOrg } from "@/lib/use-active-org";

export default function NewJobPage() {
  const router = useRouter();
  const { orgId, session } = useActiveOrg();
  const inputRef = useRef<HTMLInputElement>(null);

  const [file, setFile] = useState<File | null>(null);
  const [clientName, setClientName] = useState("");
  const [siteAddress, setSiteAddress] = useState("");
  const [jobReference, setJobReference] = useState("");
  const [status, setStatus] = useState<"idle" | "creating" | "error">("idle");
  const [message, setMessage] = useState<string | null>(null);

  async function submit() {
    if (!file) {
      setMessage("Select a survey PDF to continue.");
      return;
    }
    setStatus("creating");
    setMessage("Uploading and classifying survey…");
    try {
      const job = await createJob(orgId, {
        file,
        client_name: clientName.trim() || undefined,
        site_address: siteAddress.trim() || undefined,
        job_reference: jobReference.trim() || undefined,
        created_by: session?.email,
      });
      // Workspace auto-runs processing for freshly uploaded jobs.
      router.push(`/jobs/${job.id}`);
    } catch (e) {
      setStatus("error");
      setMessage(e instanceof Error ? e.message : "Failed to create job.");
    }
  }

  return (
    <div>
      <PageHeader
        eyebrow="New job"
        title="Upload a survey"
        description="Drop in an asbestos survey PDF and add the client details. We classify the survey, extract the register, and price a draft quote automatically."
      />

      <div className="grid gap-6 xl:grid-cols-[1fr_0.8fr]">
        <Panel>
          <PanelHeader title="Survey document" description="PDF up to 50 MB. Management, refurbishment, or demolition surveys." />
          <div className="p-5">
            <button
              type="button"
              onClick={() => inputRef.current?.click()}
              onDragOver={(e) => e.preventDefault()}
              onDrop={(e) => {
                e.preventDefault();
                const dropped = e.dataTransfer.files?.[0];
                if (dropped) setFile(dropped);
              }}
              className="flex min-h-56 w-full flex-col items-center justify-center rounded-xl border-2 border-dashed border-white/15 bg-white/[0.03] px-6 py-8 text-center transition hover:border-cyan-300/40 hover:bg-white/[0.05]"
            >
              <input
                ref={inputRef}
                type="file"
                accept="application/pdf,.pdf"
                className="hidden"
                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              />
              <div className="grid h-12 w-12 place-items-center rounded-xl border border-white/10 bg-white/[0.04] text-cyan-300">
                <FileUp className="h-6 w-6" />
              </div>
              <div className="mt-4 text-base font-semibold text-ink">
                {file ? file.name : "Click or drop a survey PDF"}
              </div>
              <p className="mt-1.5 text-sm text-graphite">
                {file ? `${(file.size / 1_048_576).toFixed(1)} MB selected` : "We'll auto-detect the survey type"}
              </p>
            </button>
          </div>
        </Panel>

        <Panel>
          <PanelHeader title="Client details" description="Optional now — shown on the exported quote and the jobs list." />
          <div className="space-y-4 p-5">
            <Field label="Client name" value={clientName} onChange={setClientName} placeholder="e.g. Tauraroa Area School" />
            <Field label="Site address" value={siteAddress} onChange={setSiteAddress} placeholder="e.g. Northland, New Zealand" />
            <Field label="Job reference" value={jobReference} onChange={setJobReference} placeholder="Optional internal reference" />

            <button onClick={() => void submit()} disabled={status === "creating"} className="btn-primary w-full py-2.5 disabled:opacity-60">
              {status === "creating" ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Creating job…
                </>
              ) : (
                <>
                  Create job
                  <ArrowRight className="h-4 w-4" />
                </>
              )}
            </button>
            {message ? (
              <p className={status === "error" ? "text-sm text-rose-200" : "text-sm text-graphite"}>{message}</p>
            ) : null}
          </div>
        </Panel>
      </div>
    </div>
  );
}

function Field({
  label,
  value,
  onChange,
  placeholder,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
}) {
  return (
    <label className="block text-[11px] font-semibold uppercase tracking-[0.16em] text-graphite">
      {label}
      <input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="mt-1.5 w-full rounded-lg border border-white/10 bg-night-900/60 px-3 py-2.5 text-sm normal-case tracking-normal text-ink outline-none transition focus:border-cyan-300/50 focus:ring-2 focus:ring-cyan-300/30"
      />
    </label>
  );
}
