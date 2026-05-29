import { redirect } from "next/navigation";

// Quote building is now the "Pricing" step inside the job workspace.
export default function QuoteRedirect() {
  redirect("/jobs");
}
