"use client";

import { Building2, Check, Sparkles } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { createOrganisation } from "@/lib/api";
import { Panel, PanelHeader } from "./panel";


export function CreateOrganisationForm() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [tradingName, setTradingName] = useState("");
  const [slug, setSlug] = useState("");
  const [email, setEmail] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    if (!name.trim()) {
      setError("Legal name is required.");
      return;
    }
    if (!email.trim() || !email.includes("@")) {
      setError("A valid admin email is required.");
      return;
    }

    setSubmitting(true);
    try {
      const created = await createOrganisation({
        name: name.trim(),
        trading_name: tradingName.trim() || null,
        slug: slug.trim() || null,
        email: email.trim(),
      });
      // Backend auto-seeds the RAS-1285 starter pricebook — land the admin on the pricebook editor
      // so they can review/edit the prices their new org will use.
      router.push(`/admin/organisations/${created.id}/pricebook?onboarded=1`);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Creation failed");
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-5">
      <div className="rounded-lg border border-moss/30 bg-moss/5 px-5 py-4 text-sm text-moss">
        <div className="flex items-center gap-2 font-semibold">
          <Sparkles className="h-4 w-4" />
          What happens next
        </div>
        <ul className="mt-2 list-disc space-y-1 pl-5 text-graphite">
          <li>Your organisation is created with quote-branding defaults from RAS-1285.</li>
          <li>A starter pricebook with all 10 RAS-1285 starter rules is auto-created and marked active.</li>
          <li>You will land on the pricebook editor — adjust unit rates, minimum charges, and risk multipliers per your business.</li>
        </ul>
      </div>

      <Panel>
        <PanelHeader
          title="Organisation details"
          description="Creates an organisation via POST /organisations and seeds a starter RAS-1285 pricebook you can edit immediately."
        />
        <form className="grid gap-4 p-5 md:grid-cols-2" onSubmit={handleSubmit}>
          <Field label="Legal name" required value={name} onChange={setName} placeholder="Acme Asbestos Removal Ltd" />
          <Field
            label="Trading name (optional)"
            value={tradingName}
            onChange={setTradingName}
            placeholder="Acme Environmental"
          />
          <Field label="Slug (optional)" value={slug} onChange={setSlug} placeholder="acme-environmental" />
          <Field
            label="Admin email"
            required
            value={email}
            onChange={setEmail}
            placeholder="admin@example.com"
            type="email"
          />

          {error && (
            <div className="md:col-span-2 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-900">
              {error}
            </div>
          )}

          <div className="md:col-span-2 flex flex-wrap items-center gap-3">
            <button
              type="submit"
              disabled={submitting}
              className="focus-ring inline-flex items-center gap-2 rounded-md bg-ink px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-graphite disabled:cursor-not-allowed disabled:opacity-50"
            >
              <Building2 className="h-4 w-4" />
              {submitting ? "Creating organisation…" : "Create organisation"}
            </button>
            <div className="flex items-center gap-1.5 text-xs text-graphite">
              <Check className="h-3.5 w-3.5 text-moss" />
              Starter pricebook with 10 RAS-1285 rules is auto-created.
            </div>
          </div>
        </form>
      </Panel>
    </div>
  );
}


function Field({
  label,
  value,
  onChange,
  placeholder,
  required,
  type = "text",
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder: string;
  required?: boolean;
  type?: string;
}) {
  return (
    <label className="text-xs font-semibold uppercase tracking-wide text-graphite">
      {label}
      {required && <span className="ml-1 text-red-600">*</span>}
      <input
        type={type}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        required={required}
        placeholder={placeholder}
        className="focus-ring mt-1 w-full rounded-md border border-line px-3 py-2 text-sm normal-case tracking-normal text-ink"
      />
    </label>
  );
}
