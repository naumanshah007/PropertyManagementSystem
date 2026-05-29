"use client";

import { Bot, CheckCircle2, KeyRound, Save, ShieldCheck, ShieldOff, TestTube2, XCircle } from "lucide-react";
import { useEffect, useState } from "react";
import { getLLMConfig, testLLMConfig, updateLLMConfig } from "@/lib/api";
import type { LLMConfig, LLMProvider, LLMTestResult } from "@/lib/types";
import { Panel, PanelHeader } from "./panel";
import { RiskChip } from "./status-chip";


const PROVIDER_LABELS: Record<LLMProvider, string> = {
  none: "Disabled (use deterministic extractor)",
  anthropic: "Anthropic Claude",
  openai: "OpenAI",
  gemini: "Google Gemini",
};

const PROVIDER_DOCS: Record<LLMProvider, string> = {
  none: "When disabled, register extraction uses the built-in deterministic rules (works for the Tauraroa demo survey only).",
  anthropic: "Get an API key from console.anthropic.com. Keys start with 'sk-ant-'.",
  openai: "Get an API key from platform.openai.com/api-keys. Keys start with 'sk-'.",
  gemini: "Get an API key from aistudio.google.com/apikey.",
};


export function LLMSettingsManager({ orgId }: { orgId: string }) {
  const [config, setConfig] = useState<LLMConfig | null>(null);
  const [provider, setProvider] = useState<LLMProvider>("none");
  const [apiKey, setApiKey] = useState("");
  const [model, setModel] = useState("");
  const [showApiKey, setShowApiKey] = useState(false);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<LLMTestResult | null>(null);
  const [message, setMessage] = useState("Loading LLM configuration…");

  useEffect(() => {
    (async () => {
      try {
        const loaded = await getLLMConfig(orgId);
        setConfig(loaded);
        setProvider(loaded.llm_provider);
        setModel(loaded.llm_model ?? "");
        setMessage("");
      } catch (error) {
        setMessage(error instanceof Error ? error.message : "Failed to load LLM config");
      }
    })();
  }, [orgId]);

  const defaultModelForProvider = config?.default_models?.[provider] ?? "";
  const effectiveModelPlaceholder = defaultModelForProvider || "model identifier";

  async function handleSave() {
    setSaving(true);
    setMessage("");
    setTestResult(null);
    try {
      // Only send api_key when the user typed something; null preserves the stored key.
      const payload = {
        llm_provider: provider,
        llm_api_key: apiKey.length > 0 ? apiKey : null,
        llm_model: model.length > 0 ? model : null,
      };
      const updated = await updateLLMConfig(orgId, payload);
      setConfig(updated);
      setApiKey("");
      setMessage("Saved. Next register extraction will use this provider.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Save failed");
    } finally {
      setSaving(false);
    }
  }

  async function handleTest() {
    if (provider === "none") {
      setTestResult({ ok: false, provider, model: "", detail: "Select a provider first." });
      return;
    }
    if (!apiKey) {
      setTestResult({
        ok: false,
        provider,
        model: model || defaultModelForProvider,
        detail: "Enter an API key in the field above to test it.",
      });
      return;
    }
    setTesting(true);
    setTestResult(null);
    try {
      const result = await testLLMConfig(orgId, {
        llm_provider: provider,
        llm_api_key: apiKey,
        llm_model: model.length > 0 ? model : null,
      });
      setTestResult(result);
    } catch (error) {
      setTestResult({
        ok: false,
        provider,
        model: model || defaultModelForProvider,
        detail: error instanceof Error ? error.message : "Test failed",
      });
    } finally {
      setTesting(false);
    }
  }

  async function handleClearKey() {
    if (!confirm("Clear the stored API key for this organisation?")) return;
    setSaving(true);
    try {
      const updated = await updateLLMConfig(orgId, {
        llm_provider: provider,
        llm_api_key: "",
        llm_model: model.length > 0 ? model : null,
      });
      setConfig(updated);
      setApiKey("");
      setMessage("API key cleared.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Clear failed");
    } finally {
      setSaving(false);
    }
  }

  return (
    <Panel>
      <PanelHeader
        title="LLM register extraction"
        description="Configure which AI provider extracts the asbestos register from uploaded survey PDFs. Without a key, the deterministic fallback is used."
      />

      <div className="grid gap-5 p-5">
        {message && (
          <div className="rounded-md border border-line bg-slate-50 px-3 py-2 text-sm text-graphite">{message}</div>
        )}

        {/* Current state */}
        <div className="flex flex-wrap items-center gap-3 rounded-md border border-line bg-slate-50 px-4 py-3">
          <Bot className="h-5 w-5 text-moss" />
          <div className="flex-1">
            <div className="text-xs font-semibold uppercase tracking-wide text-graphite">Current configuration</div>
            <div className="mt-1 text-sm font-semibold text-ink">
              {config ? PROVIDER_LABELS[config.llm_provider] : "—"}
              {config?.llm_model ? ` · ${config.llm_model}` : ""}
            </div>
            <div className="mt-1 text-xs text-graphite">
              {config?.has_api_key ? (
                <span className="inline-flex items-center gap-1 text-green-700">
                  <ShieldCheck className="h-3.5 w-3.5" /> API key on file ({config.api_key_preview})
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 text-amber-700">
                  <ShieldOff className="h-3.5 w-3.5" /> No API key — will fall back to deterministic extractor
                </span>
              )}
            </div>
          </div>
          {config?.llm_provider !== "none" && (
            <RiskChip label={config?.has_api_key ? "Active" : "Provider chosen, key missing"} />
          )}
        </div>

        {/* Provider selector */}
        <div>
          <label className="text-xs font-semibold uppercase tracking-wide text-moss">Provider</label>
          <select
            value={provider}
            onChange={(event) => {
              setProvider(event.target.value as LLMProvider);
              setTestResult(null);
            }}
            className="focus-ring mt-1 w-full rounded-md border border-line bg-white px-3 py-2 text-sm"
          >
            {(Object.keys(PROVIDER_LABELS) as LLMProvider[]).map((value) => (
              <option key={value} value={value}>
                {PROVIDER_LABELS[value]}
              </option>
            ))}
          </select>
          <p className="mt-1 text-xs text-graphite">{PROVIDER_DOCS[provider]}</p>
        </div>

        {/* API key */}
        {provider !== "none" && (
          <div>
            <label className="text-xs font-semibold uppercase tracking-wide text-moss">API key</label>
            <div className="mt-1 flex gap-2">
              <div className="relative flex-1">
                <KeyRound className="absolute left-2 top-1/2 h-4 w-4 -translate-y-1/2 text-graphite" />
                <input
                  type={showApiKey ? "text" : "password"}
                  value={apiKey}
                  onChange={(event) => setApiKey(event.target.value)}
                  placeholder={config?.has_api_key ? "Leave blank to keep existing key" : "Paste your API key here"}
                  className="focus-ring w-full rounded-md border border-line bg-white py-2 pl-8 pr-3 text-sm"
                  autoComplete="off"
                />
              </div>
              <button
                type="button"
                onClick={() => setShowApiKey((value) => !value)}
                className="focus-ring rounded-md border border-line bg-white px-3 text-sm text-graphite hover:bg-slate-50"
              >
                {showApiKey ? "Hide" : "Show"}
              </button>
            </div>
            <p className="mt-1 text-xs text-graphite">
              Keys are stored in the organisation settings JSON for this demo. They are masked on read
              (shown as <code>{config?.api_key_preview ?? "sk-***xxxx"}</code>) and never returned by the regular settings endpoint.
            </p>
            {config?.has_api_key && (
              <button
                type="button"
                onClick={handleClearKey}
                className="focus-ring mt-2 text-xs font-medium text-red-700 underline"
              >
                Clear stored API key
              </button>
            )}
          </div>
        )}

        {/* Model override */}
        {provider !== "none" && (
          <div>
            <label className="text-xs font-semibold uppercase tracking-wide text-moss">Model (optional)</label>
            <input
              type="text"
              value={model}
              onChange={(event) => setModel(event.target.value)}
              placeholder={effectiveModelPlaceholder}
              className="focus-ring mt-1 w-full rounded-md border border-line bg-white px-3 py-2 text-sm"
            />
            <p className="mt-1 text-xs text-graphite">
              Leave blank to use the default for the selected provider ({defaultModelForProvider || "—"}).
            </p>
          </div>
        )}

        {/* Test result */}
        {testResult && (
          <div
            className={`rounded-md border px-3 py-2 text-sm ${
              testResult.ok
                ? "border-green-200 bg-green-50 text-green-900"
                : "border-red-200 bg-red-50 text-red-900"
            }`}
          >
            <div className="flex items-center gap-2 font-semibold">
              {testResult.ok ? <CheckCircle2 className="h-4 w-4" /> : <XCircle className="h-4 w-4" />}
              {testResult.ok ? "Credentials work" : "Test failed"}
              <span className="text-xs font-normal opacity-70">
                · {testResult.provider} · {testResult.model || "default model"}
              </span>
            </div>
            <div className="mt-1 text-xs">{testResult.detail}</div>
          </div>
        )}

        {/* Actions */}
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={handleTest}
            disabled={testing || provider === "none"}
            className="focus-ring inline-flex items-center gap-2 rounded-md border border-line bg-white px-4 py-2 text-sm font-semibold text-ink shadow-sm hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <TestTube2 className="h-4 w-4" />
            {testing ? "Testing…" : "Test credentials"}
          </button>
          <button
            type="button"
            onClick={handleSave}
            disabled={saving}
            className="focus-ring inline-flex items-center gap-2 rounded-md bg-ink px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-graphite disabled:cursor-not-allowed disabled:opacity-50"
          >
            <Save className="h-4 w-4" />
            {saving ? "Saving…" : "Save configuration"}
          </button>
        </div>
      </div>
    </Panel>
  );
}
