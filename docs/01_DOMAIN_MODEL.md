# Domain Model

## Core Entities

### Quote Workup

A quote workup is the main project record.

Fields:

- `id`
- `client_name`
- `site_address`
- `job_type`
- `survey_type`
- `status`
- `assigned_estimator_id`
- `due_date`
- `created_at`
- `updated_at`

Statuses:

- `intake`
- `extracting`
- `needs_review`
- `pricing_draft`
- `approval_required`
- `approved`
- `exported`
- `blocked`

### Source Document

A PDF, quote, image, or supporting file uploaded to a workup.

Fields:

- `id`
- `workup_id`
- `file_name`
- `file_type`
- `storage_uri`
- `page_count`
- `parser_version`
- `ocr_status`
- `created_at`

### Source Evidence

Traceable evidence captured from a document.

Fields:

- `id`
- `document_id`
- `page_number`
- `bounding_box`
- `raw_text`
- `normalized_text`
- `evidence_type`
- `confidence`

Evidence types:

- `survey_type`
- `register_item`
- `no_access`
- `limited_access`
- `recommendation`
- `quantity`
- `material`
- `classification`
- `assumption`
- `exclusion`

### Asbestos Register Item

Structured extraction from an asbestos survey/register.

Fields:

- `id`
- `workup_id`
- `location`
- `area`
- `material`
- `product_type`
- `extent_quantity`
- `extent_unit`
- `asbestos_result`
- `fibre_type`
- `friability_class`
- `condition`
- `recommendation`
- `access_status`
- `source_evidence_ids`
- `confidence`
- `review_status`

Important statuses:

- `positive`
- `presumed`
- `nad`
- `no_access`
- `limited_access`
- `unknown`

### Quote Line

Commercial line generated from register items, pricebook rules, and estimator edits.

Fields:

- `id`
- `workup_id`
- `section`
- `description`
- `quantity`
- `unit`
- `unit_rate`
- `base_cost`
- `risk_multiplier`
- `margin`
- `tax_code`
- `subtotal`
- `gst`
- `total`
- `source_evidence_ids`
- `pricing_rule_ids`
- `similar_quote_ids`
- `assumptions`
- `exclusions`
- `review_status`
- `approval_status`

Review statuses:

- `ai_draft`
- `review_required`
- `edited`
- `accepted`
- `rejected`

Approval statuses:

- `not_ready`
- `ready_for_approval`
- `approved`

### Pricing Rule

Deterministic pricing logic.

Fields:

- `id`
- `name`
- `job_type`
- `match_conditions`
- `formula`
- `risk_factors`
- `default_assumptions`
- `default_exclusions`
- `requires_review_when`
- `version`

### Estimator Edit

Append-only record of human changes.

Fields:

- `id`
- `workup_id`
- `entity_type`
- `entity_id`
- `field_name`
- `previous_value`
- `new_value`
- `reason`
- `user_id`
- `created_at`

### Audit Event

Append-only system and user event.

Fields:

- `id`
- `workup_id`
- `actor_type`
- `actor_id`
- `event_type`
- `payload`
- `created_at`

## Required Invariants

- A quote line cannot be approved without at least one source evidence link or an explicit estimator-created reason.
- A final export cannot be generated until all review-required flags are resolved or explicitly accepted by the estimator.
- No-access and presumed asbestos items must default to `review_required`.
- Class A items must be visibly flagged in the review and quote builder screens.
- Every estimator edit must create an `EstimatorEdit` record and an `AuditEvent`.
- The system must distinguish draft AI output from approved human output.

