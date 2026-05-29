import { LLMSettingsManager } from "@/components/llm-settings-manager";
import { PageHeader } from "@/components/page-header";
import { RiskChip } from "@/components/status-chip";

export default async function OrganisationLLMSettingsPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return (
    <div>
      <PageHeader
        eyebrow="Organisation Admin"
        title="LLM register extraction"
        description={`Choose the AI provider used to extract asbestos register items from surveys uploaded by ${id}.`}
        actions={<RiskChip label="Org scoped" />}
      />
      <LLMSettingsManager orgId={id} />
    </div>
  );
}
