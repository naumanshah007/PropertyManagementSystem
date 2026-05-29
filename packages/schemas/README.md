# Shared Contracts

Phase 1 keeps contracts in two mirrored places:

- Backend Pydantic models: `services/api/app/schemas.py`
- Frontend TypeScript types: `apps/web/src/lib/types.ts`

The important contract models are:

- `QuoteWorkup`
- `SourceDocument`
- `SourceEvidence`
- `AsbestosRegisterItem`
- `QuoteLine`
- `PricingRule`
- `EstimatorEdit`
- `AuditEvent`

Phase 2 can generate TypeScript types from the backend OpenAPI schema or centralize schemas here.

