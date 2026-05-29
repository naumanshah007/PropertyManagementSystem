from __future__ import annotations

from .schemas import SeedPricebookRule


PRICEBOOK_VERSION = "revolve-ras-1285-seed-v1"
GST_RATE = 0.15


SEED_PRICEBOOK: list[SeedPricebookRule] = [
    SeedPricebookRule(
        id="pb-site-establishment",
        name="Site Establishment",
        section="Site Establishment",
        pricing_method="fixed",
        unit="item",
        unit_rate=698.00,
        risk_multiplier=1.0,
        margin=0.0,
        material_keywords=[],
        default_quantity=1,
        default_assumptions=[
            "Installation of equipment: signage, barricades, decontamination unit, and site-specific documentation.",
            "Includes WorkSafe NZ notification, morning toolbox meetings, and neighbour notification letters.",
            "Includes hazard signage board and asbestos cordon tape per site.",
        ],
        default_exclusions=[
            "Scaffolding, power isolation, and third-party independent assessor fees unless separately included.",
        ],
        explanation_template="Standard Revolve site establishment line item (RAS-1285 pattern).",
    ),
    SeedPricebookRule(
        id="pb-class-b-bitumen-sqm",
        name="Class B Bitumen Adhesive Removal",
        section="Class B Removal",
        pricing_method="per_unit",
        unit="sqm",
        unit_rate=195.00,
        risk_multiplier=1.0,
        margin=0.0,
        material_keywords=["bitumen", "adhesive"],
        class_match="Class B",
        minimum_charge=2500.00,
        default_quantity=None,
        default_assumptions=[
            "Per-sqm rate applies to bitumen / adhesive removal from floor or substrate.",
            "Minimum charge of $2,500 enforced for small rooms (under 10 sqm) per Revolve pricing pattern.",
        ],
        default_exclusions=[
            "Reinstatement and finishing work.",
            "Specialty glue removal product (priced as separate provisional line if required).",
        ],
        explanation_template="Per-sqm Class B bitumen adhesive removal (RAS-1285 pattern $195/sqm).",
    ),
    SeedPricebookRule(
        id="pb-class-b-fibre-cement-sqm",
        name="Class B Fibre Cement Sheet Removal",
        section="Class B Removal",
        pricing_method="per_unit",
        unit="sqm",
        unit_rate=80.00,
        risk_multiplier=1.0,
        margin=0.0,
        material_keywords=["fibre cement"],
        class_match="Class B",
        minimum_charge=2500.00,
        default_quantity=None,
        default_assumptions=[
            "Per-sqm rate for fibre cement sheet removal (flat sheet or corrugated).",
            "Minimum charge of $2,500 enforced for small rooms (under 10 sqm).",
        ],
        default_exclusions=[
            "Replacement cladding and reinstatement unless separately included.",
        ],
        explanation_template="Per-sqm Class B fibre cement removal (estimator-reviewable seed rate).",
    ),
    SeedPricebookRule(
        id="pb-class-b-vinyl-sqm",
        name="Class B Vinyl / Floor Tile Removal",
        section="Class B Removal",
        pricing_method="per_unit",
        unit="sqm",
        unit_rate=100.00,
        risk_multiplier=1.0,
        margin=0.0,
        material_keywords=["vinyl", "floor tile", "paper backed"],
        class_match="Class B",
        minimum_charge=2500.00,
        default_quantity=None,
        default_assumptions=[
            "Per-sqm rate for vinyl flooring or floor tile removal.",
            "Minimum charge of $2,500 enforced for small rooms.",
            "Porous timber subfloors may require encapsulation — priced separately.",
        ],
        default_exclusions=[
            "Floor polishing or refinishing.",
        ],
        explanation_template="Per-sqm Class B vinyl / floor tile removal (estimator-reviewable seed rate).",
    ),
    SeedPricebookRule(
        id="pb-class-a-insulating-board-provisional",
        name="Class A / Friable Insulating Board Provisional",
        section="Class A / Friable Removal",
        pricing_method="per_unit",
        unit="piece",
        unit_rate=650.00,
        risk_multiplier=1.0,
        margin=0.0,
        material_keywords=["insulating board", "aib", "friable", "chimney"],
        class_match="Class A",
        minimum_charge=2500.00,
        default_quantity=None,
        default_assumptions=[
            "Class A / friable work requires Class A licensed contractor and enhanced controls.",
            "Provisional pending site visit confirmation of access and scope.",
            "Minimum charge of $2,500 enforced.",
        ],
        default_exclusions=[
            "Expanded containment, enclosure, or assessor scope beyond confirmed register evidence.",
        ],
        explanation_template="Provisional Class A / friable allowance per piece pending site visit.",
    ),
    SeedPricebookRule(
        id="pb-no-access-power-investigation",
        name="No Access — POA (Price on Application)",
        section="Provisional / No Access",
        pricing_method="excluded",
        unit="poa",
        unit_rate=None,
        risk_multiplier=1.0,
        margin=0.0,
        material_keywords=[],
        access_status_match="no_access",
        default_quantity=None,
        default_assumptions=[
            "No allowance has been included for this area.",
            "Full scope to be provided after site visit and assessor confirmation.",
        ],
        default_exclusions=[
            "All work in this no-access area is excluded from current pricing.",
        ],
        explanation_template="No-access area marked POA — to be priced after site visit.",
    ),
    SeedPricebookRule(
        id="pb-waste-disposal-placeholder",
        name="Asbestos Waste Disposal",
        section="Waste / Disposal Placeholder",
        pricing_method="per_unit",
        unit="kg",
        unit_rate=0.92,
        risk_multiplier=1.0,
        margin=0.0,
        material_keywords=[],
        default_quantity=3500,
        default_assumptions=[
            "Certified disposal of asbestos material and contaminated waste at an approved disposal site.",
            "Default quantity is an estimate from total removal area; estimator should refine based on actual waste tonnage.",
        ],
        default_exclusions=[
            "Unexpected mixed demolition waste, contaminated soil, off-register materials.",
        ],
        explanation_template="Per-kg asbestos waste disposal rate (RAS-1285 pattern $0.92/kg).",
    ),
    SeedPricebookRule(
        id="pb-encapsulation-provisional",
        name="ABC Fibre Lock Encapsulant",
        section="Encapsulation / Provisional Allowance",
        pricing_method="per_unit",
        unit="sqm",
        unit_rate=34.00,
        risk_multiplier=1.0,
        margin=0.0,
        material_keywords=["encapsul", "seal", "fibre lock"],
        default_quantity=None,
        default_assumptions=[
            "ABC Fibre Lock encapsulant applied per sqm.",
            "Used where residual fibres on porous surfaces (concrete, rough timber) require sealing.",
        ],
        default_exclusions=[
            "Substrate repairs and decorative reinstatement unless separately included.",
        ],
        explanation_template="Per-sqm encapsulant rate (RAS-1285 pattern $34/sqm).",
    ),
    SeedPricebookRule(
        id="pb-glue-remover-provisional",
        name="Bitumen Glue Remover (Provisional)",
        section="Encapsulation / Provisional Allowance",
        pricing_method="fixed",
        unit="allowance",
        unit_rate=4152.00,
        risk_multiplier=1.0,
        margin=0.0,
        material_keywords=["glue", "adhesive remover", "bitumen remover"],
        default_quantity=1,
        default_assumptions=[
            "Provisional sum subject to products chosen.",
            "Applied when bitumen adhesive removal requires a specialty chemical product.",
        ],
        default_exclusions=[
            "Disposal costs of the chemical product itself — covered under waste disposal line.",
        ],
        explanation_template="Provisional sum for bitumen glue remover product (RAS-1285 pattern).",
    ),
    SeedPricebookRule(
        id="pb-excluded-nad",
        name="Excluded / NAD finding",
        section="Excluded / NAD Findings",
        pricing_method="excluded",
        unit="excluded",
        unit_rate=None,
        risk_multiplier=1.0,
        margin=0.0,
        material_keywords=[],
        default_quantity=None,
        default_assumptions=[
            "NAD / non-asbestos item remains excluded unless estimator overrides.",
        ],
        default_exclusions=[
            "No asbestos removal pricing applied to this finding.",
        ],
        explanation_template="NAD / non-asbestos finding is excluded from pricing by default.",
    ),
]


def get_seed_pricebook() -> list[SeedPricebookRule]:
    return SEED_PRICEBOOK
