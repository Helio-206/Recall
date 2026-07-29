import type { Metadata } from "next";
import { cookies } from "next/headers";

import { LandingPage } from "@/components/marketing/landing-page";

export const metadata: Metadata = {
  title: "Recall - Your learning OS for video",
  description:
    "Turn internet videos into structured learning paths, readable transcripts, and progress you can resume.",
};

export default async function HomePage() {
  const cookieStore = await cookies();
  const isAuthenticated = Boolean(cookieStore.get("recall_token")?.value);

  return <LandingPage isAuthenticated={isAuthenticated} />;
}
