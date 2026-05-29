# Phase 1 Audit Report

## Verdict

Phase 1 is substantially complete as a local vendor-demo shell. It reflects the core TraceQuote AI constitution: quote work is evidence-linked, human review is visible, AI draft state is separated from approval, no-access/Class A items are flagged, and export remains blocked.

The main issues before Phase 2 are not architectural blockers, but they should be fixed before a serious vendor demo:

- The frontend uses duplicated local demo data instead of consuming the FastAPI demo contract.
- Pricing math in the mock quote lines is commercially inconsistent with the displayed margin/risk fields.
- The implementation uses `/export` for Review & Export while the Phase 1 feature brief names `/approval`.
- Positive/NAD status chip coverage is incomplete.
- Backend schemas represent the domain entities but do not yet enforce some constitution invariants.

## Findings

### High Priority

1. **Frontend and backend demo contracts can drift**

   Evidence:

   - Backend demo payload: `services/api/app/demo_data.py`
   - Frontend duplicate payload: `apps/web/src/lib/demo-data.ts`
   - Frontend screens import `demoWorkup` locally instead of fetching `GET /workups/tw-tauraroa-school-001`.

   Impact:

   The product currently has a contract-first backend and a polished frontend, but the frontend does not prove that it can consume the backend contract. This weakens the Phase 1 acceptance criterion that the frontend can reach the backend locally.

   Recommended fix:

   Add a small API client in `apps/web/src/lib/api.ts` and have the dashboard/detail/evidence/quote/export screens fetch the demo workup from FastAPI with a local fallback for offline demo mode.

2. **Mock quote pricing is not internally consistent**

   Evidence:

   - `QuoteLine` includes `base_cost`, `risk_multiplier`, `margin`, `gst`, and `total`.
   - Several demo totals appear to apply GST but not margin, even though a margin value is displayed.

   Impact:

   The quote builder looks credible at a UI level, but an estimator or business owner may notice that totals do not reconcile with the visible commercial fields. This undermines the "pricing must be explainable" non-negotiable.

   Recommended fix:

   Either calculate totals consistently from one formula or rename fields so Phase 1 does not imply a formula it is not applying. Before vendor demo, show base, risk-adjusted subtotal, margin, GST, and total consistently.

3. **Route mismatch with Phase 1 feature brief**

   Evidence:

   - `docs/10_PHASE_1_FEATURE_BRIEF.md` specifies `/workups/[id]/approval`.
   - Implementation provides `/workups/[id]/export`.

   Impact:

   The screen exists and satisfies the workflow, but the route contract differs from the feature brief. This can confuse future implementation tasks and acceptance checks.

   Recommended fix:

   Add `/workups/[id]/approval` as an alias/redirect to `/workups/[id]/export`, or update the spec to make `/export` the canonical route.

### Medium Priority

4. **Positive and NAD chip coverage is incomplete**

   Evidence:

   - `docs/10_PHASE_1_FEATURE_BRIEF.md` calls for chips for Class A, Class B, No Access, Presumed, Positive, and NAD.
   - The UI currently displays Class A, Class B, No Access, Limited Access, and Presumed.
   - Positive values are present in data but not surfaced as chips.
   - No NAD demo item exists.

   Impact:

   Risk visibility is good for high-risk items, but the register review table does not yet show the full expected status vocabulary.

   Recommended fix:

   Add `Positive` and `NAD` chip rendering to the register table. Add a small NAD row only if the demo needs to show excluded material handling.

5. **Backend schemas match entities but do not enforce all invariants**

   Evidence:

   - Required models exist: `QuoteWorkup`, `SourceDocument`, `SourceEvidence`, `AsbestosRegisterItem`, `QuoteLine`, `PricingRule`, `EstimatorEdit`, and `AuditEvent`.
   - `QuoteLine.source_evidence_ids` is typed as `list[str]` but not constrained to non-empty.
   - `pricing_rule_ids` is also unconstrained.
   - Review/export gate logic is represented in demo data but not enforced by service logic.

   Impact:

   The API shape is good for Phase 1, but it does not yet encode the constitution strongly enough to prevent untraceable quote lines.

   Recommended fix:

   Use Pydantic constraints such as `Field(min_length=1)` for quote-line source evidence and pricing rule links. Add a service-level export readiness validator before Phase 2 export work.

