import { CreateOrganisationForm } from "@/components/create-organisation-form";
import { PageHeader } from "@/components/page-header";

export default function NewOrganisationPage() {
  return (
    <div className="space-y-5">
      <PageHeader
        eyebrow="Platform Admin"
        title="Create organisation"
        description="Each new customer organisation is created with branding defaults plus an editable RAS-1285 starter pricebook."
      />
      <CreateOrganisationForm />
    </div>
  );
}
