#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
API_ROOT = REPO_ROOT / "services" / "api"
sys.path.insert(0, str(API_ROOT))

from app.config import get_settings  # noqa: E402
from app.database import DatabaseUnavailable, latest_schema_sql, run_local_sqlite_migration, run_turso_migration, validate_schema_sql  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Run or validate TraceQuote AI database migrations.")
    parser.add_argument("--dry-run", action="store_true", help="Validate migration SQL without connecting to Turso.")
    parser.add_argument("--sqlite-path", default=str(API_ROOT / "storage" / "tracequote_local.db"))
    args = parser.parse_args()

    validate_schema_sql(latest_schema_sql())
    settings = get_settings()

    if args.dry_run:
        print("Migration SQL validated successfully.")
        print(f"DATABASE_PROVIDER={settings.database_provider}")
        return 0

    if settings.database_provider == "json":
        run_local_sqlite_migration(Path(args.sqlite_path))
        print(f"JSON mode remains active. SQLite schema validation DB written to {args.sqlite_path}.")
        return 0

    if settings.database_provider == "turso":
        try:
            asyncio.run(run_turso_migration())
        except DatabaseUnavailable as exc:
            print(str(exc), file=sys.stderr)
            print("For local JSON mode, set DATABASE_PROVIDER=json or run scripts/db_migrate.py --dry-run.", file=sys.stderr)
            return 2
        print("Turso migration completed.")
        return 0

    print(f"Unsupported DATABASE_PROVIDER={settings.database_provider}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