6. **Phase 1 backend endpoint coverage is narrower than the feature brief**

   Evidence:

   - Implemented: `GET /health`, `GET /workups`, `GET /workups/{workup_id}`, `GET /workups/{workup_id}/register-items`, `GET /workups/{workup_id}/quote-lines`, `GET /workups/{workup_id}/audit-events`.
   - `docs/10_PHASE_1_FEATURE_BRIEF.md` also lists `POST /workups` and `POST /workups/{workup_id}/documents`.

   Impact:

   The user-requested Phase 1 implementation emphasized demo endpoints, so this is not a blocker. But the feature brief is not fully satisfied.

   Recommended fix:

   Add placeholder POST endpoints that return deterministic created/accepted responses without real persistence.

7. **Manual mirrored types are acceptable for Phase 1 but should be generated soon**

   Evidence:

   - Backend Pydantic schemas are in `services/api/app/schemas.py`.
   - Frontend TypeScript interfaces are in `apps/web/src/lib/types.ts`.

   Impact:

   The duplication is currently manageable, but it will become a drift risk when Phase 2 adds extraction payloads and parser errors.

   Recommended fix:

   Generate frontend types from OpenAPI or introduce a contract generation step before expanding the API.

### Low Priority

8. **No dedicated lint script exists**

   Evidence:

   - `npm run build` performs Next's integrated checks.
   - `npm run typecheck` exists.
   - No separate `lint` script is configured.

   Impact:

   This is acceptable for Phase 1, but a lint script will be useful as the frontend grows.

   Recommended fix:

   Add ESLint/Next lint configuration or a minimal lint script before Phase 2 UI expansion.

9. **Running `next build` while `next dev` is active can temporarily break the dev server**

   Evidence:

   During audit, running frontend verification while the dev server was already using `.next` caused the dev server to return a temporary 500 until restarted. Sequential README commands pass.

   Impact:

   This is a development workflow issue, not a product bug.

   Recommended fix:

   Avoid running `npm run build` while `npm run dev` is active in the same app directory, or document that the dev server should be restarted after production builds.

10. **npm audit reports two moderate advisories**

   Evidence:

   `npm install` reported two moderate severity advisories.

   Impact:

   No immediate Phase 1 blocker, but it should be reviewed before a public or hosted demo.

   Recommended fix:

   Run `npm audit` and assess whether non-breaking dependency updates are available.

## Product Constitution Coverage

| Requirement | Status | Notes |
| --- | --- | --- |
| Traceability visible | Pass | Register and quote tables show evidence/source page placeholders. |
| Human review visible | Pass | Review-required and blocked states are shown throughout dashboard, cockpit, quote, and export screens. |
| AI draft vs approved output separated | Pass | Draft quote total is explicitly not approved; no quote line defaults to approved. |
| No-access areas flagged | Pass | Power box and power board box are no-access and review-required. |
| Class A visible | Pass | Chimney AIB is Class A and review-required. |
| Export blocked until review resolved | Pass | Export page has blocked checklist and disabled export package actions. |
| Pricing explainable | Partial | `why`, evidence, and pricing fields are visible, but calculation consistency needs work. |
| Estimator edits recorded | Partial | Demo includes an `EstimatorEdit`, but UI does not yet surface estimator edit history outside audit context. |
| No regulatory approval claim | Pass | Exclusions explicitly avoid licensed assessor/regulatory approval claims. |

## Backend Schema Coverage

| Domain Entity | Implemented | Notes |
| --- | --- | --- |
| `QuoteWorkup` | Yes | Includes documents, evidence, register items, risks, quote lines, pricing rules, edits, audit events, assumptions, exclusions, export status. |
| `SourceDocument` | Yes | Includes file metadata, page count, parser version, OCR status. |
| `SourceEvidence` | Yes | Includes page number, evidence type, raw text, confidence, optional bounding box. |
| `AsbestosRegisterItem` | Yes | Includes location, material, quantity, result, class, access, evidence, confidence, review status. |
| `QuoteLine` | Yes | Includes quantity, unit, rate, cost fields, evidence, pricing rules, assumptions, exclusions, review/approval status, rationale. |
| `PricingRule` | Yes | Includes formula and assumptions/exclusions but not match conditions from the full domain spec. |
| `EstimatorEdit` | Yes | Includes previous/new values, reason, user, timestamp. |
| `AuditEvent` | Yes | Includes actor, event type, payload, timestamp. |

Schema gaps to address before Phase 2:

