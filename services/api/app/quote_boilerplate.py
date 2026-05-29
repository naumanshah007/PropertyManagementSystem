"""RAS-1285-style boilerplate text used when generating Revolve-format client quotes.

These constants are the default values for organisation_settings fields. Each org
can override them via OrganisationSettings — these are just the demo seed text
that matches Revolve Asbestos Solutions' Fergus output pattern.
"""

from __future__ import annotations


DEFAULT_QUOTE_INCLUSIONS: list[str] = [
    "Issuing the WorkSafe notification for the quoted asbestos removal.",
    "Morning toolbox meetings to review on site hazards and work to be completed that day.",
    "Notifying neighbours by delivering letters into their letterboxes.",
    "Erecting a Hazard signage board outlining the hazards on site with the Supervisor's contact number.",
    "Cordon the area with asbestos signage tape and signage that clearly reads, “Asbestos Removal in Progress – Keep Out”.",
    "Within and around the removal areas, using 200 micron non-recycled polythene and tape for ground sheets and enclosures.",
    "Set up the decontamination chamber.",
    "Provide all PPE and RPE safety equipment for the correct removal of asbestos.",
    "Removal of the asbestos using the correct tools and equipment.",
    "Enclose the asbestos waste using the correct methods of double wrapping or double bagging and then goose necking the tops with tape.",
    "Clean up, ensuring that there are no loose or visible debris on the polythene surface.",
    "Dispose of the asbestos material and contaminated waste at a certified landfill.",
    "Contact your independent Assessor for the Certified Clearance.",
]


DEFAULT_QUOTE_IMPORTANT_NOTES: list[str] = [
    "No one is allowed on site during the removal.",
    "To confirm this pricing a site visit is required.",
    "Unless otherwise specified the above pricing does not include any reinstatement or finishing work.",
    "You are required by law to have an Assessor check the work and ensure that a Clearance Certificate can be issued. This Assessor is independent from the removal work and should be appointed by yourself. We can assist in this if needed.",
    "For the duration of the work, vehicle and truck access and parking on site must be provided.",
    "If having significant works done, we recommend you inform your insurance company.",
    "So as not to delay completion times we recommend that scaffolding be installed prior to the asbestos removal work commencing. NOTE: Unless itemised separately, scaffolding costs are not included in our pricing.",
    "Due to the unpredictability of New Zealand weather, we recommend that prior to any significant exterior works being undertaken you have the structure wrapped. This adds an additional layer of protection and enables a continuance of the project that would not be possible with the site being exposed to the conditions.",
    "For asbestos removals such as roofing, soffits, cladding, baseboards and fencing these areas need to have clear access with all trees and vegetation removed. No allowances have been made for the base of the material being embedded into the ground, concrete or between footings.",
    "Removal areas need to have clear and easy access with all furniture and general items cleared prior to commencement.",
    "The above pricing is based upon the ceiling cavity having solid state insulation, such as Pink Batts and being in reasonable condition. Where loose fill insulation is present or there is excess dirt and/or dust an additional charge will be invoiced.",
    "Where enclosures are built, adhesive tape and staples will need to be used. A certain amount of damage to wall surfaces and associated areas will occur — this is part of the removal process and the client agrees to indemnify the contractor against all actions, claims, losses, and expenses in respect of loss or damage arising from the services provided.",
    "Prior to asbestos ceilings being removed, the power supply to light fittings, fans, alarm systems etc. must be isolated by a qualified electrician. Unless otherwise requested in writing, fittings in the removal areas will be disposed of as contaminated waste.",
    "If asbestos-coated surfaces such as ceilings are to be scraped and encapsulated rather than removed, the surface will often need a multi-layered skim coat prior to painting.",
    "Due to their nature, porous surfaces such as concrete and rough sawn timber cannot always be 100% fibre free; these will need to be encapsulated with an asbestos bonding compound. Areas that have been encapsulated as part of the Clearance should not be breached through cutting, drilling, sanding, or water blasting.",
    "Where paper-backed vinyl flooring and mastic glues are being removed from floor surfaces such as tongue and groove, it is not always possible to remove all fibres from between the timber joints; the floor surface will need to be sealed with a specialised bonding compound.",
    "Unless demolition work is approved by the client in writing, where asbestos material goes behind or beneath areas such as cupboards, toilets and/or exterior decking, the removal will stop at the juncture.",
]


DEFAULT_QUOTE_REQUIRED_SERVICES: list[str] = [
    "Power to run our equipment.",
    "Running water to minimise dust and clean equipment.",
    "Toilets for staff.",
    "An independent Assessor.",
]


DEFAULT_QUOTE_INTRO_TEXT: str = (
    "Thank you for the opportunity to price the work on your property. "
    "Our mission is to make every customer a repeat customer. Customer service is everything "
    "to us and we have the systems in place so that we deliver on our promises."
)


DEFAULT_QUOTE_DISCLAIMER_TEXT: str = (
    "The pricing is based on the information supplied. Any increases or decreases in square metres, "
    "additional works for access and/or removal will be charged and affect your final cost."
)


DEFAULT_QUOTE_ACCEPTANCE_TEXT: str = (
    "Whether via Fergus, email or signing our Cost Agreement, by accepting our Quote you accept all "
    "Terms of Trade."
)


DEFAULT_QUOTE_VARIATION_TEXT: str = (
    "Where equipment and facilities such as generators and toilets are not supplied then the additional "
    "costs will be charged as a Variation to the price and will need to be paid prior to the removal commencing."
)


DEFAULT_QUOTE_CLOSING_TEXT: str = (
    "If you have any questions or would like to discuss the project further, feel free to contact me directly."
)
