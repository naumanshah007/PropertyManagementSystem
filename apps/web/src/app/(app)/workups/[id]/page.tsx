import { redirect } from "next/navigation";

// Superseded by the job workspace. Old links fall back to the jobs list.
export default function WorkupDetailRedirect() {
  redirect("/jobs");
}
