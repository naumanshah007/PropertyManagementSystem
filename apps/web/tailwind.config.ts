import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Semantic tokens — repointed at a premium dark-SaaS palette.
        // Names kept stable so existing class usage across the app
        // (bg-paper, text-ink, border-line, text-graphite, text-moss)
        // picks up the new theme without per-file edits.
        paper: "#040814",
        ink: "#e6edf7",
        graphite: "#94a3b8",
        line: "rgba(255,255,255,0.08)",
        moss: "#22d3ee",

        night: {
          900: "#040814",
          800: "#070d1c",
          700: "#0a1530",
          600: "#0e1a3a",
          500: "#152244",
        },

        hazard: "#f97316",
        attention: "#fb923c",
        verified: "#34d399",
        blocked: "#fb7185",
      },
      backgroundImage: {
        "grad-primary": "linear-gradient(135deg, #22d3ee 0%, #8b5cf6 100%)",
        "grad-accent": "linear-gradient(135deg, #22d3ee 0%, #38bdf8 50%, #a78bfa 100%)",
      },
      boxShadow: {
        panel: "0 1px 2px rgba(0,0,0,0.4), 0 8px 32px -4px rgba(2,6,23,0.6)",
        glow: "0 0 30px -4px rgba(34,211,238,0.45)",
        "glow-violet": "0 0 30px -4px rgba(139,92,246,0.45)",
      },
    },
  },
  plugins: [],
};

export default config;
