import { redirect } from "next/navigation";

export default async function ApprovalAliasPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  redirect(`/workups/${id}/export`);
}

