# Security And Compliance Spec

## Objective

Protect client documents, estimator decisions, and quote history while avoiding unsupported regulatory claims.

## MVP Security Requirements

- Store uploaded files outside the web root.
- Use generated file identifiers instead of trusting original filenames.
- Validate file type and size at upload.
- Keep extracted text associated with source document IDs.
- Record audit events for parsing, edits, approvals, and exports.
- Separate client-facing exports from internal evidence and audit outputs.

## Access Model

Initial roles:

- Administrator
- Estimator
- Reviewer
- Read-only manager

MVP can use a placeholder auth layer, but the domain model must preserve `user_id` and role fields so enterprise auth can be added later.

## Compliance Language

The product must not claim:

- Regulatory approval
- Certified asbestos assessment
- Replacement of licensed assessors
- Replacement of estimator judgement
- Guaranteed pricing accuracy

Approved positioning:

- Draft quote generation
- Evidence-linked extraction
- Human-reviewed estimator workbench
- Internal QA and traceability support

## Data Retention

MVP should define retention hooks for:

- Uploaded source documents
- Extracted text and tables
- Generated quote drafts
- Estimator edit history
- Audit logs
- Exported packages

Exact retention policies can be configured per customer later.

## High-Risk Data Handling

Asbestos surveys and hazardous material reports may contain private site, client, and commercial pricing information. The system should assume documents are confidential by default.

