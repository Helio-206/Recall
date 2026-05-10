import type { Metadata } from "next";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";

export const metadata: Metadata = {
  title: "Recall",
  description: "Developer-first learning workspace.",
};

export default async function HomePage() {
  const cookieStore = await cookies();
  const hasToken = cookieStore.get("recall_token")?.value;
  redirect(hasToken ? "/dashboard" : "/login");
}
