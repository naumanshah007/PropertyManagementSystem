import Image from "next/image";
import Link from "next/link";
import {
  ArrowRight,
  BadgeCheck,
  Brain,
  Building2,
  CheckCircle2,
  FileSearch,
  Lock,
  PackageCheck,
  ShieldCheck,
  Sparkles,
  Workflow,
} from "lucide-react";

const APP_NAME = process.env.NEXT_PUBLIC_APP_NAME ?? "TraceQuote AI";

const benefits = [
  {
    icon: FileSearch,
    title: "Evidence-linked extraction",
    body: "Every register item, quantity, and class is tied back to its source page so estimators can audit a line in one click.",
    accent: "from-cyan-400/30 to-cyan-500/0",
    iconClass: "text-cyan-300",
  },
  {
    icon: Brain,
    title: "AI that defers to humans",
    body: "Draft quotes are generated automatically — Class A, no-access, and presumed lines route to a human for review before export.",
    accent: "from-violet-400/30 to-violet-500/0",
    iconClass: "text-violet-300",
  },
  {
    icon: Workflow,
    title: "Pricebook your way",
    body: "Each organisation gets a starter pricebook seeded from real NZ industry rates, fully editable to match your job mix.",
    accent: "from-emerald-400/30 to-emerald-500/0",
    iconClass: "text-emerald-300",
  },
  {
    icon: PackageCheck,
    title: "Client-ready output",
    body: "Export branded RAS-style quote PDFs or push line items into Fergus as a CSV — no copy-paste, no errors.",
    accent: "from-pink-400/30 to-pink-500/0",
    iconClass: "text-pink-300",
  },
  {
    icon: Building2,
    title: "Multi-organisation SaaS",
    body: "Run multiple trading entities, teams, and pricebooks in one workspace with role-aware access.",
    accent: "from-amber-400/30 to-amber-500/0",
    iconClass: "text-amber-300",
  },
  {
    icon: Lock,
    title: "Secure and traceable",
    body: "Per-org LLM keys, hashed credentials, upload limits, and a full audit trail from upload through approval.",
    accent: "from-sky-400/30 to-sky-500/0",
    iconClass: "text-sky-300",
  },
];

const valuePoints = [
  "Cut 4–6 hours of estimator time off every survey",
  "Stop missing no-access areas and Class A clearance recommendations",
  "Standardise quote formatting across estimators and trading entities",
  "Keep the human approval gate that compliance and insurers expect",
];

export default function LandingPage() {
  return (
    <div className="relative min-h-screen overflow-hidden bg-night-900 text-ink antialiased">
      <BackgroundGlow />
      <SiteHeader />

      <main className="relative">
        <Hero />
        <TrustBar />
        <ValueProp />
        <HowItWorks />
        <ExtractedIntelligence />
        <Benefits />
        <CallToAction />
      </main>

      <SiteFooter />
    </div>
  );
}

function BackgroundGlow() {
  return (
    <div aria-hidden className="pointer-events-none absolute inset-0 -z-0 overflow-hidden">
      <div className="absolute -top-40 left-1/2 h-[640px] w-[1100px] -translate-x-1/2 rounded-full bg-cyan-500/15 blur-[140px]" />
      <div className="absolute top-[700px] -left-40 h-[420px] w-[640px] rounded-full bg-violet-500/15 blur-[140px]" />
      <div className="absolute top-[1500px] -right-40 h-[420px] w-[640px] rounded-full bg-pink-500/10 blur-[140px]" />
      <div className="absolute inset-0 surface-grid [mask-image:radial-gradient(ellipse_at_center,black_30%,transparent_75%)]" />
    </div>
  );
}

function SiteHeader() {
  return (
    <header className="sticky top-0 z-30 border-b border-white/5 bg-night-900/70 backdrop-blur-xl">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-5 py-4 lg:px-8">
        <Link href="/" className="flex items-center gap-2.5 font-semibold tracking-tight text-ink">
          <span className="grid h-8 w-8 place-items-center rounded-lg bg-grad-primary shadow-glow">
            <Sparkles className="h-4 w-4 text-night-900" />
          </span>
          {APP_NAME}
        </Link>

        <nav className="hidden items-center gap-8 text-sm font-medium text-graphite md:flex">
          <a href="#how-it-works" className="transition hover:text-ink">How it works</a>
          <a href="#intelligence" className="transition hover:text-ink">Intelligence</a>
          <a href="#benefits" className="transition hover:text-ink">Benefits</a>
          <a href="#cta" className="transition hover:text-ink">Book a demo</a>
        </nav>

        <div className="flex items-center gap-2">
          <Link href="/login" className="btn-secondary hidden sm:inline-flex">Sign in</Link>
          <Link href="/login" className="btn-primary">
            Open the app
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </div>
    </header>
  );
}

