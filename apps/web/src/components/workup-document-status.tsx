"use client";

import type React from "react";
import { useEffect, useState } from "react";
import { CheckCircle2, Clock, Database, FileText } from "lucide-react";
import { readWorkupAttachment, type WorkupDocumentAttachment } from "@/lib/workup-documents";
import { Panel, PanelHeader } from "./panel";
import { RiskChip } from "./status-chip";

export function WorkupDocumentStatus({ workupId }: { workupId: string }) {
  const [attachment, setAttachment] = useState<WorkupDocumentAttachment | null>(null);

  useEffect(() => {
    setAttachment(readWorkupAttachment(workupId));

    function handleAttached(event: Event) {
      const custom = event as CustomEvent<WorkupDocumentAttachment>;
      if (custom.detail.workupId === workupId) {
        setAttachment(custom.detail);
      }
    }

    window.addEventListener("tracequote:workup-document-attached", handleAttached);
    return () => window.removeEventListener("tracequote:workup-document-attached", handleAttached);
  }, [workupId]);

  return (
    <Panel>
      <PanelHeader
        title="Parsed document attachment"
        description="POC frontend state linking the latest parsed PDF metadata to this workup."
        right={attachment ? <RiskChip label="Parsed" /> : <RiskChip label="Awaiting upload" />}
      />
      {attachment ? (
        <div className="grid gap-3 p-5 md:grid-cols-5">
          <StatusMetric icon={<FileText className="h-4 w-4" />} label="File name" value={attachment.fileName} />
          <StatusMetric icon={<Database className="h-4 w-4" />} label="Pages" value={String(attachment.pageCount)} />
          <StatusMetric icon={<Database className="h-4 w-4" />} label="Parser" value={attachment.parserVersion} />
          <StatusMetric icon={<CheckCircle2 className="h-4 w-4" />} label="OCR status" value={attachment.ocrStatus.replace("_", " ")} />
          <StatusMetric icon={<Clock className="h-4 w-4" />} label="Uploaded" value={new Date(attachment.uploadedAt).toLocaleString("en-NZ")} />
        </div>
      ) : (
        <div className="p-5 text-sm leading-6 text-graphite">
          Upload a PDF from this workup to attach parsed document metadata. Existing deterministic quote demo data remains unchanged.
        </div>
      )}
    </Panel>
  );
}

function StatusMetric({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <div className="rounded-md border border-line bg-slate-50 p-3">
      <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-moss">
        {icon}
        {label}
      </div>
      <div className="mt-2 truncate text-sm font-semibold text-ink">{value}</div>
    </div>
  );
}
