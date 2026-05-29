# TraceQuote AI Product Constitution

## Mission

TraceQuote AI is an enterprise AI estimator workbench for regulated site-services businesses. It converts asbestos, demolition, remediation, and hazardous-cleaning reports into traceable, human-reviewed quote drafts.

## Core Principle

The system must never produce an untraceable final quote. Every quote line must be linked to source evidence, pricing logic, assumptions, exclusions, and human approval status.

## First Vertical

Asbestos removal and demolition quoting.

## Primary User

Estimator or project manager at an asbestos removal company.

## Secondary Users

Business owner, operations manager, compliance manager, administrator.

## Core Workflow

1. Upload asbestos survey/report.
2. Parse PDF text, tables, and pages.
3. Detect survey type and quote suitability.
4. Extract asbestos register items.
5. Extract no-access and limited-access warnings.
6. Convert findings into quote line items.
7. Apply rule-based pricebook and similar quote retrieval.
8. Require estimator review.
9. Export client-facing quote package.
10. Store estimator edits as training data.

## Non-Negotiables

- Human approval is required before final quote.
- AI must show source page and evidence.
- No-access areas must be flagged.
- Presumed asbestos must be treated as provisional and review-required.
- Class A/Class B must be visible.
- Pricing must be explainable.
- All estimator edits must be recorded.
- The system must not claim regulatory approval.

## MVP Definition

A vendor-demo-ready product that can upload the provided asbestos survey, extract register items, generate editable quote lines, show risk flags, and export a professional quote draft.

## Out of Scope for First Build

- Billing
- Multi-tenant SaaS
- Construction support
- Full ML training
- Fergus live API integration
- Mobile app

## Product Promise

TraceQuote AI gives estimators a governed workbench that reads the survey, prepares the first quote draft, shows the evidence behind every line, and learns from every correction.