- Add non-empty evidence constraints for quote lines.
- Add non-empty pricing-rule constraints where generated pricing is used.
- Consider using `date` for `due_date` rather than `str`.
- Consider bounded literals for `event_type`, `evidence_type`, `access_status`, and `friability_class`.

## Demo Data Coverage

| Golden Output Requirement | Status | Notes |
| --- | --- | --- |
| Tauraroa Area School workup | Pass | Demo workup uses Tauraroa Area School. |
| Asbestos Demolition Survey | Pass | `survey_type` is correct. |
| 320 sqm Class B external flat cladding | Pass | Present with source evidence. |
| 1 sqm power box presumed/no access | Pass | Present and review-required. |
| Chimney hidden AIB Class A/limited access | Pass | Present and review-required. |
| 920 sqm Class B external cladding | Pass | Present with source evidence. |
| Power board box presumed/no access | Pass | Present and review-required. |
| Expected quote sections | Pass | Site establishment, Class B removal, Class A/friable, no-access investigation, waste disposal, encapsulation/provisional, assumptions/exclusions are represented. |
| Blocked export state | Pass | `export_status` is `blocked`. |
| No approved-by-default lines | Pass | All quote lines have `approval_status: not_ready`. |

## UI/UX Assessment

Overall UI quality: strong Phase 1 pass.

Strengths:

- The UI feels like an operational enterprise SaaS tool, not a chatbot.
- The left navigation, work queue, KPI cards, evidence table, and quote table are appropriate for estimator workflow.
- The dashboard is credible for a vendor walkthrough.
- The workflow timeline is clear and uses the correct sequence: Intake, Extraction, Evidence Review, Quote Draft, Approval, Export.
- Tables are readable and use horizontal overflow where needed.
- Confidence, class, access risk, and review statuses are visible in the document intelligence screen.
- Quote builder shows source evidence and commercial fields, making the draft feel traceable.

Weak spots:

- The dashboard could be more impressive with a review queue table, extraction confidence KPI, and "Needs More Info" card from the UX spec.
- Quote builder should show risk multiplier and margin as explicit columns or in an expandable pricing panel.
- The document intelligence screen is still clearly a placeholder PDF viewer, which is acceptable for Phase 1 but should be Phase 2's first visible upgrade.
- Estimator edit history is present in data but not clearly surfaced as a learning/audit signal.

## Engineering Assessment

Strengths:

- Clean separation between FastAPI backend, Next.js frontend, worker placeholder, and schema notes.
- API boundaries are clear and OpenAPI is enabled by FastAPI.
- Smoke tests cover health, workup, register items, quote lines, and audit events.
- No ML, billing, multi-tenancy, Fergus integration, or fake regulatory claim was implemented.
- No broken imports were found during build/typecheck.

Risks:

- Frontend does not yet consume backend API.
- Demo data and contracts are manually duplicated.
- Some domain invariants are test-level/demo-level only, not schema-enforced.
- No frontend route smoke test exists yet.

## Verification Results

Commands run:

```bash
cd services/api
source .venv/bin/activate
PYTHONPATH=. pytest
```

Result:

```text
5 passed
```

Commands run sequentially:

```bash
cd apps/web
npm run typecheck
npm run build
```

Result:

```text
typecheck passed
production build passed
```

Local endpoint checks:

```text
GET http://127.0.0.1:8000/health -> 200 OK
GET http://127.0.0.1:3000 -> 200 OK when dev server is running cleanly
```

Note:

Do not run `npm run build` while `npm run dev` is active in the same directory unless you are prepared to restart the dev server.

## Prioritized Fix List

### P0: Before Phase 2 Implementation

1. Connect frontend pages to the FastAPI demo workup endpoint, with a local mock fallback only if the API is unavailable.
2. Normalize quote-line pricing math or simplify the displayed pricing fields so totals reconcile.
3. Add `/workups/[id]/approval` alias/redirect or update the Phase 1 feature brief to use `/export` consistently.

### P1: Before Vendor Demo

4. Add Positive and NAD chip support in the register table.
5. Add explicit risk multiplier and margin visibility to the quote builder.
6. Surface estimator edit history on the workup cockpit or export/audit screen.
7. Add placeholder POST endpoints for workup creation and document upload.
8. Add schema constraints for quote-line evidence and pricing-rule links.

### P2: Before Larger Phase 2 Expansion

9. Generate TypeScript contracts from FastAPI OpenAPI or centralize schema generation.
10. Add frontend route smoke tests.
11. Add a lint script.
12. Review npm audit advisories.

