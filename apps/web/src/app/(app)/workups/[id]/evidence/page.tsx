import { redirect } from "next/navigation";

// Evidence review is now the "Survey review" step inside the job workspace.
export default function EvidenceRedirect() {
  redirect("/jobs");
}
