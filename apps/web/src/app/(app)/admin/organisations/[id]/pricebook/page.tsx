import { PageHeader } from "@/components/page-header";
import { PricebookManager } from "@/components/pricebook-manager";
import { RiskChip } from "@/components/status-chip";

export default async function OrganisationPricebookPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return (
    <div>
      <PageHeader
        eyebrow="Organisation Admin"
        title="Company pricebook"
        description={`Manage active pricing rules for ${id}. These rules drive deterministic quote pricing before estimator review.`}
        actions={<RiskChip label="Editable rules" />}
      />
      <PricebookManager orgId={id} />
    </div>
  );
}
