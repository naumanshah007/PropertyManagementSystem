import { redirect } from "next/navigation";

export default function NewWorkupRedirect() {
  redirect("/jobs/new");
}
