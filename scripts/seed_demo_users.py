#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
API_ROOT = REPO_ROOT / "services" / "api"

# Default APP_ENV to "local" so Phase F's tightened password fallback works for
# this local-seed script. Explicit env values from the operator still win.
os.environ.setdefault("APP_ENV", "local")

sys.path.insert(0, str(API_ROOT))

from app.config import get_settings  # noqa: E402
from app.demo_auth import seed_demo_environment  # noqa: E402


def main() -> int:
    if not get_settings().demo_seed_enabled:
        print("Demo seed is disabled. Set DEMO_SEED_ENABLED=true to seed local demo users.", file=sys.stderr)
        return 2
    result = seed_demo_environment()
    print("TraceQuote AI demo auth seed complete.")
    print(f"Organisation: {result['organisation_id']}")
    print("Users: admin@privexa.co, test@privexa.co")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
