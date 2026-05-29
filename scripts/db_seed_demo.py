#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
API_ROOT = REPO_ROOT / "services" / "api"
sys.path.insert(0, str(API_ROOT))

from app.config import get_settings  # noqa: E402
from app.demo_auth import seed_demo_environment  # noqa: E402


def main() -> int:
    settings = get_settings()
    if not settings.demo_seed_enabled:
        print("Demo seed is disabled. Set DEMO_SEED_ENABLED=true for local/staging demo seeding.", file=sys.stderr)
        return 2
    result = seed_demo_environment()
    print("Demo seed complete.")
    print(f"Organisation ID: {result['organisation_id']}")
    print(f"Users: {', '.join(result['demo_users'])}")
    print(f"Pricebooks: {result['pricebooks']}")
    if settings.database_provider == "turso":
        print("Note: structured app data still uses JSON repositories in this phase; Turso schema is migration-ready.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
