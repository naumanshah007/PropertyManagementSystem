# Phase 10 Editable Pricebook UI Report

## Scope

Phase 10 gives organisation admins a demo-ready way to manage company-owned pricebook rules and quoting controls.

This phase does not add ML, LLM quote writing, billing, Fergus integration, or production authentication.

## Implemented Backend

Added organisation-scoped pricebook endpoints:

- `GET /organisations/{org_id}/pricebooks/{pricebook_id}`
- `POST /organisations/{org_id}/pricebooks/{pricebook_id}/rules`
- `PATCH /organisations/{org_id}/pricebooks/{pricebook_id}/rules/{rule_id}`
- `DELETE /organisations/{org_id}/pricebooks/{pricebook_id}/rules/{rule_id}`
- `POST /organisations/{org_id}/pricebooks/{pricebook_id}/activate`

`DELETE` is implemented as a safe deactivate operation by setting `active=false` on the rule.

## Rule Fields

Editable rules now support:

- Rule name
- Category/section
- Material match
- Class match: `Class A`, `Class B`, `Unknown`
- Access match: `normal`, `no-access`, `limited-access`, `unknown`
- Pricing method: `fixed`, `per_sqm`, `per_piece`, `per_hour`, `excluded`
- Unit
- Unit rate
- Risk multiplier
- Margin
- GST taxable
- Minimum charge
- Assumptions
- Exclusions
- Review required
- Mandatory
- Active

## Pricing Integration

The pricing engine now checks for an active organisation pricebook for the uploaded document’s organisation.

If an active organisation pricebook exists and has active rules, those rules are used for deterministic pricing. If no organisation pricebook exists, pricing falls back to the Phase 5 seed pricebook.

The pricing result records the pricebook version used.

## Frontend

The organisation admin pricebook route now provides an editable rule manager:

- Pricebook list and active version indicator
- Rule table with mandatory/optional and active/inactive states
- Add rule form
- Edit rule form
- Deactivate rule action
- Activate pricebook action
- Preview calculation for a sample quantity

Route:

- `/admin/organisations/{org_id}/pricebook`

## Tests

Added backend coverage for:

- Creating a pricebook rule
- Editing a rule
- Deactivating a rule
- Activating a pricebook
- Persisting assumptions and exclusions
- Using active organisation-specific pricebook rules in pricing
- Falling back to the seed pricebook when no organisation pricebook is available

## Known Limitations

- Demo auth still provides navigation only and is not a production security boundary.
- Rule matching is deterministic and deliberately simple: category/section, material keyword, class, and access state.
- Rule deletion is soft deactivation to preserve auditability.
- Frontend pricebook editing is suitable for demo/admin workflows, but it does not yet include bulk import/export or version comparison.
- Existing priced quote lines are not automatically repriced when a pricebook rule changes; users rerun pricing for a document.
