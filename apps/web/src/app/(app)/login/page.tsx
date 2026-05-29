"use client";

import { useState } from "react";
import { ArrowRight, ShieldCheck, Sparkles } from "lucide-react";
import { loginDemo } from "@/lib/api";
import { saveDemoSession } from "@/lib/demo-auth";

export default function LoginPage() {
  const [email, setEmail] = useState("admin@privexa.co");
  const [password, setPassword] = useState("admin123");
  const [message, setMessage] = useState("Use demo-only credentials for local mode.");
  const [submitting, setSubmitting] = useState(false);

  async function submit() {
    setSubmitting(true);
    try {
      const session = await loginDemo({ email, password });
      saveDemoSession(session);
      window.location.href = session.default_route;
    } catch {
      setMessage("Login failed. Check the demo email and password.");
      setSubmitting(false);
    }
  }

  return (
    <div className="relative mx-auto flex max-w-md flex-col justify-center py-8">
      <div className="mb-6 flex items-center gap-3">
        <div className="grid h-11 w-11 place-items-center rounded-xl bg-grad-primary shadow-glow">
          <Sparkles className="h-5 w-5 text-night-900" />
        </div>
        <div>
          <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-cyan-300">TraceQuote AI</div>
          <h1 className="text-2xl font-semibold text-ink">Sign in to your workspace</h1>
        </div>
      </div>

      <div className="relative">
        <div className="absolute -inset-6 -z-10 rounded-3xl bg-gradient-to-tr from-cyan-500/20 via-violet-500/15 to-transparent blur-3xl" />
        <div className="rounded-2xl border border-white/10 bg-night-800/70 p-6 shadow-panel backdrop-blur-xl">
          <div className="space-y-4">
            <label className="block text-[11px] font-semibold uppercase tracking-[0.16em] text-graphite">
              Email
              <input
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                className="mt-1.5 w-full rounded-lg border border-white/10 bg-night-900/60 px-3 py-2.5 text-sm normal-case tracking-normal text-ink outline-none transition focus:border-cyan-300/50 focus:ring-2 focus:ring-cyan-300/30"
              />
            </label>
            <label className="block text-[11px] font-semibold uppercase tracking-[0.16em] text-graphite">
              Password
              <input
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                className="mt-1.5 w-full rounded-lg border border-white/10 bg-night-900/60 px-3 py-2.5 text-sm normal-case tracking-normal text-ink outline-none transition focus:border-cyan-300/50 focus:ring-2 focus:ring-cyan-300/30"
              />
            </label>
            <button
              onClick={() => void submit()}
              disabled={submitting}
              className="btn-primary w-full py-2.5 disabled:opacity-60"
            >
              {submitting ? "Signing in…" : "Sign in"}
              <ArrowRight className="h-4 w-4" />
            </button>
          </div>

          <div className="mt-5 rounded-xl border border-white/10 bg-white/[0.04] p-4 text-xs leading-5 text-graphite">
            <div className="flex items-center gap-2 text-cyan-200">
              <ShieldCheck className="h-3.5 w-3.5" />
              {message}
            </div>
            <div className="mt-3 space-y-1">
              <div>
                <span className="text-graphite">Super admin: </span>
                <span className="font-semibold text-ink">admin@privexa.co / admin123</span>
              </div>
              <div>
                <span className="text-graphite">Org admin: </span>
                <span className="font-semibold text-ink">test@privexa.co / admin123</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
