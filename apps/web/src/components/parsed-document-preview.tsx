"use client";

import type React from "react";
import { useEffect, useState } from "react";
import { AlertTriangle, Database, FileText, Loader2, Search, TableProperties } from "lucide-react";
import { createOfflineParsedDocumentFallback, getParsedDocument } from "@/lib/api";
import type { ParsedDocument } from "@/lib/types";
import {
  LAST_PARSED_DOCUMENT_STORAGE_KEY,
  readWorkupAttachment,
  type WorkupDocumentAttachment,
} from "@/lib/workup-documents";
import { Panel, PanelHeader } from "./panel";
import { RiskChip } from "./status-chip";

export function ParsedDocumentPreview({ workupId }: { workupId?: string }) {
  const [documentId, setDocumentId] = useState<string | null>(null);
  const [attachment, setAttachment] = useState<WorkupDocumentAttachment | null>(null);
  const [document, setDocument] = useState<ParsedDocument | null>(null);
  const [selectedPage, setSelectedPage] = useState(1);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState<"idle" | "loading" | "loaded" | "error">("idle");
  const [message, setMessage] = useState("Upload a PDF from New Workup or Workup Cockpit to preview parsed text.");

  useEffect(() => {
    const workupAttachment = workupId ? readWorkupAttachment(workupId) : null;
    if (workupAttachment) {
      setAttachment(workupAttachment);
      setDocumentId(workupAttachment.documentId);
      return;
    }

    const stored = localStorage.getItem(LAST_PARSED_DOCUMENT_STORAGE_KEY);
    if (stored) {
      setDocumentId(stored);
    }

    function handleParsed(event: Event) {
      const custom = event as CustomEvent<string>;
      setDocumentId(custom.detail);
    }

    function handleAttached(event: Event) {
      const custom = event as CustomEvent<WorkupDocumentAttachment>;
      if (!workupId || custom.detail.workupId === workupId) {
        setAttachment(custom.detail);
        setDocumentId(custom.detail.documentId);
      }
    }

    window.addEventListener("tracequote:document-parsed", handleParsed);
    window.addEventListener("tracequote:workup-document-attached", handleAttached);
    return () => {
      window.removeEventListener("tracequote:document-parsed", handleParsed);
      window.removeEventListener("tracequote:workup-document-attached", handleAttached);
    };
  }, [workupId]);

  useEffect(() => {
    if (!documentId) {
      return;
    }

    let cancelled = false;
    setStatus("loading");
    setMessage("Loading parsed document JSON...");

    getParsedDocument(documentId)
      .then((parsed) => {
        if (cancelled) {
          return;
        }
        setDocument(parsed);
        setSelectedPage(1);
        setStatus("loaded");
        setMessage(`Loaded ${parsed.page_count} parsed pages and ${parsed.tables.length} extracted tables.`);
      })
      .catch((error) => {
        if (cancelled) {
          return;
        }
        if (process.env.NEXT_PUBLIC_TRACEQUOTE_OFFLINE_DEMO === "true") {
          const fallback = createOfflineParsedDocumentFallback();
          setDocument(fallback);
          setSelectedPage(1);
          setStatus("loaded");
          setMessage("Offline demo fallback active. This is not backend parsed output.");
          return;
        }
        setStatus("error");
        setMessage(error instanceof Error ? error.message : "Could not load parsed document.");
      });

    return () => {
      cancelled = true;
    };
  }, [documentId]);

  const page = document?.pages.find((entry) => entry.page_number === selectedPage);
  const pageTables = document?.tables.filter((table) => table.page_number === selectedPage) ?? [];
  const normalizedSearch = search.trim().toLowerCase();
  const visiblePages = document
    ? document.pages
        .filter((entry) => !normalizedSearch || entry.text.toLowerCase().includes(normalizedSearch))
        .slice(0, 120)
    : [];
  const pageText = page?.text || "";
  const sourceReady = Boolean(pageText.trim());
  const warnings = page?.warnings ?? [];

  return (
    <Panel>
      <PanelHeader
        title="Parsed document preview"
        description="Deterministic Phase 2 output from PyMuPDF page text and pdfplumber tables."
        right={
          status === "loading" ? (
            <Loader2 className="h-4 w-4 animate-spin text-moss" />
          ) : document ? (
            <RiskChip label={`${document.page_count} pages`} />
          ) : null
        }
      />
      <div className="border-b border-line bg-slate-50 px-5 py-3 text-sm text-graphite">{message}</div>
      {attachment ? (
        <div className="grid gap-3 border-b border-line px-5 py-4 md:grid-cols-5">
          <Metric icon={<FileText className="h-4 w-4" />} label="Attached file" value={attachment.fileName} />
          <Metric icon={<Database className="h-4 w-4" />} label="Page count" value={String(attachment.pageCount)} />
          <Metric icon={<Database className="h-4 w-4" />} label="Parser" value={attachment.parserVersion} />
          <Metric icon={<Database className="h-4 w-4" />} label="OCR" value={attachment.ocrStatus.replace("_", " ")} />
          <Metric icon={<Database className="h-4 w-4" />} label="Uploaded" value={new Date(attachment.uploadedAt).toLocaleString("en-NZ")} />
        </div>
      ) : null}
      {document ? (
        <div className="grid gap-0 lg:grid-cols-[260px_1fr]">
          <aside className="max-h-[680px] overflow-auto border-r border-line bg-slate-50 p-3">
            <label className="mb-3 block">
              <span className="mb-1 flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-moss">
                <Search className="h-3.5 w-3.5" />
                Search parsed text
              </span>
              <input
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Register, Class A..."
                className="w-full rounded-md border border-line bg-white px-3 py-2 text-sm text-ink shadow-sm"
              />
            </label>
            {visiblePages.map((entry) => (
              <button
                key={entry.page_number}
                type="button"
                onClick={() => setSelectedPage(entry.page_number)}
                className={`mb-2 flex w-full items-center justify-between rounded-md border px-3 py-2 text-left text-sm ${
                  selectedPage === entry.page_number
                    ? "border-moss bg-white text-ink shadow-sm"
                    : "border-line bg-white/60 text-graphite hover:bg-white"
                }`}
              >
                <span className="font-semibold">Page {entry.page_number}</span>
                {entry.warnings.length ? <RiskChip label="Warning" /> : null}
              </button>
            ))}
            {visiblePages.length === 0 ? (
              <div className="rounded-md border border-line bg-white p-3 text-sm text-graphite">No pages match this search.</div>
            ) : null}
          </aside>
          <div className="min-w-0 p-5">
            <div className="mb-4 grid gap-3 md:grid-cols-3">
              <Metric icon={<FileText className="h-4 w-4" />} label="File" value={document.file_name} />
              <Metric icon={<Database className="h-4 w-4" />} label="OCR" value={document.ocr_status.replace("_", " ")} />
              <Metric icon={<TableProperties className="h-4 w-4" />} label="Tables on page" value={String(pageTables.length)} />
            </div>
            <div className="mb-4 flex flex-wrap gap-2">
              <RiskChip label={sourceReady ? "Source-ready" : "Source not ready"} />
              {warnings.map((warning) => (
                <RiskChip key={warning} label={warning.replace(/_/g, " ")} />
              ))}
            </div>
            {warnings.length ? (
              <div className="mb-4 rounded-md border border-amber-200 bg-amber-50 p-4 text-sm text-amber-950">
                <div className="flex items-start gap-2 font-semibold">
                  <AlertTriangle className="mt-0.5 h-4 w-4" />
                  Parser warnings
                </div>
                <ul className="mt-2 list-disc pl-5">
                  {warnings.map((warning) => (
                    <li key={warning}>{warning.replace(/_/g, " ")}</li>
                  ))}
                </ul>
              </div>
            ) : null}
            <div className="rounded-md border border-line">
              <div className="border-b border-line bg-slate-50 px-4 py-3 text-sm font-semibold text-ink">
                Page {selectedPage} text preview
              </div>
              <pre className="max-h-80 overflow-auto whitespace-pre-wrap p-4 text-sm leading-6 text-graphite">
                {pageText || "No text extracted from this page."}
              </pre>
            </div>
            <div className="mt-4 rounded-md border border-line">
              <div className="border-b border-line bg-slate-50 px-4 py-3 text-sm font-semibold text-ink">
                Table extraction preview
              </div>
              {pageTables.length ? (
                <div className="overflow-x-auto p-4">
                  {pageTables.map((table, index) => (
                    <table key={`${table.page_number}-${index}`} className="mb-4 min-w-full divide-y divide-line text-xs">
                      <tbody className="divide-y divide-line">
                        {table.rows.slice(0, 8).map((row, rowIndex) => (
                          <tr key={rowIndex}>
                            {row.map((cell, cellIndex) => (
                              <td key={cellIndex} className="max-w-64 border-r border-line px-2 py-2 align-top text-graphite">
                                {cell}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  ))}
                </div>
              ) : (
                <div className="p-4 text-sm text-graphite">No tables detected on this page.</div>
              )}
            </div>
          </div>
        </div>
      ) : (
        <div className="p-5 text-sm text-graphite">
          Parsed document previews will appear here after a PDF is uploaded and parsed.
        </div>
      )}
    </Panel>
  );
}

function Metric({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
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
