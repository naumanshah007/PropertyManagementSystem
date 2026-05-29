from __future__ import annotations

import hashlib
import hmac
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from .document_parser import DEFAULT_ORGANISATION_ID, STORAGE_ROOT
from .config import get_settings
from .auth_tokens import create_access_token
from .repository import get_repository
from .organisation_store import (
    add_organisation_user,
    create_organisation,
    create_pricebook,
    get_organisation,
    list_pricebooks,
    upsert_organisation_settings,
)
from .schemas import (
    CreateOrganisationRequest,
    CreateOrganisationUserRequest,
    CreatePricebookRequest,
    DemoAuthSession,
    DemoAuthUserRecord,
    DemoLoginRequest,
    PricebookRule,
    Role,
    UpsertOrganisationSettingsRequest,
)


TEST_ORGANISATION_ID = "org-demo-asbestos-services"
AUTH_DIR = STORAGE_ROOT / "demo_auth"
AUTH_USERS_PATH = AUTH_DIR / "users.json"
HASH_ITERATIONS = 120_000


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _hash_password(password: str, salt: str) -> str:
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), HASH_ITERATIONS)
    return digest.hex()


def _new_user(email: str, name: str, role: Role, organisation_id: str | None, password: str) -> DemoAuthUserRecord:
    salt = uuid4().hex
    return DemoAuthUserRecord(
        id=f"demo-user-{uuid4().hex[:12]}",
        email=email,
        name=name,
        role=role,
        organisation_id=organisation_id,
        password_hash=_hash_password(password, salt),
        password_salt=salt,
        created_at=_now(),
    )


def seed_demo_auth_users() -> list[DemoAuthUserRecord]:
    settings = get_settings()
    admin_password = settings.demo_admin_password
    org_admin_password = settings.demo_org_admin_password
    if admin_password is None or org_admin_password is None:
        raise RuntimeError("Demo passwords are not configured. Set DEMO_ADMIN_PASSWORD and DEMO_ORG_ADMIN_PASSWORD.")
    users = [
        _new_user(settings.demo_admin_email, "Privexa Super Admin", "platform_admin", None, admin_password),
        _new_user(settings.demo_org_admin_email, "Test Organisation Admin", "organisation_admin", TEST_ORGANISATION_ID, org_admin_password),
    ]
    get_repository().put_auth_users(users)
    return users


def load_demo_auth_users() -> list[DemoAuthUserRecord]:
    repo = get_repository()
    if not repo.auth_users_exist():
        return seed_demo_auth_users()
    return repo.list_auth_users()


def demo_login(request: DemoLoginRequest) -> DemoAuthSession | None:
    email = request.email.lower().strip()
    for user in load_demo_auth_users():
        if user.email.lower() != email:
            continue
        candidate = _hash_password(request.password, user.password_salt)
        if not hmac.compare_digest(candidate, user.password_hash):
            return None
        default_route = "/admin" if user.role == "platform_admin" else "/dashboard"
        token = create_access_token(
            user_id=user.id,
            email=user.email,
            role=user.role,
            organisation_id=user.organisation_id,
        )
        return DemoAuthSession(
            token=token,
            email=user.email,
            name=user.name,
            role=user.role,
            organisation_id=user.organisation_id,
            default_route=default_route,
        )
    return None


def seed_demo_environment() -> dict[str, object]:
    if get_organisation(DEFAULT_ORGANISATION_ID) is None:
        # Both demo orgs use "Demo Asbestos Services Ltd" as their trading name so the
        # auto-derived business_name on the quote export matches the demo materials.
        create_organisation(
            CreateOrganisationRequest(
                name="TraceQuote Demo Organisation",
                slug="tracequote-demo",
                trading_name="Demo Asbestos Services Ltd",
                email="demo@tracequote.local",
            ),
            org_id=DEFAULT_ORGANISATION_ID,
        )

    if get_organisation(TEST_ORGANISATION_ID) is None:
        create_organisation(
            CreateOrganisationRequest(
                name="Demo Asbestos Services Ltd",
                slug="demo-asbestos-services",
                trading_name="Demo Asbestos Services Ltd",
                email="test@privexa.co",
            ),
            org_id=TEST_ORGANISATION_ID,
        )

    upsert_organisation_settings(
        TEST_ORGANISATION_ID,
        UpsertOrganisationSettingsRequest(
            gst_rate=0.15,
            default_margin=0.20,
            default_currency="NZD",
            quote_prefix="TQD",
            require_review_for_class_a=True,
            require_review_for_no_access=True,
        ),
    )
    # The auto-seeded RAS-1285 starter is created by create_organisation above. For the
    # test/demo org we layer on a richer demo pricebook (travel, surcharges, PPE, etc.)
    # which deactivates the starter via the standard SaaS semantics.
    if not any(p.version == "demo-v1" for p in list_pricebooks(TEST_ORGANISATION_ID)):
        create_pricebook(
            TEST_ORGANISATION_ID,
            CreatePricebookRequest(
                name="Demo asbestos services pricebook",
                version="demo-v1",
                rules=_demo_pricebook_rules(TEST_ORGANISATION_ID),
            ),
        )

    existing_users = {user.email for user in load_demo_auth_users()}
    settings = get_settings()
    if not {settings.demo_admin_email, settings.demo_org_admin_email}.issubset(existing_users):
        seed_demo_auth_users()

    if not any(user.email == settings.demo_org_admin_email for user in _safe_org_users(TEST_ORGANISATION_ID)):
        add_organisation_user(
            TEST_ORGANISATION_ID,
            CreateOrganisationUserRequest(email=settings.demo_org_admin_email, name="Test Organisation Admin", role="organisation_admin"),
        )

    return {
        "organisation_id": TEST_ORGANISATION_ID,
        "demo_users": [user.email for user in load_demo_auth_users()],
        "pricebooks": len(list_pricebooks(TEST_ORGANISATION_ID)),
    }


