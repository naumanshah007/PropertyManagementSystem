"""Turso (libsql) repository backend — parity with the JSON backend.

Drives the real store functions (organisation_store, job_store, demo_auth)
with `DATABASE_PROVIDER=turso` pointed at a throwaway local libsql file, so the
production persistence path is exercised end-to-end without cloud credentials.
"""

from __future__ import annotations

import os
import tempfile

import pytest

from auth_helpers import PLATFORM_ADMIN_HEADERS  # noqa: F401 (ensures APP_ENV=local)


@pytest.fixture()
def turso_env(monkeypatch: pytest.MonkeyPatch):
    """Point the repository at a fresh local libsql file for this test."""
    import app.repository as repo_module

    db_path = os.path.join(tempfile.mkdtemp(), "turso_test.db")
    monkeypatch.setenv("DATABASE_PROVIDER", "turso")
    monkeypatch.setenv("TURSO_DATABASE_URL", f"file:{db_path}")
    repo_module._repository_for.cache_clear()
    try:
        yield
    finally:
        # Close the libsql client (non-daemon executor thread) so pytest exits cleanly.
        repo = repo_module._repository_for("turso")
        close = getattr(repo, "close", None)
        if callable(close):
            close()
        repo_module._repository_for.cache_clear()


def test_backend_is_turso(turso_env) -> None:
    from app.repository import TursoRepository, get_repository

    assert isinstance(get_repository(), TursoRepository)


def test_org_pricebook_lifecycle_on_turso(turso_env) -> None:
    from app.organisation_store import (
        create_organisation,
        create_pricebook,
        get_active_pricebook,
        get_organisation,
        list_organisations,
        list_pricebooks,
    )
    from app.schemas import CreateOrganisationRequest, CreatePricebookRequest

    org = create_organisation(
        CreateOrganisationRequest(name="Turso Co", trading_name="Turso Co", email="turso@example.com")
    )
    # Round-trips out of libsql.
    assert get_organisation(org.id) is not None
    assert org.id in {o.id for o in list_organisations()}

    # Auto-seeded starter pricebook is active.
    starter = get_active_pricebook(org.id)
    assert starter is not None and starter.active is True
    assert len(starter.rules) == 10

    # Newest pricebook deactivates the starter (SaaS semantics) — persisted in libsql.
    second = create_pricebook(org.id, CreatePricebookRequest(name="FY26", version="fy26", rules=[]))
    assert second is not None
    books = {b.version: b for b in list_pricebooks(org.id)}
    assert books["fy26"].active is True
    assert books[starter.version].active is False


def test_org_users_and_settings_on_turso(turso_env) -> None:
    from app.organisation_store import (
        add_organisation_user,
        create_organisation,
        get_organisation_settings,
        list_organisation_users,
        upsert_organisation_settings,
    )
    from app.schemas import (
        CreateOrganisationRequest,
        CreateOrganisationUserRequest,
        UpsertOrganisationSettingsRequest,
    )

    org = create_organisation(
        CreateOrganisationRequest(name="Turso Users Co", trading_name="Turso Users Co", email="u@example.com")
    )
    add_organisation_user(org.id, CreateOrganisationUserRequest(email="est@example.com", name="Est", role="estimator"))
    users = list_organisation_users(org.id)
    assert any(u.email == "est@example.com" for u in users)

    upsert_organisation_settings(org.id, UpsertOrganisationSettingsRequest(quote_prefix="ZZZ"))
    assert get_organisation_settings(org.id).quote_prefix == "ZZZ"


def test_jobs_on_turso(turso_env) -> None:
    from app.organisation_store import create_organisation
    from app.job_store import create_job, get_job, list_jobs, set_status
    from app.schemas import CreateOrganisationRequest

    org = create_organisation(
        CreateOrganisationRequest(name="Turso Jobs Co", trading_name="Turso Jobs Co", email="j@example.com")
    )
    job = create_job(org.id, document_id="doc-1", file_name="s.pdf", survey_type="demolition_survey", quotable=True)
    assert get_job(org.id, job.id) is not None
    assert [j.id for j in list_jobs(org.id)] == [job.id]

    set_status(org.id, job.id, "priced", total_inc_gst=1234.5)
    reloaded = get_job(org.id, job.id)
    assert reloaded.status == "priced"
    assert reloaded.total_inc_gst == 1234.5


def test_auth_users_seed_and_load_on_turso(turso_env) -> None:
    from app.demo_auth import load_demo_auth_users

    users = load_demo_auth_users()  # seeds on first call
    emails = {u.email for u in users}
    assert "admin@privexa.co" in emails
    # Reload comes back out of libsql (not re-seeded).
    again = load_demo_auth_users()
    assert {u.email for u in again} == emails
    assert all(u.password_hash for u in again)
