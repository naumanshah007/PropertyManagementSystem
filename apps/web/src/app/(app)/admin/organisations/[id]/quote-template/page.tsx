import { PageHeader } from "@/components/page-header";
import { QuoteTemplateManager } from "@/components/quote-template-manager";
import { RiskChip } from "@/components/status-chip";

export default async function QuoteTemplatePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return (
    <div>
      <PageHeader
        eyebrow="Organisation Admin"
        title="Quote template"
        description="Configure how this organisation's client-facing quotes are branded and laid out. New exports use the active template."
        actions={<RiskChip label="Branded export" />}
      />
      <QuoteTemplateManager orgId={id} />
    </div>
  );
}
