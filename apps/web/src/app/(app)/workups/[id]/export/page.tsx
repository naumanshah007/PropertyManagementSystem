import { redirect } from "next/navigation";

// Review & export is now the "Approve" + "Export" steps inside the job workspace.
export default function ExportRedirect() {
  redirect("/jobs");
}
