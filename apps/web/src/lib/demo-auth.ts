"use client";

import type { DemoAuthSession } from "./types";

const DEMO_SESSION_KEY = "tracequote:demoSession";

export function saveDemoSession(session: DemoAuthSession) {
  localStorage.setItem(DEMO_SESSION_KEY, JSON.stringify(session));
}

export function readDemoSession(): DemoAuthSession | null {
  const raw = localStorage.getItem(DEMO_SESSION_KEY);
  if (!raw) {
    return null;
  }
  try {
    return JSON.parse(raw) as DemoAuthSession;
  } catch {
    return null;
  }
}

export function clearDemoSession() {
  localStorage.removeItem(DEMO_SESSION_KEY);
}
