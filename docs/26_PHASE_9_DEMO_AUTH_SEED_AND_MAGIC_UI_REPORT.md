# Phase 9 Demo Auth, Seed, and Magic UI Report

## Scope

Phase 9 turns the local POC into a smoother SaaS-style demo by adding demo-only authentication, a seeded asbestos services organisation, a seeded pricebook, and a polished extracted-intelligence view.

This phase does not add production authentication, ML, LLM quote writing, billing, or Fergus integration.

## Implemented

- Demo login endpoint with salted PBKDF2 password hashing.
- Demo logout endpoint.
- Local demo session support in the frontend.
- Login page with role-aware redirects.
- Seeded super admin account: `admin@privexa.co`.
- Seeded organisation admin account: `test@privexa.co`.
- Seeded organisation: `Demo Asbestos Services Ltd`.
- Seeded organisation settings: 15% GST, 20% default margin, NZD, `TQD` quote prefix.
- Seeded asbestos services pricebook with mandatory and optional demo rules.
- Demo seed/reset scripts that rebuild users, organisation, settings, pricebook, and the Tauraroa workflow.
- Organisation admin landing page for users, settings, pricebook, and estimator workups.
- Platform admin organisation directory and seeded demo org links.
- Document Intelligence “Extracted Intelligence” panel.
- Magic extraction summary endpoint.
- Register table polish showing pricing relevance and mapped quote action.

## Demo Auth Model

Authentication is deliberately local/demo-only:

- Passwords are never stored as plain text.
- Password verification uses salted PBKDF2 hashes.
- Returned tokens are simple local demo tokens.
- The frontend stores the demo session in local storage.
- There is no production identity provider, refresh-token flow, MFA, SSO, or server-side session database in this phase.

Role redirects:

- `platform_admin` -> `/admin`
- `organisation_admin` -> `/org`
- `estimator` and `reviewer` -> `/workups`

## Seeded Pricebook

Mandatory seed rules include:

- Site establishment
- Class A friable removal
- Class B non-friable removal
- Fibre cement sheet per sqm
- Insulating board per piece
- No-access/provisional investigation
- Waste disposal
- Encapsulation allowance
- Minimum job charge
- GST
- Margin

Optional demo rules include:

- Scaffolding allowance
- Travel charge
- After-hours surcharge
- Emergency surcharge
- PPE/RPE allowance
- Decontamination unit
- Supervisor hourly rate
- Equipment hire
- Assessor/clearance note
- Reinstatement exclusion

## Magic Extraction Summary

The backend summary combines deterministic outputs already created by earlier phases:

- Parsed document metadata
- Register extraction
- Quote candidate mapping
- Priced quote lines

The frontend displays:

- Survey type
- Total pages parsed
- Register items extracted
- Quote candidates generated
- Priced lines generated
- Class A item count
- Class B item count
- No-access item count
- Limited-access item count
- NAD/excluded count
- Total extracted sqm
- Source pages detected
- Confidence summary
- Materials, locations, quantities, access risks, friability classes, recommendations, pricing triggers, assumptions, and exclusions

## Demo Flow

1. Run `python3 scripts/demo_reset.py`.
2. Start FastAPI.
3. Start Next.js.
4. Open `/login`.
5. Log in as `admin@privexa.co` to see the platform admin view.
6. Log in as `test@privexa.co` to see the test organisation admin view.
7. Open the Tauraroa workup and Document Intelligence.
8. Upload or use the seeded Tauraroa survey workflow.
9. Reveal extracted intelligence.
10. Continue through quote candidate generation, pricing, review gates, and export.

## Verification

Phase 9 adds backend tests for:

- Demo user seeding.
- Password hashes not matching plain passwords.
- Super admin login.
- Test organisation admin login.
- Wrong-password rejection.
- Seeded test organisation pricebook.
- Role-aware access metadata.
- Magic extraction summary generation.

Frontend verification covers TypeScript contracts and production build.

## Known Limitations

- Demo auth is not production-ready and should be replaced before real deployment.
- Local storage is still JSON/file based.
- Frontend role access is demo navigation, not a security boundary.
- Pricebook editing remains a demo placeholder.
- Magic extraction is a deterministic summary of existing parser/extractor/pricing outputs, not an LLM analysis layer.