function Hero() {
  return (
    <section className="relative">
      <div className="mx-auto max-w-7xl px-5 pb-20 pt-16 lg:px-8 lg:pt-24">
        <div className="grid items-center gap-12 lg:grid-cols-[1.05fr_1.1fr]">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] text-ink backdrop-blur">
              <span className="h-1.5 w-1.5 rounded-full bg-cyan-300 shadow-[0_0_8px_rgba(34,211,238,0.9)]" />
              Evidence-linked quoting with human approval
            </div>
            <h1 className="mt-5 text-4xl font-semibold leading-[1.05] tracking-tight sm:text-5xl lg:text-[58px]">
              Turn survey reports into{" "}
              <span className="bg-gradient-to-r from-cyan-300 via-sky-300 to-violet-300 bg-clip-text text-transparent">
                quote drafts
              </span>{" "}
              in minutes.
            </h1>
            <p className="mt-5 max-w-xl text-base leading-7 text-graphite sm:text-lg">
              {APP_NAME} is an AI-powered survey-to-quote workflow for asbestos, demolition, and remediation teams.
              Extract. Price. Review. Export — without the spreadsheet rebuild.
            </p>

            <div className="mt-8 flex flex-wrap items-center gap-3">
              <Link href="#cta" className="btn-primary px-5 py-3">
                Book a demo
                <ArrowRight className="h-4 w-4" />
              </Link>
              <Link href="/login" className="btn-secondary px-5 py-3">
                Try the live demo
              </Link>
            </div>

            <div className="mt-10 flex flex-wrap items-center gap-x-6 gap-y-3 text-xs font-medium uppercase tracking-[0.14em] text-graphite">
              <span className="inline-flex items-center gap-2">
                <ShieldCheck className="h-3.5 w-3.5 text-cyan-300" /> Audit ready
              </span>
              <span className="inline-flex items-center gap-2">
                <Lock className="h-3.5 w-3.5 text-violet-300" /> Enterprise secure
              </span>
              <span className="inline-flex items-center gap-2">
                <BadgeCheck className="h-3.5 w-3.5 text-emerald-300" /> Human approval
              </span>
            </div>
          </div>

          <div className="relative">
            <div className="absolute -inset-8 -z-10 rounded-[2rem] bg-gradient-to-tr from-cyan-500/25 via-violet-500/15 to-transparent blur-3xl" />
            <div className="overflow-hidden rounded-2xl border border-white/10 bg-night-800 shadow-[0_40px_120px_-30px_rgba(34,211,238,0.35)] ring-1 ring-white/5">
              <Image
                src="/marketing/hero.png"
                alt="TraceQuote AI dashboard turning a 50-page asbestos survey into a priced quote draft"
                width={1672}
                height={945}
                priority
                className="h-auto w-full"
              />
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function TrustBar() {
  return (
    <section className="relative">
      <div className="mx-auto max-w-7xl px-5 py-8 lg:px-8">
        <div className="grid grid-cols-2 gap-px overflow-hidden rounded-2xl border border-white/10 bg-white/5 text-sm md:grid-cols-4">
          {[
            { label: "Survey pages parsed", value: "50+ per upload" },
            { label: "Register items extracted", value: "Class A, B & no-access" },
            { label: "Pricebook rules", value: "Per-org, fully editable" },
            { label: "Export channels", value: "PDF + Fergus CSV" },
          ].map((stat) => (
            <div key={stat.label} className="bg-night-800/80 px-5 py-5">
              <div className="text-[10px] font-semibold uppercase tracking-[0.16em] text-cyan-300/90">
                {stat.label}
              </div>
              <div className="mt-1 text-base font-semibold text-ink">{stat.value}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function ValueProp() {
  return (
    <section className="relative mx-auto max-w-7xl px-5 py-20 lg:px-8">
      <div className="grid gap-12 lg:grid-cols-[0.95fr_1.05fr] lg:items-center">
        <div>
          <div className="text-xs font-semibold uppercase tracking-[0.18em] text-cyan-300">
            Why estimators choose {APP_NAME}
          </div>
          <h2 className="mt-3 text-3xl font-semibold tracking-tight text-ink sm:text-4xl">
            Stop rebuilding quotes from scratch for every survey.
          </h2>
          <p className="mt-4 text-base leading-7 text-graphite">
            Surveys arrive as 30–80 page PDFs with messy registers, no-access notes, and Class A items mixed in.{" "}
            {APP_NAME} reads the register, links every line back to the source page, prices it against your pricebook,
            and stages it for a human estimator to approve.
          </p>
        </div>
        <ul className="grid gap-3 sm:grid-cols-2">
          {valuePoints.map((point) => (
            <li
              key={point}
              className="group relative flex items-start gap-3 rounded-xl border border-white/10 bg-white/[0.04] p-4 backdrop-blur-sm transition hover:border-cyan-300/40 hover:bg-white/[0.06]"
            >
              <CheckCircle2 className="mt-0.5 h-5 w-5 flex-shrink-0 text-cyan-300" />
              <span className="text-sm leading-6 text-ink">{point}</span>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}

function HowItWorks() {
  return (
    <section id="how-it-works" className="relative py-20">
      <div className="mx-auto max-w-7xl px-5 lg:px-8">
        <div className="mx-auto max-w-2xl text-center">
          <div className="text-xs font-semibold uppercase tracking-[0.18em] text-cyan-300">How it works</div>
          <h2 className="mt-3 text-3xl font-semibold tracking-tight text-ink sm:text-4xl">
            From survey to quote, with evidence and control.
          </h2>
          <p className="mt-4 text-base leading-7 text-graphite">
            Six steps. One workflow. Every action is traceable from the source survey page through pricing, review, and
            the final client-ready quote package.
          </p>
        </div>

        <div className="relative mt-12">
          <div className="absolute -inset-6 -z-10 rounded-[2rem] bg-gradient-to-tr from-violet-500/20 via-cyan-500/10 to-transparent blur-3xl" />
          <div className="overflow-hidden rounded-2xl border border-white/10 bg-white shadow-[0_40px_120px_-30px_rgba(139,92,246,0.35)] ring-1 ring-white/5">
            <Image
              src="/marketing/workflow.png"
              alt="The six-step TraceQuote AI workflow: upload survey, extract intelligence, generate candidates, apply pricing, review and approve, export quote"
              width={1536}
              height={1024}
              className="h-auto w-full"
            />
          </div>
        </div>
      </div>
    </section>
  );
}

function ExtractedIntelligence() {
  return (
    <section id="intelligence" className="relative py-20">
      <div className="mx-auto max-w-7xl px-5 lg:px-8">
        <div className="mx-auto max-w-2xl text-center">
          <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-ink backdrop-blur">
            <Sparkles className="h-3.5 w-3.5 text-cyan-300" />
            AI document intelligence
          </div>
          <h2 className="mt-4 text-3xl font-semibold tracking-tight text-ink sm:text-4xl">
            Extracted intelligence from{" "}
            <span className="bg-gradient-to-r from-cyan-300 via-sky-300 to-violet-300 bg-clip-text text-transparent">
              complex survey reports
            </span>
            .
          </h2>
          <p className="mt-4 text-base leading-7 text-graphite">
            {APP_NAME} reads, understands, and structures your survey data — materials, locations, friability classes,
            access risks, pricing triggers, assumptions, and exclusions — so you can quote with speed, confidence, and
            complete traceability.
          </p>
        </div>

        <div className="relative mt-14">
          <div className="absolute -inset-10 -z-10 rounded-[2.5rem] bg-gradient-to-tr from-cyan-500/20 via-violet-500/15 to-pink-500/10 blur-3xl" />
          <div className="overflow-hidden rounded-2xl border border-white/10 bg-night-800 shadow-[0_50px_140px_-30px_rgba(34,211,238,0.4)] ring-1 ring-white/5">
            <Image
              src="/marketing/extracted-intelligence.png"
              alt="Extracted intelligence dashboard: materials, locations, quantities, access risks, friability classes, pricing triggers, assumptions, and review items"
              width={1536}
              height={1024}
              className="h-auto w-full"
            />
          </div>
        </div>

        <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[
            { label: "Materials detected", note: "Per register row" },
            { label: "Access risks tagged", note: "No-access auto-flagged" },
            { label: "Friability classes", note: "Class A & Class B" },
            { label: "Pricing triggers", note: "Linked to pricebook rules" },
          ].map((item) => (
            <div key={item.label} className="rounded-xl border border-white/10 bg-white/[0.04] p-4 backdrop-blur-sm">
              <div className="text-[10px] font-semibold uppercase tracking-[0.16em] text-cyan-300">{item.label}</div>
              <div className="mt-1 text-sm font-medium text-ink">{item.note}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function Benefits() {
  return (
    <section id="benefits" className="relative mx-auto max-w-7xl px-5 py-20 lg:px-8">
      <div className="mx-auto max-w-2xl text-center">
        <div className="text-xs font-semibold uppercase tracking-[0.18em] text-cyan-300">Key benefits</div>
        <h2 className="mt-3 text-3xl font-semibold tracking-tight text-ink sm:text-4xl">
          Built for regulated site-services teams.
        </h2>
        <p className="mt-4 text-base leading-7 text-graphite">
          Designed around the real NZ asbestos and demolition workflow — and structured as multi-organisation SaaS so it
          scales across trading entities.
        </p>
      </div>

      <div className="mt-12 grid gap-5 md:grid-cols-2 lg:grid-cols-3">
        {benefits.map((item) => {
          const Icon = item.icon;
          return (
            <div
              key={item.title}
              className="group relative overflow-hidden rounded-2xl border border-white/10 bg-white/[0.04] p-6 backdrop-blur-sm transition hover:-translate-y-0.5 hover:border-white/20"
            >
              <div
                className={`pointer-events-none absolute -right-16 -top-16 h-40 w-40 rounded-full bg-gradient-to-br ${item.accent} blur-2xl`}
              />
              <div
                className={`relative grid h-10 w-10 place-items-center rounded-lg border border-white/10 bg-white/5 ${item.iconClass}`}
              >
                <Icon className="h-5 w-5" />
              </div>
              <h3 className="relative mt-4 text-base font-semibold text-ink">{item.title}</h3>
              <p className="relative mt-2 text-sm leading-6 text-graphite">{item.body}</p>
            </div>
          );
        })}
      </div>
    </section>
  );
}

function CallToAction() {
  return (
    <section id="cta" className="relative px-5 pb-24 lg:px-8">
      <div className="relative mx-auto max-w-6xl overflow-hidden rounded-3xl border border-white/10 bg-gradient-to-br from-night-700 via-night-800 to-night-700 px-8 py-14 shadow-[0_50px_140px_-30px_rgba(34,211,238,0.35)] sm:px-14">
        <div
          aria-hidden
          className="absolute inset-0 -z-10 [background-image:radial-gradient(circle_at_top_right,rgba(34,211,238,0.25),transparent_55%),radial-gradient(circle_at_bottom_left,rgba(139,92,246,0.25),transparent_55%)]"
        />

        <div className="grid items-center gap-10 lg:grid-cols-[1.2fr_1fr]">
          <div>
            <div className="text-xs font-semibold uppercase tracking-[0.18em] text-cyan-300">Request a walkthrough</div>
            <h2 className="mt-3 text-3xl font-semibold tracking-tight text-ink sm:text-4xl">
              See your survey become a quote in minutes.
            </h2>
            <p className="mt-4 max-w-xl text-base leading-7 text-graphite">
              Bring a real survey PDF. We&apos;ll walk you through extraction, pricing, review gates, and exporting a
              RAS-style quote or Fergus-ready CSV — live, on your data.
            </p>

            <div className="mt-8 flex flex-wrap gap-3">
              <a href="mailto:hello@privexa.co?subject=TraceQuote%20AI%20demo%20request" className="btn-primary px-5 py-3">
                Book a demo
                <ArrowRight className="h-4 w-4" />
              </a>
              <Link href="/login" className="btn-secondary px-5 py-3">
                Open the live demo
              </Link>
            </div>
          </div>

          <ul className="space-y-3 text-sm">
            {[
              "30-minute guided walkthrough",
              "Run on a survey you bring",
              "See pricing logic, no-access, Class A clearance",
              "Export PDF + Fergus CSV at the end",
            ].map((item) => (
              <li
                key={item}
                className="flex items-start gap-3 rounded-xl border border-white/10 bg-white/[0.04] p-4 backdrop-blur-sm"
              >
                <CheckCircle2 className="mt-0.5 h-5 w-5 flex-shrink-0 text-cyan-300" />
                <span className="text-ink">{item}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}

function SiteFooter() {
  return (
    <footer className="relative border-t border-white/5 bg-night-900/80">
      <div className="mx-auto flex max-w-7xl flex-col items-start justify-between gap-4 px-5 py-8 text-sm text-graphite md:flex-row md:items-center lg:px-8">
        <div className="flex items-center gap-2 font-semibold text-ink">
          <span className="grid h-7 w-7 place-items-center rounded-lg bg-grad-primary">
            <Sparkles className="h-3.5 w-3.5 text-night-900" />
          </span>
          {APP_NAME}
        </div>
        <div className="text-xs">
          © {new Date().getFullYear()} Privexa · Evidence-linked AI quoting for regulated site services.
        </div>
        <div className="flex items-center gap-5">
          <Link href="/login" className="transition hover:text-ink">Sign in</Link>
          <a href="mailto:hello@privexa.co" className="transition hover:text-ink">Contact</a>
        </div>
      </div>
    </footer>
  );
}
