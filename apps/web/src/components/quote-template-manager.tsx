"use client";

import { useEffect, useState } from "react";
import { ExternalLink, FileText, Loader2, Save, Sparkles } from "lucide-react";
import { API_BASE_URL, getOrganisationSettings, updateOrganisationSettings } from "@/lib/api";
import { Panel, PanelHeader } from "@/components/panel";
import { RiskChip } from "@/components/status-chip";
import type { OrganisationSettings, QuoteTemplateType } from "@/lib/types";

// Seeded demo documents (from scripts/demo_reset.py) so the admin can preview a
// real export of the active template.
const PREVIEW_DOC: Record<string, string> = {
  "org-revolve-demo": "demo-tauraroa-revolve",
  "org-demo-tracequote": "demo-tauraroa-vendor",
};

export function QuoteTemplateManager({ orgId }: { orgId: string }) {
  const [settings, setSettings] = useState<OrganisationSettings | null>(null);
  const [status, setStatus] = useState<"loading" | "ready" | "saving" | "error">("loading");
  const [message, setMessage] = useState<string | null>(null);

  // Editable fields
  const [templateType, setTemplateType] = useState<QuoteTemplateType>("default");
  const [templateName, setTemplateName] = useState("");
  const [quotePrefix, setQuotePrefix] = useState("");
  const [gstNumber, setGstNumber] = useState("");
  const [contactName, setContactName] = useState("");
  const [contactPhone, setContactPhone] = useState("");
  const [validDays, setValidDays] = useState(30);
  const [showAppendix, setShowAppendix] = useState(false);
  const [showReview, setShowReview] = useState(true);
  const [intro, setIntro] = useState("");
  const [closing, setClosing] = useState("");
  const [emailMsg, setEmailMsg] = useState("");
  const [inclusions, setInclusions] = useState("");
  const [importantNotes, setImportantNotes] = useState("");
  const [requiredServices, setRequiredServices] = useState("");

  useEffect(() => {
    getOrganisationSettings(orgId)
      .then((s) => {
        setSettings(s);
        setTemplateType(s.template_type);
        setTemplateName(s.template_name);
        setQuotePrefix(s.quote_prefix);
        setGstNumber(s.business_gst_number);
        setContactName(s.contact_name);
        setContactPhone(s.contact_phone);
        setValidDays(s.quote_valid_days);
        setShowAppendix(s.show_source_evidence_appendix);
        setShowReview(s.show_review_statement);
        setIntro(s.quote_intro_text);
        setClosing(s.quote_closing_text);
        setEmailMsg(s.default_email_message);
        setInclusions(s.quote_inclusions.join("\n"));
        setImportantNotes(s.quote_important_notes.join("\n"));
        setRequiredServices(s.quote_required_services.join("\n"));
        setStatus("ready");
      })
      .catch((e) => {
        setStatus("error");
        setMessage(e instanceof Error ? e.message : "Failed to load settings");
      });
  }, [orgId]);

  const lines = (text: string) => text.split("\n").map((l) => l.trim()).filter(Boolean);

  async function save() {
    setStatus("saving");
    setMessage(null);
    try {
      const updated = await updateOrganisationSettings(orgId, {
        template_type: templateType,
        template_name: templateName,
        quote_prefix: quotePrefix,
        business_gst_number: gstNumber,
        contact_name: contactName,
        contact_phone: contactPhone,
        quote_valid_days: validDays,
        show_source_evidence_appendix: showAppendix,
        show_review_statement: showReview,
        quote_intro_text: intro,
        quote_closing_text: closing,
        default_email_message: emailMsg,
        quote_inclusions: lines(inclusions),
        quote_important_notes: lines(importantNotes),
        quote_required_services: lines(requiredServices),
      });
      setSettings(updated);
      setStatus("ready");
      setMessage("Saved. New client quotes for this organisation use this template.");
    } catch (e) {
      setStatus("error");
      setMessage(e instanceof Error ? e.message : "Save failed");
    }
  }

  if (status === "loading") {
    return (
      <Panel className="flex items-center gap-3 p-6 text-sm text-graphite">
        <Loader2 className="h-4 w-4 animate-spin text-cyan-300" /> Loading template…
      </Panel>
    );
  }
  if (!settings) {
    return <Panel className="p-6 text-sm text-rose-200">{message ?? "Could not load settings."}</Panel>;
  }

  const previewDoc = PREVIEW_DOC[orgId];

  return (
    <div className="space-y-6">
      <Panel>
        <PanelHeader
          title="Template type"
          description="Controls the client-facing quote layout. Internal evidence/audit is never shown to the client unless explicitly enabled."
          right={<RiskChip label={templateType === "ras_style" ? "RAS-style estimate" : "Generic quote"} />}
        />
        <div className="grid gap-3 p-5 sm:grid-cols-2">
          <TypeCard
            active={templateType === "default"}
            onClick={() => setTemplateType("default")}
            title="Generic TraceQuote quote"
            body='Clean "Quote" layout with your branding — the safe default/fallback.'
            icon={FileText}
          />
          <TypeCard
            active={templateType === "ras_style"}
            onClick={() => setTemplateType("ras_style")}
            title="RAS-style estimate"
            body='RAS-1285 "Estimate" layout: numbered inclusions, IMPORTANT notes, required client services.'
            icon={Sparkles}
          />
        </div>
      </Panel>

      <Panel>
        <PanelHeader title="Quote header & contact" description="Appears on every exported client quote." />
        <div className="grid gap-4 p-5 md:grid-cols-2">
          <Field label="Template name" value={templateName} onChange={setTemplateName} />
          <Field label="Quote prefix" value={quotePrefix} onChange={setQuotePrefix} />
          <Field label="GST number" value={gstNumber} onChange={setGstNumber} />
          <Field label="Valid for (days)" value={String(validDays)} onChange={(v) => setValidDays(Number(v) || 0)} />
          <Field label="Contact person" value={contactName} onChange={setContactName} />
          <Field label="Contact phone" value={contactPhone} onChange={setContactPhone} />
        </div>
        <div className="flex flex-wrap gap-6 border-t border-white/10 px-5 py-4">
          <Toggle label="Show review statement" checked={showReview} onChange={setShowReview} />
          <Toggle
            label="Show source-evidence appendix (internal)"
            checked={showAppendix}
            onChange={setShowAppendix}
          />
        </div>
      </Panel>

      <Panel>
        <PanelHeader title="Boilerplate text" description="Opening, closing, and default email message." />
        <div className="space-y-4 p-5">
          <Area label="Opening paragraph" value={intro} onChange={setIntro} rows={3} />
          <Area label="Closing / sign-off" value={closing} onChange={setClosing} rows={2} />
          <Area label="Default email message" value={emailMsg} onChange={setEmailMsg} rows={2} />
        </div>
      </Panel>

      <Panel>
        <PanelHeader title="Inclusions, notes & required services" description="One item per line." />
        <div className="space-y-4 p-5">
          <Area label='"This pricing includes" list' value={inclusions} onChange={setInclusions} rows={8} />
          <Area label="IMPORTANT notes" value={importantNotes} onChange={setImportantNotes} rows={8} />
          <Area label="Client-required services" value={requiredServices} onChange={setRequiredServices} rows={4} />
        </div>
      </Panel>

      <div className="flex flex-wrap items-center gap-3">
        <button onClick={() => void save()} disabled={status === "saving"} className="btn-primary disabled:opacity-60">
          {status === "saving" ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
          Save template
        </button>
        {previewDoc ? (
          <a
            href={`${API_BASE_URL}/documents/${previewDoc}/export-quote/pdf`}
            target="_blank"
            rel="noreferrer"
            className="btn-secondary"
          >
            <ExternalLink className="h-4 w-4" /> Preview export (PDF)
          </a>
        ) : null}
        {message ? <span className={status === "error" ? "text-sm text-rose-200" : "text-sm text-emerald-200"}>{message}</span> : null}
      </div>
    </div>
  );
}

function TypeCard({
  active,
  onClick,
  title,
  body,
  icon: Icon,
}: {
  active: boolean;
  onClick: () => void;
  title: string;
  body: string;
  icon: typeof FileText;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded-xl border p-4 text-left transition ${
        active ? "border-cyan-300/50 bg-cyan-400/10" : "border-white/10 bg-white/[0.03] hover:border-white/20"
      }`}
    >
      <div className={`grid h-9 w-9 place-items-center rounded-lg border border-white/10 ${active ? "text-cyan-300" : "text-graphite"}`}>
        <Icon className="h-4 w-4" />
      </div>
      <div className="mt-3 font-semibold text-ink">{title}</div>
      <p className="mt-1 text-sm text-graphite">{body}</p>
    </button>
  );
}

function Field({ label, value, onChange }: { label: string; value: string; onChange: (v: string) => void }) {
  return (
    <label className="block text-[11px] font-semibold uppercase tracking-[0.16em] text-graphite">
      {label}
      <input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="mt-1.5 w-full rounded-lg border border-white/10 bg-night-900/60 px-3 py-2.5 text-sm normal-case tracking-normal text-ink outline-none focus:border-cyan-300/50 focus:ring-2 focus:ring-cyan-300/30"
      />
    </label>
  );
}

function Area({
  label,
  value,
  onChange,
  rows,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  rows: number;
}) {
  return (
    <label className="block text-[11px] font-semibold uppercase tracking-[0.16em] text-graphite">
      {label}
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        rows={rows}
        className="mt-1.5 w-full rounded-lg border border-white/10 bg-night-900/60 px-3 py-2.5 text-sm normal-case tracking-normal text-ink outline-none focus:border-cyan-300/50 focus:ring-2 focus:ring-cyan-300/30"
      />
    </label>
  );
}

function Toggle({ label, checked, onChange }: { label: string; checked: boolean; onChange: (v: boolean) => void }) {
  return (
    <button type="button" onClick={() => onChange(!checked)} className="inline-flex items-center gap-2 text-sm font-medium text-ink">
      <span className={`relative h-4 w-7 rounded-full transition ${checked ? "bg-grad-primary" : "bg-white/15"}`}>
        <span className={`absolute top-0.5 h-3 w-3 rounded-full bg-night-900 transition ${checked ? "left-3.5" : "left-0.5"}`} />
      </span>
      {label}
    </button>
  );
}
