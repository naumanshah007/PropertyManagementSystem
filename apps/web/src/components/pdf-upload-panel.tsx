"use client";

import { useRef, useState } from "react";
import { CheckCircle2, FileUp, Loader2, ServerCrash } from "lucide-react";
import { uploadPdf } from "@/lib/api";
import type { ParsedDocument } from "@/lib/types";
import {
  LAST_PARSED_DOCUMENT_STORAGE_KEY,
  saveWorkupAttachment,
  toWorkupAttachment,
} from "@/lib/workup-documents";
import { Panel, PanelHeader } from "./panel";

export function PdfUploadPanel({
  compact = false,
  onParsed,
  workupId,
}: {
  compact?: boolean;
  onParsed?: (document: ParsedDocument) => void;
  workupId?: string;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [status, setStatus] = useState<"idle" | "uploading" | "parsed" | "error">("idle");
  const [message, setMessage] = useState("Upload a PDF to parse the survey.");
  const [parsed, setParsed] = useState<ParsedDocument | null>(null);

  async function handleFile(file: File | undefined) {
    if (!file) {
      return;
    }

    setStatus("uploading");
    setMessage("Uploading and parsing with PyMuPDF/pdfplumber...");

    try {
      const document = await uploadPdf(file);
      localStorage.setItem(LAST_PARSED_DOCUMENT_STORAGE_KEY, document.document_id);
      if (workupId) {
        const attachment = toWorkupAttachment(workupId, document);
        saveWorkupAttachment(attachment);
        window.dispatchEvent(new CustomEvent("tracequote:workup-document-attached", { detail: attachment }));
      }
      window.dispatchEvent(new CustomEvent("tracequote:document-parsed", { detail: document.document_id }));
      setParsed(document);
      setStatus("parsed");
      setMessage(`Parsed ${document.page_count} pages. OCR status: ${document.ocr_status.replace("_", " ")}.`);
      onParsed?.(document);
    } catch (error) {
      setStatus("error");
      setMessage(error instanceof Error ? error.message : "Upload failed.");
    }
  }

  const body = (
    <div
      className="flex min-h-64 flex-col items-center justify-center rounded-lg border-2 border-dashed border-line bg-slate-50 px-6 py-8 text-center"
      onDragOver={(event) => event.preventDefault()}
      onDrop={(event) => {
        event.preventDefault();
        void handleFile(event.dataTransfer.files[0]);
      }}
    >
      <input
        ref={inputRef}
        type="file"
        accept="application/pdf,.pdf"
        className="hidden"
        onChange={(event) => void handleFile(event.target.files?.[0])}
      />
      {status === "uploading" ? (
        <Loader2 className="h-10 w-10 animate-spin text-moss" />
      ) : status === "parsed" ? (
        <CheckCircle2 className="h-10 w-10 text-verified" />
      ) : status === "error" ? (
        <ServerCrash className="h-10 w-10 text-blocked" />
      ) : (
        <FileUp className="h-10 w-10 text-moss" />
      )}
      <div className="mt-4 text-lg font-semibold text-ink">
        {status === "parsed" ? parsed?.file_name : "Upload survey/report PDF"}
      </div>
      <p className="mt-2 max-w-md text-sm leading-6 text-graphite">{message}</p>
      {parsed ? (
        <div className="mt-4 grid gap-2 text-sm sm:grid-cols-3">
          <div className="rounded-md border border-line bg-white px-3 py-2">
            <div className="text-xs font-semibold uppercase tracking-wide text-moss">Pages</div>
            <div className="mt-1 font-semibold text-ink">{parsed.page_count}</div>
          </div>
          <div className="rounded-md border border-line bg-white px-3 py-2">
            <div className="text-xs font-semibold uppercase tracking-wide text-moss">Tables</div>
            <div className="mt-1 font-semibold text-ink">{parsed.tables.length}</div>
          </div>
          <div className="rounded-md border border-line bg-white px-3 py-2">
            <div className="text-xs font-semibold uppercase tracking-wide text-moss">Parser</div>
            <div className="mt-1 font-semibold text-ink">{parsed.parser_version}</div>
          </div>
        </div>
      ) : null}
      <button
        type="button"
        onClick={() => inputRef.current?.click()}
        className="focus-ring mt-5 rounded-md bg-ink px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-graphite disabled:cursor-not-allowed disabled:opacity-60"
        disabled={status === "uploading"}
      >
        {status === "uploading" ? "Parsing..." : "Select PDF"}
      </button>
    </div>
  );

  if (compact) {
    return body;
  }

  return (
    <Panel>
      <PanelHeader title="Source document" description="Upload a PDF and create parsed page/table JSON for review." />
      <div className="p-5">{body}</div>
    </Panel>
  );
}
