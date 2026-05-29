import type { ParsedDocument } from "./types";

export const WORKUP_DOCUMENTS_STORAGE_KEY = "tracequote:workupDocumentAttachments";
export const LAST_PARSED_DOCUMENT_STORAGE_KEY = "tracequote:lastParsedDocumentId";

export interface WorkupDocumentAttachment {
  workupId: string;
  documentId: string;
  fileName: string;
  pageCount: number;
  parserVersion: string;
  ocrStatus: string;
  parsedStatus: "parsed";
  uploadedAt: string;
}

export function toWorkupAttachment(workupId: string, document: ParsedDocument): WorkupDocumentAttachment {
  return {
    workupId,
    documentId: document.document_id,
    fileName: document.file_name,
    pageCount: document.page_count,
    parserVersion: document.parser_version,
    ocrStatus: document.ocr_status,
    parsedStatus: "parsed",
    uploadedAt: document.created_at,
  };
}

export function readWorkupAttachments(): Record<string, WorkupDocumentAttachment> {
  if (typeof window === "undefined") {
    return {};
  }

  const raw = localStorage.getItem(WORKUP_DOCUMENTS_STORAGE_KEY);
  if (!raw) {
    return {};
  }

  try {
    return JSON.parse(raw) as Record<string, WorkupDocumentAttachment>;
  } catch {
    return {};
  }
}

export function saveWorkupAttachment(attachment: WorkupDocumentAttachment) {
  const attachments = readWorkupAttachments();
  attachments[attachment.workupId] = attachment;
  localStorage.setItem(WORKUP_DOCUMENTS_STORAGE_KEY, JSON.stringify(attachments));
  localStorage.setItem(LAST_PARSED_DOCUMENT_STORAGE_KEY, attachment.documentId);
}

export function readWorkupAttachment(workupId: string): WorkupDocumentAttachment | null {
  return readWorkupAttachments()[workupId] ?? null;
}