def _safe_org_users(org_id: str):
    from .organisation_store import list_organisation_users

    return list_organisation_users(org_id)


def _demo_pricebook_rules(org_id: str) -> list[PricebookRule]:
    data = [
        ("pb-site-establishment", "Site establishment", "Site Establishment", "item", 1850, 1.0, 0.20),
        ("pb-class-a-friable-removal", "Class A friable removal", "Class A / Friable Removal", "allowance", 3500, 1.35, 0.25),
        ("pb-class-b-non-friable-removal", "Class B non-friable removal", "Class B Removal", "allowance", 1200, 1.10, 0.20),
        ("pb-fibre-cement-sheet-sqm", "Fibre cement sheet per sqm", "Class B Removal", "sqm", 42.5, 1.10, 0.20),
        ("pb-insulating-board-piece", "Insulating board per piece", "Class A / Friable Removal", "piece", 650, 1.35, 0.25),
        ("pb-no-access-investigation", "No-access/provisional investigation", "Provisional / No Access", "allowance", 750, 1.20, 0.20),
        ("pb-waste-disposal", "Waste disposal", "Waste / Disposal Placeholder", "allowance", 1800, 1.15, 0.20),
        ("pb-encapsulation", "Encapsulation allowance", "Encapsulation / Provisional Allowance", "allowance", 1250, 1.10, 0.20),
        ("pb-minimum-job", "Minimum job charge", "Commercial Minimum", "item", 2500, 1.0, 0.20),
        ("pb-gst", "GST", "Tax", "percent", 0.15, 1.0, 0.0),
        ("pb-margin", "Margin", "Commercial Margin", "percent", 0.20, 1.0, 0.0),
        ("pb-scaffolding", "Scaffolding allowance", "Access", "allowance", 2500, 1.15, 0.20),
        ("pb-travel", "Travel charge", "Travel", "km", 2.2, 1.0, 0.20),
        ("pb-after-hours", "After-hours surcharge", "Surcharge", "percent", 0.25, 1.0, 0.0),
        ("pb-emergency", "Emergency surcharge", "Surcharge", "percent", 0.35, 1.0, 0.0),
        ("pb-ppe-rpe", "PPE/RPE allowance", "Controls", "person", 95, 1.0, 0.20),
        ("pb-decon-unit", "Decontamination unit", "Controls", "day", 450, 1.0, 0.20),
        ("pb-supervisor", "Supervisor hourly rate", "Labour", "hour", 95, 1.0, 0.20),
        ("pb-equipment-hire", "Equipment hire", "Equipment", "day", 380, 1.0, 0.20),
        ("pb-assessor-clearance", "Assessor/clearance note", "Assessor", "allowance", 900, 1.0, 0.20),
        ("pb-reinstatement-exclusion", "Reinstatement exclusion", "Exclusions", "excluded", None, 1.0, 0.0),
    ]
    material_matches = {
        "pb-class-a-friable-removal": "friable generic unmatched",
        "pb-class-b-non-friable-removal": "non-friable generic unmatched",
        "pb-fibre-cement-sheet-sqm": "fibre cement sheet",
        "pb-insulating-board-piece": "insulating board, aib",
        "pb-no-access-investigation": "power, electric, board, box",
        "pb-encapsulation": "encapsulation, seal, residual",
    }
    class_matches = {
        "pb-class-a-friable-removal": "Class A",
        "pb-insulating-board-piece": "Class A",
        "pb-class-b-non-friable-removal": "Class B",
        "pb-fibre-cement-sheet-sqm": "Class B",
    }
    access_matches = {
        "pb-no-access-investigation": "no-access",
    }
    pricing_methods = {
        "sqm": "per_sqm",
        "piece": "per_piece",
        "person": "per_piece",
        "item": "fixed",
        "allowance": "fixed",
        "percent": "fixed",
        "km": "fixed",
        "day": "fixed",
        "hour": "per_hour",
        "excluded": "excluded",
    }
    mandatory = {
        "pb-site-establishment",
        "pb-class-a-friable-removal",
        "pb-class-b-non-friable-removal",
        "pb-fibre-cement-sheet-sqm",
        "pb-insulating-board-piece",
        "pb-no-access-investigation",
        "pb-waste-disposal",
        "pb-encapsulation",
        "pb-minimum-job",
        "pb-gst",
        "pb-margin",
    }
    return [
        PricebookRule(
            id=rule_id,
            organisation_id=org_id,
            name=name,
            category=section,
            section=section,
            material_match=material_matches.get(rule_id),
            class_match=class_matches.get(rule_id),  # type: ignore[arg-type]
            access_match=access_matches.get(rule_id, "normal"),  # type: ignore[arg-type]
            pricing_method=pricing_methods.get(unit, "fixed"),  # type: ignore[arg-type]
            unit=unit,
            unit_rate=rate,
            risk_multiplier=risk,
            margin=margin,
            gst_taxable=rule_id not in {"pb-gst", "pb-margin", "pb-reinstatement-exclusion"},
            minimum_charge=2500 if rule_id == "pb-minimum-job" else None,
            assumptions=["Demo seed rule for vendor walkthrough."],
            exclusions=["Estimator must review before client issue."],
            review_required=rule_id
            in {
                "pb-site-establishment",
                "pb-class-a-friable-removal",
                "pb-insulating-board-piece",
                "pb-no-access-investigation",
                "pb-waste-disposal",
                "pb-encapsulation",
            },
            mandatory=rule_id in mandatory,
        )
        for rule_id, name, section, unit, rate, risk, margin in data
    ]
